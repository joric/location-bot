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
    def dms_to_deg(d, m=0, s=0, sign=1):
        return sign * (float(d) + float(m)/60 + float(s)/3600)
    q = q.replace(',', ' ').upper()
    pattern = r'(\d+(?:\.\d+)?)\D+(\d*(?:\.\d+)?)?\D*(\d*(?:\.\d+)?)?\D*([NS])?.*?(\d+(?:\.\d+)?)\D+(\d*(?:\.\d+)?)?\D*(\d*(?:\.\d+)?)?\D*([EW])?'
    m = re.search(pattern, q)
    if m:
        d1,m1,s1,ns,d2,m2,s2,ew = m.groups()
        lat = dms_to_deg(d1, m1 or 0, s1 or 0, -1 if ns=='S' else 1)
        lng = dms_to_deg(d2, m2 or 0, s2 or 0, -1 if ew=='W' else 1)
        return lat, lng
    parts = [x for x in q.split() if re.match(r'^-?\d+(\.\d+)?$', x)]
    if len(parts) == 2:
        return float(parts[0]), float(parts[1])

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
