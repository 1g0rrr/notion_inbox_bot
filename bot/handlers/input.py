from bot.page_commands import parse_title_and_execute_from_command
from bot.translations import localize
from typing import Callable, Tuple
from telegram import message, messageid
import telegram
from telegram.ext import dispatcher
from telegram.message import Message
from bot_app.models import TelegramChat, TelegramUser
from django.core.management import BaseCommand
from django.conf import settings
from datetime import datetime, timezone
from bot.decorators import get_or_create_user_and_chat, check_notion_link_in_chat, cooldown_check
from bot import constants
from bot.conversations import greetings
from bot.conversations import edit_notion_page
from bot import common
from telegram.ext.dispatcher import Dispatcher, run_async

from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from notion.block import Children, TextBlock, BasicBlock, SubsubheaderBlock, BulletedListBlock, HeaderBlock, SubheaderBlock, CalloutBlock, Block
from typing import Any, Callable, Iterable, List, Mapping, Optional, Text, Type, TypeVar, Union
from threading import Thread
import time
import traceback
from bot import global_services
from django.db.models import F

# THREADING
def _thread_target_function(threadingFunction:Callable[..., Any], threadingFunctionArgs: Iterable[Any], lastAddedThread: Thread):
    if isinstance(lastAddedThread, Thread):
        if lastAddedThread.is_alive():
            lastAddedThread.join()

    threadingFunction(*threadingFunctionArgs)

# Эта функция добавляет мою функцию в тред.
def add_to_parrallel_queue(threadingFunction: Callable[..., Any], threadingFunctionArgs: Iterable[Any], context: CallbackContext):
    
    lastAddedThread = context.chat_data.get(constants.CD_LAST_ADDED_THREAD_OBJ)
    
    lastAddedThread = Thread(target=_thread_target_function, args=[threadingFunction, threadingFunctionArgs, lastAddedThread])
    lastAddedThread.start()
    context.chat_data[constants.CD_LAST_ADDED_THREAD_OBJ] = lastAddedThread



# ADDING DATE BLOCK
def _check_block_is_date(locBlock: BasicBlock) -> Tuple[bool, datetime]:
    srcTitle = locBlock.title_plaintext

    srcTitle = srcTitle.strip()

    isDate = False
    dateObject = None

    try:
        dateObject = datetime.strptime(srcTitle, '%d %B %Y')
        isDate = True
    except ValueError:
        isDate = False

    return isDate, dateObject

def _formatDateToStr(locDate:datetime):
    return locDate.strftime('%d %B %Y')

def _get_block_before_second_date(notion_page:BasicBlock) -> BasicBlock:
    cur_count = 0
    for index, loc_block in enumerate(notion_page.children):
        isDate, dateObj = _check_block_is_date(loc_block)
        if(isDate):
            cur_count += 1
            if(cur_count == 2):
                return notion_page.children[index - 1]

    return None


def check_or_create_first_date_block(notion_page: Block, message_date: datetime):

    newServiceBlock = None

    # inbox_page = global_services.get_notion_client().get_block(te)
    #context.chat_data.get(constants.CD_NOTION_PAGE_OBJ)

    firstLine = next(iter(notion_page.children), None)

    userCurrentDate = message_date

    try:
        if(firstLine is not None):
            isDate, dateObject = _check_block_is_date(firstLine)

            if(not isDate):
                # Если верхняя строка вообще не дата - добавляем сервисную строку с датой.
                newServiceBlock = notion_page.children.add_new(SubsubheaderBlock, title=_formatDateToStr(userCurrentDate))
            else:
                if(userCurrentDate.date() > dateObject.date()):
                    #Если дата в сообщении старше текущей - создаем новую сервисную строку    
                    newServiceBlock = notion_page.children.add_new(SubsubheaderBlock, title=_formatDateToStr(userCurrentDate))
        else:
            newServiceBlock = notion_page.children.add_new(SubsubheaderBlock, title=_formatDateToStr(userCurrentDate))

        if(newServiceBlock is not None):
            newServiceBlock.move_to(notion_page, "first-child")
    except:
        print('Can\'t add date. No access.')


