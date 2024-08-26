import logging

import telegram, os
from telegram.ext import Dispatcher, MessageHandler, CommandHandler, Filters

from uuid import uuid4

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

def getLocationFromOSM(q):
    r = http.request('GET', 'https://nominatim.openstreetmap.org/search', fields={"q":q, "format":"json", "limit": 1})
    text = r.data.decode('utf-8')
    data = json.loads(text)
    if data:
        return [data[0]['display_name'], *map(float, [data[0]['lat'], data[0]['lon']])]
    return None

def echo(update, context):
    update.effective_message.reply_text(update.effective_message.text)

def location(update, context):
    try:
        latitude = float(context.args[0].rstrip(','))
        longitude = float(context.args[1])
        update.effective_message.reply_location(latitude=latitude, longitude=longitude)
    except (IndexError, ValueError) as e:
        try:
            q = ' '.join(context.args)
            res = getLocationFromOSM(q)
            if res:
                display_name, latitude, longitude = res
                update.effective_message.reply_text(display_name)
                update.effective_message.reply_location(latitude=latitude, longitude=longitude)
            else:
                update.effective_message.reply_text(f'Location "{q}" not found.')
        except (IndexError, ValueError) as e:
            # logger.error(f"Error processing location command: {e} - {context.args}")
            update.effective_message.reply_text('Usage: /location <latitude> <longitude>')

def get_dispatcher(bot):
    """Create and return dispatcher instances"""
    dispatcher = Dispatcher(bot, None, workers=0)

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("location", location))
    dispatcher.add_handler(MessageHandler((Filters.text | Filters.update) & ~Filters.command, echo))
    return dispatcher
