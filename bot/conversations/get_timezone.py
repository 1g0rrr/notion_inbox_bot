from bot_app.models import TelegramChat, TelegramUser
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ConversationHandler
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Bot
from notion.utils import InvalidNotionIdentifier
from telegram.ext.handler import Handler
from bot import constants
from notion.block import PageBlock, BasicBlock
from bot import common,page_commands
from bot.decorators import get_or_create_user_and_chat, cooldown_check
import os
from bot.translations import localize
from django.conf import settings
from geopy import geocoders
from geopy.point import Point
import pytz
from datetime import datetime
from telegram.ext.typehandler import TypeHandler

GET_CITY_NAME = range(1)


@cooldown_check
@get_or_create_user_and_chat
def timezone_command_callback(update: Update, context: CallbackContext, *args, **kwargs):
    _send_welcome_message(update, context)
    return GET_CITY_NAME

@cooldown_check
@get_or_create_user_and_chat
def got_city_name(update: Update, context: CallbackContext, *args, **kwargs):

    city_name = update.message.text.strip()

    telegram_chat:TelegramChat = kwargs.get(constants.P_TELEGRAM_CHAT_OBJ)
    telegram_user:TelegramUser = kwargs.get(constants.P_TELEGRAM_USER_OBJ)

    # Зацикливаем

    g = geocoders.GoogleV3(api_key='AIzaSyCFydmiSLjAOsQWHJQRKsoYDy4omL7BhWk')
    g_result = g.geocode(city_name)
    print('g_result' + str(g_result))
    if(g_result is not None):
        place, location = g_result
        timezone_geopy = g.reverse_timezone(location)
        timezone_string = timezone_geopy.pytz_timezone.zone

        print('timezone_string ' + timezone_string)

        ctz = pytz.timezone(timezone_string)
        d = datetime.now(tz=ctz)

        telegram_user.timezone = '' if timezone_string is None else str(timezone_string)
        telegram_user.save()

        context.bot.send_message(chat_id=update.effective_chat.id, text=localize("Готово! Ваш часовой пояс: {}. Вы всегда можете изменить его с помощью команды /timezone.").format(timezone_string))

        page_commands.parse_title_and_execute_from_command(telegram_chat, update=update, context=context)
        common.send_waiting_input_message(telegram_chat)
        
        return ConversationHandler.END
    else:

        context.bot.send_message(chat_id=update.effective_chat.id, text=localize("Не удалось определить город. Попробуйте ввести другое название:"))
        return GET_CITY_NAME


def cancel_getting_city(update: Update, context: CallbackContext, *args, **kwargs):
    return ConversationHandler.END

def _send_welcome_message(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=localize("Напишите название крупного города в вашем часовом поясе:"))


# @cooldown_check
# @get_or_create_user_and_chat
# def get_timezone_handler_callback(update: Update, context: CallbackContext):
#     _send_welcome_message(update, context)
#     return GET_CITY_NAME

# get_timezone_handler = TypeHandler(GetTimezoneUpdate, get_timezone_handler_callback)
timezone_command = CommandHandler('timezone', timezone_command_callback)

conversation_handler = ConversationHandler(
    # get_timezone_handler, 
    entry_points=[ timezone_command],
    states={
        GET_CITY_NAME: [MessageHandler(Filters.text, got_city_name)],
    },
    fallbacks=[CommandHandler('cancel', cancel_getting_city)],
    allow_reentry=True
)