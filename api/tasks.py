from __future__ import absolute_import

import os
import time
import random
from datetime import date
from html.parser import HTMLParser

import telegram
from celery import shared_task
from celery.schedules import crontab
from celery.utils import log
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth.models import User

import feedparser
from telegram import Bot, KeyboardButton, ReplyKeyboardMarkup
from telegram import Update, Message
from telegram.ext import CommandHandler

from api import models

logger = log.get_task_logger(__name__)


@shared_task
def email_managers(template_name, context=None):
    manager_emails = [a[1] for a in getattr(settings, 'MANAGERS', [])]

    for em in manager_emails:
        email_user(em, template_name, context)


@shared_task
def email_user(email, template_name, context=None, attach_filelocation=None):
    """
    Task to send an email template rendered with a context to a specified email address. The subject line is also
    extracted from a text template file alongside the body template. The function also accepts a file that would be
    attached to the email message.
    """
    email_templatepath = 'emails'

    # fetch the subject template and render it with context
    subject_fileprefix = 'subject_'  # the subject filename prefix

    # strip the extension
    template_filename_bare, template_filename_ext = os.path.splitext(template_name)
    # the subject template filename is the subject prefix joined with the body template name
    subject_template_filename = os.path.join(email_templatepath,
                                             '{0}{1}.txt'.format(subject_fileprefix, template_filename_bare))

    body_template_filename = os.path.join(email_templatepath, template_name)

    # render subject template with context
    rendered_subject_template = render_to_string(subject_template_filename, context).replace('\n', ' ')
    # the email template rendered with context, as a string
    rendered_body_template = render_to_string(body_template_filename, context)

    msg = EmailMessage(rendered_subject_template, rendered_body_template, to=[email])
    msg.content_subtype = 'html'  # Main content is now text/html

    if attach_filelocation is not None:
        msg.attach_file(attach_filelocation)

    logger.info("Sending email {0} to {1}".format(rendered_subject_template, email))

    msg.send()


@shared_task
def fetch_rss():
    stop_words = [
        'a', 'the', 'of',
        'off', 'for', '+'
    ]
    class TagStripper(HTMLParser):
        def __init__(self):
            self.reset()
            self.strict = False
            self.convert_charrefs = True
            self.fed = []

        def handle_data(self, d):
            self.fed.append(d)

        def get_data(self):
            return ''.join(self.fed)

    doc = feedparser.parse('https://www.ozbargain.com.au/deals/feed')

    for entry in doc.entries:
        deal_title = entry.title
        deal_link = entry.link

        deal_exists = models.Deal.objects.filter(title=deal_title).exists()

        if not deal_exists:
            deal = models.Deal()
            deal.title = deal_title
            deal.link = deal_link
            deal.raw = entry

            # assign meta fields to deal
            deal.meta = dict()
            # first is summary
            deal.meta['summary'] = entry.summary

            # summary is in html so strip it out
            ts = TagStripper()
            ts.feed(entry.summary)
            deal.meta['summary_sanshtml'] = ts.get_data()

            # combine all this text to look at
            deal_text = '{0} {1}'.format(deal.meta['summary_sanshtml'], deal.title)

            # turn it into a word cloud
            # by first splitting it up and lowering it
            deal_text_parts_list = deal_text.split()
            deal_text_parts_list = list(map(lambda word: word.lower(), deal_text_parts_list))
            word_cloud_list = []

            # then making sure it doesn't contain words in the stop list
            for part in deal_text_parts_list:
                if part not in stop_words and part not in word_cloud_list:
                    word_cloud_list.append(part)
            deal.meta['word_cloud'] = word_cloud_list

            deal.save()

    # check user interests every time we refresh rss
    check_interests()


def command_start(message):
    msg_chat_id = message.chat_id
    from_user = message.from_user
    # use telegram user id to check if profile already exists, if not create new user and profile
    userprofile_exists = models.UserProfile.objects.filter(telegram_user_id=from_user.id).exists()

    if userprofile_exists:
        # previous user
        userprofile = models.UserProfile.objects.get(telegram_user_id=from_user.id)

        # update chat id for ex-user
        userprofile.chat_id = msg_chat_id
        userprofile.save()

        message.reply_text(
            "You're already connected to the Aussie Shopper bot! Try /help if you're not sure what to do next.")
    else:
        # new user, create account
        user = User.objects.create_user('u{0}'.format(from_user.id))

        userprofile = models.UserProfile()
        userprofile.duser = user
        userprofile.telegram_user_id = from_user.id
        userprofile.chat_id = msg_chat_id
        userprofile.save()

        message.reply_text(
            "You are now connected to the Aussie Shopper bot! You will get deals that might interest you when you register your interests. Try /help if you're not sure what to do next.")


def command_unknown(message):
    message_user("I am not sure I understand but I am listening.", message=message, instant=True)


