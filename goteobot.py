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
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta
import config

# Enable logging
logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        # level=logging.INFO)
        level=logging.INFO)

logger = logging.getLogger(__name__)
job_queue = None
last_id = {}
last_date = datetime.now() - timedelta(days=1)

def get_project(project):
    r = requests.get(config.API_URL + '/projects/' + project, auth=(config.API_USER, config.API_KEY))
    logger.info("REQUEST %s %s" % (config.API_URL + '/projects/' + project, r))
    if r.status_code == 200:
        project = r.json()
        return project
    return None

def get_invests(project_id):
    payload = {
        'limit' : 5,
        'from_date': last_date.strftime('%Y-%m-%d')
    }
    if project_id is not '*':
        payload['project'] = project_id,
    r = requests.get(config.API_URL + '/invests/', params=payload, auth=(config.API_USER, config.API_KEY))
    logger.info("REQUEST %s %s PARAMS %s" % (config.API_URL + '/invests/', r, payload))
    if r.status_code == 200:
        invests = r.json()
        # print(invests)
        if 'items' in invests and invests['items']:
            return list(reversed(invests['items']))
    return None

def msg_yell(amount=0):
    if amount > 100:
        return "Yabadabadu!"
    if amount >= 100:
        return "Amazing!"
    if amount >= 50:
        return "Great!"
    if amount >= 20:
        return "Good!"
    if amount >= 10:
        return "Cool!"
    if amount >= 5:
        return "Not bad!"
    return 'Ahem, that could be better...'

def msg_invest(invest):
    m = "*%s*" % msg_yell(invest['amount'])
    m += " A new *%i %s* contribution" % (invest['amount'], invest['currency'])
    if invest['region']:
        m+= " from _%s_" % invest['region']

    if invest['project']:
        prj = get_project(invest['project'])
        if prj:
            m += " to [%s](%s)" % (prj['name'], prj['project-url'])
        else:
            m += " to *unknown project*"
    else:
        m += " to the *virtual wallet*"
    return m

def filter_new_invests(invests):
    global last_date

    ret = []
    for i in invests:

        logger.info("INVEST %s of %i %s" % (i['id'], i['amount'], i['currency']))

        # print('lASTID', last_id)

        if i['project'] not in last_id:
            last_id[i['project']] = 0
        if i['id'] > last_id[i['project']]:
            ret.append(i)
            logger.info("ADDING INVEST %s" % i['id'])
            last_id[i['project']] = i['id']
            last_date = parsedate_to_datetime(i['date-invested'])

    # print('LAST_ID', last_id, 'INVESTS', ret)

    return ret

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
        if project_id != '*':
            project = get_project(project_id)
            if project is None:
                bot.sendMessage(chat_id, text='Sorry, project not found!')
                raise ValueError;

        logger.info("NEW SUBSCRIPTION FOR [%s]" % project_id)
        # print(update.message)

        def updates(bot):
            """ Inner function to send the updates message """

            invests = get_invests(project_id)
            if not invests:
                logger.info("NO INVESTS FOUND FOR [%s]" % project_id)
                return

            invests = filter_new_invests(invests)
            logger.info("TOTAL INVEST FOUND: %i" % len(invests))

            for invest in invests:
                logger.info("INVEST [%s] OF [%i %s] UPDATED [%s] FOR PROJECT [%s]" % (invest['id'],
                                                                                      invest['amount'],
                                                                                      invest['currency'],
                                                                                      invest['date-invested'],
                                                                                      invest['project']))
                bot.sendMessage(chat_id,
                                text=msg_invest(invest),
                                parse_mode=ParseMode.MARKDOWN)


        # Add job to queue
        job_queue.put(updates, config.POLL_FREQUENCY)

        t = "Subscribed to all projects!"
        if project:
            t = "Subscribed for project %s" % project['name']

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

