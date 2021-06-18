from bot import global_services
from telegram.ext.dispatcher import Dispatcher
from bot import page_commands
from bot_app.models import TelegramChat
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ConversationHandler
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Bot
from notion.utils import InvalidNotionIdentifier
from telegram.ext.handler import Handler
from bot import constants
from notion.block import PageBlock, BasicBlock
from bot import common
from bot.decorators import get_or_create_user_and_chat, cooldown_check
import os
from bot.translations import localize
from django.conf import settings

GET_INITIAL_GREETING, GET_PAGE_PREPARING, GET_PAGE_SHARING, GET_INBOX_PAGE_LINK, TRY_AGAIN_NOTION = range(5)


@cooldown_check
@get_or_create_user_and_chat
def start_command(update: Update, context: CallbackContext, *args, **kwargs):
    print('open tutorial!')

# Вот тут удаляю название и делаю парсинг пустого. 
    telegram_chat:TelegramChat = kwargs.get(constants.P_TELEGRAM_CHAT_OBJ)
    telegram_chat.notion_page_title = ''
    telegram_chat.notion_page_url = ''
    telegram_chat.notion_page_id = ''
    telegram_chat.save()
    page_commands.parse_title_and_execute_from_command(telegram_chat, update=update, context=context)



    context.bot.send_message(chat_id=update.effective_chat.id, text=localize('Добро пожаловать!\nЭто бот, который пересылает пересылает сообщения в Notion.'))

    context.bot.send_message(chat_id=update.effective_chat.id, text=localize("Для работы с ботом нужно сделать два простых шага: \n\n1. Расшарить страницу с эмейлом: \n`inboxbot@dailymap.app`\n\n2. Скинуть ссылку в этот чат\n\n"), parse_mode=ParseMode.MARKDOWN)
    file_path = os.path.join(settings.IMAGES_DIR, 'tutorialv2_1.jpg')
    image = open(file_path, 'rb')
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=image)
    context.bot.send_message(chat_id=update.effective_chat.id, text=localize("Ожидаю ссылку на страницу:"))

    print('return GET_INBOX_PAGE_LINK')
    return GET_INBOX_PAGE_LINK

@get_or_create_user_and_chat
def got_first_inbox_page_link(update: Update, context: CallbackContext, *args, **kwargs):

    notion_link_str = update.message.text.strip()

    telegram_chat = kwargs.get(constants.P_TELEGRAM_CHAT_OBJ)

    validation_errors = common.check_notion_url_or_id_syntax(notion_link_str)

    if(len(validation_errors) == 0):

        notion_page_nullable:BasicBlock = global_services.get_notion_client().get_block(notion_link_str, force_refresh=True)
        access_errors = common.check_notion_page_access(notion_page_nullable)

        if(len(access_errors) == 0):
            telegram_chat.notion_page_url = '' if notion_page_nullable.get_browseable_url() is None else notion_page_nullable.get_browseable_url()
            telegram_chat.notion_page_id = '' if notion_page_nullable.id is None else str(notion_page_nullable.id)
            telegram_chat.notion_page_title = '' if notion_page_nullable.title_plaintext is None else str(notion_page_nullable.title_plaintext)
            telegram_chat.save()        

            context.bot.send_message(chat_id=update.effective_chat.id, text=localize("Спасибо! Всё готово. \nЕсли вам нужно будет обновить страницу выполните команду /refresh"))

            page_commands.parse_title_and_execute_from_command(telegram_chat, update=update, context=context)

            common.send_waiting_input_message(telegram_chat)
            return ConversationHandler.END
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=localize("Не удалось соединиться со страницой Notion. Пожалуйста, проверьте доступ к странице. Она должна быть расшарена с емейлом: `inboxbot@dailymap.app`\nОжидаю ссылку на страницу:"), parse_mode=ParseMode.MARKDOWN)
            return GET_INBOX_PAGE_LINK
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=localize("Не удалось распознать ссылку. Пожалуйста, проверьте правильность написания. Ссылка должна выглядеть так:\n`https://www.notion.so/00003333aaaa8888bbbb99997777cccc`\nОжидаю ссылку на страницу:"), parse_mode=ParseMode.MARKDOWN)

        print('return TRY_AGAIN_NOTION')
        return GET_INBOX_PAGE_LINK



def cancel_greeting_handler(update: Update, context: CallbackContext, *args, **kwargs):
    return ConversationHandler.END


conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start_command)],
    states={
        GET_INBOX_PAGE_LINK: [MessageHandler(Filters.text & ~Filters.command, got_first_inbox_page_link)],
    },
    fallbacks=[CommandHandler('cancel', cancel_greeting_handler)],
    allow_reentry=True
)