def get_userprofile(user_id: int) -> models.UserProfile:
    try:
        userprofile = models.UserProfile.objects.get(telegram_user_id=user_id)
        return userprofile
    except models.UserProfile.DoesNotExist as dne:
        logger.exception(dne)
    except models.UserProfile.MultipleObjectsReturned as mor:
        logger.exception(mor)

    return None


def failas_notregistered(message: Message):
    message_user("You are not in the system, /start to register yourself.", message=message, instant=True)


def command_latestdeals(message: Message):
    from_user = message.from_user
    userprofile = get_userprofile(from_user.id)

    if userprofile:
        message_user("Alright, sending you latest deals seen no earlier than today", message=message, instant=True)

        deal_list = list(models.Deal.objects.filter(id__gt=userprofile.last_deal_sent_id, created_at__gte=date.today()))

        for deal in deal_list:
            message_user("Deal: {0} [Link]({1}) At: {2}".format(deal.title, deal.link, deal.created_at.isoformat()),
                         message=message)

        if deal_list:
            userprofile.last_deal_sent_id = deal_list[-1].id
            userprofile.save()
        else:
            message_user("No new deals yet. Wait for it.", message=message, instant=True)
    else:
        failas_notregistered(message)


def command_addinterest(message: Message):
    from_user = message.from_user
    interests_str = ' '.join(message.text.split()[1:])

    if not interests_str:
        message_user("Maybe try the command as follows /addinterest shaver", message=message, instant=True)
        return

    interests_list = interests_str.split(',')

    userprofile = get_userprofile(from_user.id)

    if not userprofile:
        failas_notregistered(message)
        return

    for interest in interests_list:
        userprofile.interests.append(interest.lower())

    userprofile.save()

    message_user("Added interest: {0}".format(interests_str), message.chat_id, instant=True)


def command_removeinterest(message: Message):
    from_user = message.from_user
    interests_str = ' '.join(message.text.split()[1:])

    if not interests_str:
        message_user("Maybe try the command as follows /removeinterest shaver", message=message, instant=True)
        return

    interests_list = interests_str.split(',')

    userprofile = get_userprofile(from_user.id)

    if not userprofile:
        failas_notregistered(message)
        return

    for interest in interests_list:
        if interest in userprofile.interests:
            userprofile.interests.remove(interest)

    userprofile.save()

    message_user("Removed interest: {0}".format(interests_str), message.chat_id, instant=True)


def message_user(text, chat_id=None, instant=False, message=None):
    if not chat_id and not message:
        return

    if instant:
        time.sleep(1)
    else:
        time.sleep(random.randint(2, 6))

    bot = Bot(getattr(settings, 'TELEGRAM_BOT_TOKEN', ''))

    keyboardbutton_list = [
        [
            KeyboardButton('/start'),
            KeyboardButton('/help')
        ],
        [
            KeyboardButton('/addinterest'),
            KeyboardButton('/removeinterest'),
            KeyboardButton('/listinterest')
        ],
        [
            KeyboardButton('/latest')
        ]
    ]

    # replykeyboard = ReplyKeyboardMarkup(keyboardbutton_list, one_time_keyboard=True)

    if message:
        sent_message = message.reply_text(text, parse_mode=telegram.ParseMode.MARKDOWN)  # , reply_markup=replykeyboard)
    elif chat_id:
        sent_message = bot.send_message(chat_id, text, parse_mode=telegram.ParseMode.MARKDOWN)  # , reply_markup=replykeyboard)

    lcm = models.LogChatMessage()
    lcm.original_msg = sent_message.to_dict()
    lcm.direction = models.LogChatMessage.DIRECTION_OUTGOING
    lcm.fromwhom = 'Bot'
    lcm.kind = models.LogChatMessage.KIND_MSG_RESPONSE
    lcm.save()


def check_interests():
    userprofile_list = models.UserProfile.objects.filter(duser__is_active=True)

    for userprofile in userprofile_list:
        # get django user connected to the telegram user
        duser = userprofile.duser
        # check if they're active, if not no need to continue
        if not duser.is_active:
            continue

        user_interests_list = userprofile.interests  # List[str]
        deal_list = list(
            models.Deal.objects.filter(id__gt=userprofile.last_deal_checked_id,
                                       created_at__gte=date.today()))

        for deal in deal_list:
            user_interests_list = list(map(lambda word: word.lower(), user_interests_list))

            if deal.meta is None:
                continue

            deal_word_cloud = deal.meta.get('word_cloud', [])

            for interest in user_interests_list:
                if interest in deal_word_cloud:
                    try:
                        # found an interest in one of the deals, msg the user
                        message_user(
                            "I think we found an interest {0} in {1}. Here's the [link]({2}) for it. Seen at {2}".format(
                                interest,
                                deal.title,
                                deal.link,
                                deal.created_at.isoformat()),
                            userprofile.chat_id)
                    except Exception as ex:
                        # for any kind of exception, log it and disable user so that we don't keep on sending
                        # them messages
                        logger.exception(ex)
                        duser.is_active = False
                        duser.save()

        if deal_list:
            # save which deal we last checked
            userprofile.last_deal_checked_id = deal_list[-1].id
            userprofile.save()


