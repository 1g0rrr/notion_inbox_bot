import traceback
from telegram.parsemode import ParseMode
from bot.translations import localize
from time import sleep
from bot_app.models import TelegramChat, TelegramUser
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, Dispatcher
from telegram import Update
from datetime import datetime, timedelta
import pytz
from typing import Tuple

import re
from bot import constants
from bot import conversations


ERROR_NO_TIMEZONE = 'ERROR_NO_TIMEZONE'
ERROR_WRONG_TIME = 'ERROR_WRONG_TIME'
ERROR_WRONG_ARGS = 'ERROR_WRONG_ARGS'
ERROR_WRONG_SYNTAX = 'ERROR_WRONG_SYNTAX'


def _at_timer_handler(handler_context):
    chat_id = handler_context.job.context
    print('hndls chat_id' + str(chat_id))

    Dispatcher.get_instance().bot.send_message(
        chat_id=chat_id, text=localize("Напоминание! Время что-то написать:"))


def _at_handler(command_args_str: str, telegram_chat: TelegramChat) -> Tuple[list, list]:

    telegram_user: TelegramUser = telegram_chat.telegram_user_fkey

    errors_list = []
    messages_list = []

    if(telegram_user.timezone == ''):
        errors_list.append(ERROR_NO_TIMEZONE)
        return errors_list, messages_list

    time_string = None
    days_string = None

    args_arr = command_args_str.split(' ')

    if(len(args_arr) == 1):
        time_string = args_arr[0]
    elif(len(args_arr) == 2):
        time_string, days_string = args_arr
    else:
        errors_list.append(ERROR_WRONG_ARGS)
        return errors_list, messages_list

    user_timezone = pytz.timezone(telegram_user.timezone)

    try:
        naive_user_datetime = datetime.strptime(time_string, '%H:%M')
    except:
        errors_list.append(ERROR_WRONG_TIME)
        return errors_list, messages_list

    # time_obj = datetime.now() + timedelta(seconds=1)
    # t = '21:43'

    tz_user_datetime = user_timezone.localize(naive_user_datetime)
    tz_user_time = tz_user_datetime.timetz()

    days_list = []
    if(days_string is not None):
        for day_s in days_string:
            day_i = int(day_s)
            day_i -= 1
            if(day_i == -1):
                day_i = 6
            days_list.append(day_i)
    else:
        days_list = range(7)

    try:
        job = Dispatcher.get_instance().job_queue.run_daily(_at_timer_handler, time=tz_user_time, name=str(
            telegram_chat.telegram_chat_id), days=tuple(days_list), context=telegram_chat.telegram_chat_id)
        messages_list.append(
            localize('Напоминание установлено на *{}*').format(command_args_str))
    except:
        errors_list.append(ERROR_WRONG_SYNTAX)
        return errors_list, messages_list

    return errors_list, messages_list


def _upward_handler(command_args, telegram_chat) -> Tuple[list, list]:

    Dispatcher.get_instance(
    ).chat_data[telegram_chat.telegram_chat_id][constants.CD_PAGE_IS_UPWARD] = True

    messages_list = []
    messages_list.append(localize('Выполнена команда *{}*').format('upward'))
    return [], messages_list


def _diary_handler(command_args, telegram_chat) -> Tuple[list, list]:

    Dispatcher.get_instance(
    ).chat_data[telegram_chat.telegram_chat_id][constants.CD_PAGE_IS_DIARY] = True

    messages_list = []
    messages_list.append(localize('Выполнена команда *{}*').format('diary'))
    return [], messages_list


def execute_command(command_name: str, command_args_string: str, telegram_chat) -> Tuple[list, list]:

    print('execute: ' + command_name + ':' + str(command_args_string))

    # Это не хэндлеры. Переименовать. Хэндлер - это то что программа делает, реакция на таймер, например.
    if(command_name == 'at'):
        return _at_handler(command_args_string, telegram_chat)
    elif(command_name == 'upward'):
        return _upward_handler(command_args_string, telegram_chat)
    elif(command_name == 'diary'):
        return _diary_handler(command_args_string, telegram_chat)
    else:
        messages_list = [
            localize("Не удалось распознать команду \"*{}*\"").format(command_name)]
        return [], messages_list


