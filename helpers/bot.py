import logging

import telegram, os
from telegram.ext import Dispatcher, MessageHandler, CommandHandler, Filters

import urllib3
import json

logger = logging.getLogger(__name__)

def start(update, context):
    """Send a message when the command /start is issued."""
    update.effective_message.reply_text("""Hi! I send location.
Example:
/location 40.714627 -74.002863
"""
    )

http = urllib3.PoolManager()

def getDisplayNameFromOSM(lat, lng):
    r = http.request('GET', 'https://nominatim.openstreetmap.org/reverse', fields={"lat":lat, "lon":lng, "format":"json"})
    data = json.loads(r.data.decode('utf-8'))
    if 'name' in data and 'display_name' in data:
        return data['name'], data['display_name']

def getLocationFromOSM(q):
    r = http.request('GET', 'https://nominatim.openstreetmap.org/search', fields={"q":q, "format":"json", "limit": 1})
    data = json.loads(r.data.decode('utf-8'))
    if data:
        return [data[0]['name'], data[0]['display_name'], *map(float, [data[0]['lat'], data[0]['lon']])]

def reply(update, context, q):
    if not q:
        update.effective_message.reply_text('Usage: /location <latitude> <longitude>')
    else:
        try:
            lat, lng = map(float,q.replace(',',' ').split())
            name, display_name = getDisplayNameFromOSM(lat, lng) or ['Unknown','Unknown Location']
            # Either venue or latitude, longitude, address and title must be passed as arguments
            update.effective_message.reply_venue(latitude=lat or 0.00001, longitude=lng or 0.00001, title=f'{lat}, {lng}', address=display_name)
        except Exception as e:
            # logger.error(f"Error processing location command: {e} - {context.args}")
            res = getLocationFromOSM(q)
            if res:
                name, display_name, lat, lng = res
                update.effective_message.reply_venue(latitude=lat, longitude=lng, title=f'{lat}, {lng}', address=display_name)
            else:
                update.effective_message.reply_text(f'"{q}" not found.')

def echo(update, context):
    reply(update, context, update.effective_message.text)

def search(update, context):
    reply(update, context, ' '.join(context.args))

def location(update, context):
    reply(update, context, ' '.join(context.args))

def get_dispatcher(bot):
    """Create and return dispatcher instances"""
    dispatcher = Dispatcher(bot, None, workers=0)

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", start))
    dispatcher.add_handler(CommandHandler("location", location))
    dispatcher.add_handler(CommandHandler("search", search))
    dispatcher.add_handler(MessageHandler((Filters.text | Filters.update) & ~Filters.command, echo))
    return dispatcher
