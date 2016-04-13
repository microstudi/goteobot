#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Goteo Bot to send Telegram messages using The Goteo API
# LICENSE GPLv3.

"""
This Bot gives you information about projects and other Goteo stuff by using its
api: https://api.goteo.org/

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
...TODO...
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram.ext import Updater
from telegram import ParseMode
import logging
import requests
from time import strftime, localtime
from email.utils import parsedate_to_datetime
from datetime import datetime
import config

# Enable logging
logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

logger = logging.getLogger(__name__)
job_queue = None


def get_project(project):
    r = requests.get(config.API_URL + '/projects/' + project, auth=(config.API_USER, config.API_KEY))
    if r.status_code == 200:
        project = r.json()
        return project
    return None

def get_last_invest(project):
    payload = {
        'limit' : 1,
        'from_date': strftime('%Y-%m-%d', localtime())
    }
    if project is not '*':
        payload['project'] = project,

    r = requests.get(config.API_URL + '/invests', params=payload, auth=(config.API_USER, config.API_KEY))
    if r.status_code == 200:
        invests = r.json()
        if 'items' in invests and invests['items']:
            return invests['items'][0]
    return None


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    bot.sendMessage(update.message.chat_id, text='Hi! Use /subscribe <project-id> to '
                                                 'receive updates on every contribution')

def subscribe(bot, update, args):
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the project to follow
        project_id = args[0]
        project = None
        t = "Subscribed for updates in %s" % project_id
        if project_id == '*':
            t = "Subscribed to all projects!"
        else:
            project = get_project(project_id)
            if project is None:
                bot.sendMessage(chat_id, text='Sorry, project not found!')
                raise ValueError;

        def updates(bot):
            """ Inner function to send the updates message """
            m = "Yeah! A new contribution of"
            invest = None
            prj = None
            invest = get_last_invest(project_id)
            date = parsedate_to_datetime(invest['date-updated'])
            if date < datetime.now():
                logger.info("SKIPPED INVEST [%s] UPDATED [%s]" % (invest['id'], invest['date-updated']))
                return

            logger.info("INVEST [%s] OF [%i %s] UPDATED [%s] FOR PROJECT [%s]" % (invest['id'],
                                                                                  invest['amount'],
                                                                                  invest['currency'],
                                                                                  invest['date-updated'],
                                                                                  invest['project']))

            m += " **%i %s**" % (invest['amount'], invest['currency'])
            if invest['project']:
                if project_id == invest['project']:
                    prj = project.copy()
                else:
                    prj = get_project(invest['project'])
                m += " for [%s](%s)" % (prj['name'], prj['project-url'])
            else:
                m += " to the virtual wallet"

            bot.sendMessage(chat_id, text=m, parse_mode=ParseMode.MARKDOWN)

        # Add job to queue
        job_queue.put(updates, config.POLL_FREQUENCY)
        bot.sendMessage(chat_id, text=t)

    except IndexError:
        bot.sendMessage(chat_id, text='Usage: /subscribe <project>')
    except ValueError:
        bot.sendMessage(chat_id, text='Usage: /subscribe <project>')


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    global job_queue


    updater = Updater(config.BOT_TOKEN)
    job_queue = updater.job_queue

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.addTelegramCommandHandler("start", start)
    dp.addTelegramCommandHandler("help", start)
    dp.addTelegramCommandHandler("subscribe", subscribe)

    # log all errors
    dp.addErrorHandler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()