def _clean_past_commands(telegram_chat: TelegramChat):

    # ОЧИЩАЮ ДЕЙСТВИЯ ВСЕХ ПРОШЛЫХ КОММАНД
    Dispatcher.get_instance(
    ).chat_data[telegram_chat.telegram_chat_id][constants.CD_PAGE_IS_DIARY] = False
    Dispatcher.get_instance(
    ).chat_data[telegram_chat.telegram_chat_id][constants.CD_PAGE_IS_UPWARD] = False

    jobs = Dispatcher.get_instance().job_queue.get_jobs_by_name(
        str(telegram_chat.telegram_chat_id))
    for j in jobs:
        j.schedule_removal()


def parse_title_and_execute(telegram_chat: TelegramChat) -> Tuple[list, list]:

    page_title = telegram_chat.notion_page_title


    print('parse title: {}'.format(page_title))

    _clean_past_commands(telegram_chat)

    errors_list = []
    messages_list = []


    title_split2 = page_title.rsplit("|", 1)
    if(len(title_split2) == 2):
        commands_string = title_split2[1]
    else:
        # Если комманд вообще нет, то выход.
        # НЕ ЗАБЫВАТЬ ПРО ЭТОТ РЕТУРН!!!111
        return [], []

    # Убираю лишние пробелы. (больше одного подряд)
    commands_string = re.sub(' {2,}', ' ', commands_string)
    commands_strings_arr = commands_string.split(',')

    commands_tuples = []

    for command_string in commands_strings_arr:
        command_split2 = command_string.strip().split(' ', 1)
        command_name = command_split2[0]

        # У команды может не быть аргументов
        if(len(command_split2) == 2):
            command_args_string = command_split2[1].strip()
        else:
            command_args_string = ''

        commands_tuples.append((command_name, command_args_string))

    # Тут же надо сбросить все джобсы, чтобы потом заново их назначить


    for cmd_tuple in commands_tuples:
        # В этом месте сохранить. Тут я должен знать чат айди.
        loc_errors, loc_messages = execute_command(
            cmd_tuple[0], cmd_tuple[1], telegram_chat)
        errors_list.extend(loc_errors)
        messages_list.extend(loc_messages)



    return errors_list, messages_list

def parse_title_and_execute_from_command(telegram_chat:TelegramChat, update: Update, context: CallbackContext):
    errors_list, messages_list = parse_title_and_execute(telegram_chat)

    # Пробуем изменить название чата.
    if(telegram_chat.chat_type == constants.CHAT_TYPE_GROUP):
        try:
            
            title_set_success = Dispatcher.get_instance().bot.set_chat_title(chat_id=telegram_chat.telegram_chat_id, title=telegram_chat.notion_page_title)

            if(title_set_success):
                messages_list.append(localize("Название чата изменено на \"{}\".").format(telegram_chat.notion_page_title))
            else:
                messages_list.append(localize("Не удалось изменить название чата. Пожалуйста добавьте бота в список администраторов группы."))
        except:
            messages_list.append(localize("Не удалось изменить название чата. Пожалуйста добавьте бота в список администраторов группы."))

    for error in errors_list:
        if(error == ERROR_NO_TIMEZONE):
            Dispatcher.get_instance().bot.send_message(chat_id=telegram_chat.telegram_chat_id, text=localize("Внимание! Для работы с напоминаниями нужно установить часовой пояс. Пожалуйста, выполните команду /timezone"))            
            key = conversations.get_timezone.conversation_handler._get_key(update)
            conversations.get_timezone.conversation_handler.update_state(conversations.get_timezone.GET_CITY_NAME, key)
        elif(error == ERROR_WRONG_TIME):
            Dispatcher.get_instance().bot.send_message(chat_id=telegram_chat.telegram_chat_id, text=localize("Внимание! Не удалось прочитать команду \"*at*\". Неверно указано время.")) 
        elif(error == ERROR_WRONG_ARGS):
            Dispatcher.get_instance().bot.send_message(chat_id=telegram_chat.telegram_chat_id, text=localize("Внимание! Не удалось прочитать команду \"*at*\". Неверное количество аргументов."))
        elif(error == ERROR_WRONG_SYNTAX):
            Dispatcher.get_instance().bot.send_message(chat_id=telegram_chat.telegram_chat_id, text=localize("Внимание! Не удалось прочитать команду \"*at*\", пожалуйста, проверьте синтаксис."))

    if(len(errors_list) == 0):
        for message in messages_list:
            print(message)
            Dispatcher.get_instance().bot.send_message(chat_id=telegram_chat.telegram_chat_id, text=message, parse_mode=ParseMode.MARKDOWN)

    print('Jobs count ', len(Dispatcher.get_instance().job_queue.get_jobs_by_name(str(telegram_chat.telegram_chat_id)) ) )
    # traceback.print_stack()
    traceback.print_exc()
    # raise Exception("Super ex")