def _add_message_after(notion_page: Block, message_text:str, targetBlock:BasicBlock):

    messages_arr = message_text.split('\n')
    prev_message = None
    for raw_mesage in messages_arr:
        new_message = None
        if(raw_mesage[:1] == '-'):
            block_title = raw_mesage[1:]
            # Если следующий символ пробел - удаляем его
            if(block_title[:1] == ' '):
                block_title = block_title[1:]
            new_message = notion_page.children.add_new(BulletedListBlock, title=block_title)

        elif(raw_mesage[:1] == '!'):
            block_title = raw_mesage[1:]
            if(block_title[:1] == ' '):
                block_title = block_title[1:]
            new_message = notion_page.children.add_new(CalloutBlock, title=block_title, icon="💡") # 

        # ЗАГОЛОВКИ
        elif(raw_mesage[:5] == '= = ='):
            block_title = raw_mesage[5:]
            if(block_title[:1] == ' '):
                block_title = block_title[1:]
            new_message = notion_page.children.add_new(SubsubheaderBlock, title=block_title)

        elif(raw_mesage[:3] == '==='):
            block_title = raw_mesage[3:]
            if(block_title[:1] == ' '):
                block_title = block_title[1:]
            new_message = notion_page.children.add_new(SubsubheaderBlock, title=block_title)

        elif(raw_mesage[:3] == '###'):
            block_title = raw_mesage[3:]
            if(block_title[:1] == ' '):
                block_title = block_title[1:]
            new_message = notion_page.children.add_new(SubsubheaderBlock, title=block_title)

        elif(raw_mesage[:3] == '= ='):
            block_title = raw_mesage[3:]
            if(block_title[:1] == ' '):
                block_title = block_title[1:]
            new_message = notion_page.children.add_new(SubheaderBlock, title=block_title)

        elif(raw_mesage[:2] == '=='):
            block_title = raw_mesage[2:]
            if(block_title[:1] == ' '):
                block_title = block_title[1:]
            new_message = notion_page.children.add_new(SubheaderBlock, title=block_title)

        elif(raw_mesage[:2] == '##'):
            block_title = raw_mesage[2:]
            if(block_title[:1] == ' '):
                block_title = block_title[1:]
            new_message = notion_page.children.add_new(SubheaderBlock, title=block_title)

        elif(raw_mesage[:1] == '='):
            block_title = raw_mesage[1:]
            if(block_title[:1] == ' '):
                block_title = block_title[1:]
            new_message = notion_page.children.add_new(HeaderBlock, title=block_title)

        elif(raw_mesage[:1] == '#'):
            block_title = raw_mesage[1:]
            if(block_title[:1] == ' '):
                block_title = block_title[1:]
            new_message = notion_page.children.add_new(HeaderBlock, title=block_title)

        else:
            new_message = notion_page.children.add_new(TextBlock, title=raw_mesage)

        if(prev_message is None):
            if(targetBlock is not None):
                new_message.move_to(targetBlock, position="after")
            else:
                new_message.move_to(notion_page, position="first-child")
        else:
            new_message.move_to(prev_message, position="after")

        prev_message = new_message


# UPLOAD TO NOTION
def upload_to_notion(context: CallbackContext, user_message: Message, got_it_message: Message, telegram_chat:TelegramChat):

    notion_page:Block = global_services.get_notion_client().get_block(telegram_chat.notion_page_id)

    page_is_upward = context.chat_data.get(constants.CD_PAGE_IS_UPWARD)
    page_is_diary = context.chat_data.get(constants.CD_PAGE_IS_DIARY)

    try:
        if(page_is_diary and not page_is_upward):
            check_or_create_first_date_block(notion_page, user_message.date)
        
            block_before_second_date = _get_block_before_second_date(notion_page)

            if(block_before_second_date is None):
                # Если блока перед второй датой нет - просто добавляем в низ списка
                _add_message_after(notion_page, user_message.text, notion_page.children[-1])
            else:
                # Если блок перед второй датой есть - добавляем сообщение после него.
                _add_message_after(notion_page, user_message.text, block_before_second_date)

        elif(page_is_diary and page_is_upward):
            check_or_create_first_date_block(notion_page, user_message.date)

            # Добавление сообщения на вторую строчку
            _add_message_after(notion_page, user_message.text, notion_page.children[0])
        elif(not page_is_diary and page_is_upward):
            # Просто добавление на верх страницы
            _add_message_after(notion_page, user_message.text, None)
        else:
            # Добавляем просто в конец страницы.
            target_message = None if len(notion_page.children) <= 0 else notion_page.children[-1] 
            _add_message_after(notion_page, user_message.text, target_message)

        got_it_message.edit_text(text = localize("Готово.")) 

    except Exception as e: 
        got_it_message.edit_text(text = localize("Ошибка."))
        common.send_lost_access_message(telegram_chat)




# MAIN COMMAND
@cooldown_check
@get_or_create_user_and_chat
@check_notion_link_in_chat
def input_command(update: Update, context: CallbackContext, *args, **kwargs):

    telegram_user:TelegramUser = kwargs.get(constants.P_TELEGRAM_USER_OBJ)
    telegram_chat:TelegramChat = kwargs.get(constants.P_TELEGRAM_CHAT_OBJ)

    telegram_chat.last_message_at_utc = datetime.now(tz=timezone.utc)
    telegram_chat.last_message_text_cache = '' if update.message.text is None else str(update.message.text)
    telegram_chat.save()    

    telegram_user.last_message_at_utc = datetime.now(tz=timezone.utc)
    telegram_user.messages_count = F('messages_count') + 1
    telegram_user.save()

    # time.sleep(0.2)
    # [" + inbox_page.title + "](https://t.me/)
    # , reply_to_message_id=update.message.message_id
    # update.message.reply_to_message()

# Это небольшой фикс, что тайтл я теперь храню в базе.
    if(telegram_chat.notion_page_title == ''):
        notion_page = global_services.get_notion_client().get_block(telegram_chat.notion_page_url)
        if(notion_page is not None):
            telegram_chat.notion_page_title = notion_page.title_plaintext
            parse_title_and_execute_from_command(telegram_chat, update=update, context=context)
            Dispatcher.get_instance().bot.send_message(chat_id=telegram_chat.telegram_chat_id, text=localize('Для обновления страницы используйте команду /refresh'))


    time.sleep(0.2)
    
    got_it_message = context.bot.send_message(chat_id=update.effective_chat.id, text=localize("Готово"), parse_mode=ParseMode.MARKDOWN)
    # Вот, щас норм. Но в некоторых слушаях - не отправлять этот комплит. Когда прошлые уже загрузились.
    add_to_parrallel_queue(threadingFunction=upload_to_notion, threadingFunctionArgs=[context, update.message, got_it_message, telegram_chat], context=context)

    # Интересно что рефреш никак не помогает. Хотя теоретически должен вроде.
    # telegram_chat.refresh_from_db()


    # Удаляем старый листен. (вместо апдейта)
    time.sleep(0.2)
    common.delete_last_waiting_message(telegram_chat)

    common.send_waiting_input_message(telegram_chat)



