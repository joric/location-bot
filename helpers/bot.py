import logging

import os
os.environ["PYTHON_TELEGRAM_BOT_NO_EXTENSIONS"] = "1"

import telegram
from telegram.ext import Dispatcher, MessageHandler, CommandHandler, Filters

import urllib3
import json

logger = logging.getLogger(__name__)

def help(update, context):
    """Send a message when the command /start is issued."""
    update.effective_message.reply_text("""Hi! I search location.
Example: "40.714627 -74.002863" or "new york".
"""
    )

http = urllib3.PoolManager(headers={'User-Agent': 'LocationBot/1.0'})

import re

def parse_coords(q):
    def dms(d, m=0, s=0, sign=1):
        return sign * (float(d) + float(m)/60 + float(s)/3600)

    def fmt(x):
        s = f"{x:.6f}".rstrip('0').rstrip('.')
        return s if s else '0'

    q = q.strip().upper()

    if '°' in q:
        coords = re.findall(r'(\d+(?:\.\d+)?)\s*°\s*(\d*(?:\.\d+)?)?\s*\'?\s*(\d*(?:\.\d+)?)?\s*"?\s*([NSEW])?', q)

        if len(coords) >= 2:
            d1, m1, s1, a1 = coords[0]
            d2, m2, s2, a2 = coords[1]

            lat = dms(d1, m1 or 0, s1 or 0, -1 if a1 == 'S' else 1)
            lon = dms(d2, m2 or 0, s2 or 0, -1 if a2 == 'W' else 1)

            return float(fmt(lat)), float(fmt(lon))

        return None

    m = re.fullmatch(r'\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*', q)
    if m:
        return float(fmt(float(m.group(1)))), float(fmt(float(m.group(2))))

    return None

def getDisplayNameFromOSM(lat, lng):
    r = http.request('GET', 'https://nominatim.openstreetmap.org/reverse', fields={"lat":lat, "lon":lng, "format":"json"}, timeout=10)
    data = json.loads(r.data.decode('utf-8'))
    if 'display_name' in data:
        return data['name'], data['display_name']

def getLocationFromOSM(q):
    r = http.request('GET', 'https://nominatim.openstreetmap.org/search', fields={"q":q, "format":"json", "limit": 1}, timeout=10)
    data = json.loads(r.data.decode('utf-8'))
    if data:
        return [data[0]['name'], data[0]['display_name'], *map(float, [data[0]['lat'], data[0]['lon']])]

def reply(update, context, q):
    if not q:
        help(update, context)
    else:
        coords = parse_coords(q)

        if coords:
            lat, lng = coords
            name, display_name = getDisplayNameFromOSM(lat, lng) or ['Unknown','Unknown Location']
            update.effective_message.reply_venue(latitude=lat or 0.00001, longitude=lng or 0.00001, title=f'{lat}, {lng}', address=display_name)
            return

        res = getLocationFromOSM(q)
        if res:
            name, display_name, lat, lng = res
            update.effective_message.reply_venue(latitude=lat, longitude=lng, title=f'{lat}, {lng}', address=display_name)
        else:
            update.effective_message.reply_text(f'"{q}" not found.')

def echo(update, context):
    reply(update, context, update.effective_message.text)

def get_dispatcher(bot):
    """Create and return dispatcher instances"""
    dispatcher = Dispatcher(bot, None, workers=0)

    dispatcher.add_handler(CommandHandler("start", help))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(MessageHandler((Filters.text | Filters.update) & ~Filters.command, echo))
    return dispatcher