def command_listinterest(message: Message):
    from_user = message.from_user

    user_profile = get_userprofile(from_user.id)

    message_user("Here are your interests:\n{0}".format(','.join(user_profile.interests)), message=message,
                 instant=True)


def command_help(message: Message):
    """

    :param message:
    :return:
    """
    help_msg = """
You are now talking to the Aussie Shopper bot. This bot will help you to find relevant deals.
Try the following:
1. /listinterest to list your currently registered interests
2. /addinterest <interest> to add an interest ex. /addinterest earphones
3. /removeinterest <interest> to remove an interest ex. /removeinterest earphones
4. /latest to list the latest deals
5. /reset to remove all interests
6. /contact <text> to send a message to the admin ex. /contact I love your work
    """
    message_user(help_msg,
                 message=message)


def command_reset(message: Message):
    """
    Remove all interests for the user without them having to remove them one at a time
    """
    from_user = message.from_user
    userprofile = get_userprofile(from_user.id)

    if not userprofile:
        failas_notregistered(message)
        return

    userprofile.interests.clear()
    userprofile.save()

    message_user("Successfully removed all your interests", message.chat_id, instant=True)


def command_contact(message: Message):
    """
    Command to contact admin which the user with ID 1. This delivers the message to the admin.
    """
    from_user = message.from_user

    # send message to admin
    email_managers('contact.html', {
        'user_id': from_user.id,
        'message_text': message.text
    })

    # tell user that their message will be delivered
    message_user("Your message has been delivered. If necessary, someone will be in touch shortly.", message.chat_id, instant=True)


@shared_task
def handle_message(telegram_json_msg, logchat_id: int):
    bot = Bot(getattr(settings, 'TELEGRAM_BOT_TOKEN', ''))

    update = Update.de_json(telegram_json_msg, bot)
    message = update.message  # telegram.Message

    # fetch the log message we just stored, we'll be modifying it as we learn from about the msg
    lcm = models.LogChatMessage.objects.get(pk=logchat_id)

    if message.from_user:
        lcm.fromwhom = message.from_user.first_name

    cmd_dict_list = [{
        'command': 'start',
        'description': 'start - Starts the conversation',
        'callback': command_start,
        'kind': models.LogChatMessage.KIND_MSG_CMD_START
    }, {
        'command': 'latest',
        'description': 'latest - Get the latest deal that I haven\'t seen yet',
        'callback': command_latestdeals,
        'kind': models.LogChatMessage.KIND_MSG_CMD_LATEST
    }, {
        'command': 'addinterest',
        'description': '',
        'callback': command_addinterest,
        'kind': models.LogChatMessage.KIND_MSG_CMD_ADD_INTEREST
    }, {
        'command': 'removeinterest',
        'description': '',
        'callback': command_removeinterest,
        'kind': models.LogChatMessage.KIND_MSG_CMD_REMOVE_INTEREST
    }, {
        'command': 'listinterest',
        'description': 'listinterest - List the interests that you\'re monitoring deals for',
        'callback': command_listinterest,
        'kind': models.LogChatMessage.KIND_MSG_CMD_LIST_INTEREST
    }, {
        'command': 'help',
        'description': 'help - Help me!',
        'callback': command_help,
        'kind': models.LogChatMessage.KIND_MSG_CMD_HELP
    }, {
        'command': 'reset',
        'description': 'reset - Removes all user interests',
        'callback': command_reset,
        'kind': models.LogChatMessage.KIND_MSG_CMD_RESET
    }, {
        'command': 'contact',
        'description': 'contact - Contact the admin',
        'callback': command_contact,
        'kind': models.LogChatMessage.KIND_MSG_CMD_CONTACT
    }]

    for cmd_dict in cmd_dict_list:
        cmd_handler = CommandHandler(cmd_dict['command'], cmd_dict['callback'])

        if cmd_handler.check_update(update):
            cmd_dict['callback'](message)

            # modify the kind of logchat message stored after we know what it is
            lcm.kind = cmd_dict.get('kind', models.LogChatMessage.KIND_MSG_UNKNOWN)
            break
    else:
        command_unknown(message)

    lcm.save()


@shared_task()
def broadcast_to_users(text: str):
    user_profiles = models.UserProfile.objects.all()

    for up in user_profiles:
        chat_id = up.chat_id

        message_user(text, chat_id=chat_id)
