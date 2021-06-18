from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import Dispatcher
from bot_app.models import TelegramUser, TelegramChat
from datetime import datetime, timedelta, timezone
from bot import constants
from django.conf import settings
from bot import global_services
from bot import common
from bot.translations import localize
import traceback

def get_or_create_user_and_chat(callback):
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        telegram_user, user_just_created = TelegramUser.objects.get_or_create(telegram_user_id=update.effective_user.id, defaults={
            'username': '' if update.effective_user.username is None else str(update.effective_user.username),
            'full_name': '' if update.effective_user.full_name is None else str(update.effective_user.full_name),
            'language_code': '' if update.effective_user.language_code is None else str(update.effective_user.language_code),
            'last_message_at_utc': datetime.utcnow(),
            'paid_up_to_utc': datetime.utcnow(),
        })


        telegram_chat, chat_just_created = TelegramChat.objects.get_or_create(telegram_chat_id=update.effective_chat.id, defaults={
            'telegram_user_fkey': telegram_user,
            'telegram_user_id_cache': '' if update.effective_user.id is None else str(update.effective_user.id),
            'full_name_cache': '' if update.effective_user.full_name is None else str(update.effective_user.full_name),
            'chat_type': '' if update.effective_chat.type is None else str(update.effective_chat.type),
            'last_message_at_utc': datetime.utcnow(),
        })

        kwargs[constants.P_TELEGRAM_USER_OBJ] = telegram_user
        kwargs[constants.P_TELEGRAM_CHAT_OBJ] = telegram_chat

        return callback(update, context, *args, **kwargs)

    return wrapper

def check_notion_link_in_chat(callback):
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):

        telegram_chat = kwargs.get(constants.P_TELEGRAM_CHAT_OBJ)

        if(telegram_chat.notion_page_id == ''):
            context.bot.send_message(chat_id=update.effective_chat.id, text=localize("Не удалось найти ссылку на страницу Notion. Пожалуйста начните с команды /start ."))
            return None

            # create_notion_page(telegram_chat)

        return callback(update, context, *args, **kwargs)
    return wrapper


_user_actions_utc_timestamps = []

def _is_overheat(max_actions:int, time_gap:int):

    if len(_user_actions_utc_timestamps) < max_actions: return False

    max_saved_time = _user_actions_utc_timestamps[-max_actions]
    max_alowed_time = datetime.now(tz=timezone.utc) - timedelta(seconds=time_gap)

    return max_saved_time > max_alowed_time 

def cooldown_check(callback):
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        current_timestamp = datetime.now(tz=timezone.utc)
        

        # in 1 second
        if _is_overheat(max_actions=2, time_gap=1): 
            context.bot.send_message(chat_id=update.message.chat_id, text=localize("Слишком много действий в секунду!"))
            return False

        # in 10 seconds
        if _is_overheat(max_actions=10, time_gap=10): 
            context.bot.send_message(chat_id=update.message.chat_id, text=localize("Слишком много действий за 10 секунд!"))
            return False
        
        # in 1 minute
        if _is_overheat(max_actions=20, time_gap=60): 
            context.bot.send_message(chat_id=update.message.chat_id, text=localize("Слишком много действий за 1 минуту!"))
            return False

        # in 1 hour
        if _is_overheat(max_actions=50, time_gap=60 * 60):
            context.bot.send_message(chat_id=update.message.chat_id, text=localize("Слишком много действий за 1 час!"))
            return False

        # in 24 hours
        max_actions_in_24_hours = 150
        if _is_overheat(max_actions=max_actions_in_24_hours, time_gap=60 * 60 * 24):
            context.bot.send_message(chat_id=update.message.chat_id, text=localize("Слишком много действий за 24 часа!"))
            return False

        if(len(_user_actions_utc_timestamps) > max_actions_in_24_hours):
            _user_actions_utc_timestamps.pop(0)

        _user_actions_utc_timestamps.append(current_timestamp)
    
        return callback(update, context, *args, **kwargs)
    return wrapper
