import logging

import telegram, os
from telegram.ext import Dispatcher, MessageHandler, CommandHandler, Filters

from uuid import uuid4

def start(update, context):
    """Send a message when the command /start is issued."""
    update.effective_message.reply_text("""Hi! I send location.
Example:
/location 40.714627 -74.002863
"""
    )

def echo(update, context):
    update.effective_message.reply_text(update.effective_message.text)

def location(update, context):
    try:
        latitude = float(context.args[0])
        longitude = float(context.args[1])
        update.effective_message.reply_location(latitude=latitude, longitude=longitude)
    except (IndexError, ValueError):
        update.effective_message.reply_text('Usage: /location <latitude> <longitude>')

def get_dispatcher(bot):
    """Create and return dispatcher instances"""
    dispatcher = Dispatcher(bot, None, workers=0)

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("location", location))
    dispatcher.add_handler(MessageHandler((Filters.text | Filters.update) & ~Filters.command, echo))
    return dispatcher
