from bot.translations import localize
from bot.page_commands import parse_title_and_execute, parse_title_and_execute_from_command
from notion.client import NotionClient
from telegram.message import Message
from bot_app.models import TelegramChat, TelegramUser
from django.core.management import BaseCommand
from django.conf import settings
from datetime import datetime, timezone, tzinfo
import time
from bot import constants
from bot import global_services
from bot.conversations import greetings,get_timezone
from bot.conversations import edit_notion_page
from bot import common
from telegram.ext.dispatcher import Dispatcher, run_async
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from notion.block import Block, Children, TextBlock, BasicBlock, SubsubheaderBlock
from bot.handlers import input
from bot.decorators import get_or_create_user_and_chat, check_notion_link_in_chat, cooldown_check
import os
import telegram

@get_or_create_user_and_chat
def help_command(update: Update, context: CallbackContext, *args, **kwargs) -> None:

    help_text_1 = (
        "👋 <b>Привет!</b>\n\n"
        "Базовая идея бота проста. Всё что вы ему отправите будет записано на странице Notion\n\n"
        "Чтобы расширить возможности бота вы можете добавить команды в заголовок страницы.\n\n\n"
        "🔥 <b>Команды для бота:</b>\n\n"
        "<b>upward</b> - все новые сообщение будут записываться сверху. Удобно для \"инбокса\", чтобы не нужно было скролить вниз к последним записям.\n\n"
        "<b>diary</b> - сообщения будут разделяться датами. Удобно для ведения дневников и для того, чтобы не превращать страницу в сплошную стену текста.\n\n"
        "<b>at 17:00</b> - бот будет каждый день в указанное время присылать напоминание. Чтобы напоминания приходили в определённые дни - можно добавить номера этих дней, например: \"at 19:00 135\"\n\n"

        "⚠️ Команды нужно записывать вконце заголовка после вертикальной черты. Можно использовать сразу несколько команд, разделяя их запятыми:"

    )
    update.message.reply_text(localize(help_text_1), parse_mode=ParseMode.HTML)

    
    file_path = os.path.join(settings.IMAGES_DIR, 'title_commands.jpg')
    image = open(file_path, 'rb')
    update.message.reply_photo(photo=image)    


    help_text_2 = (
        "⚠️ После изменения заголовка нужно выполнить команду /refresh, чтобы название страницы перечиталось.\n\n\n"
        "🤝 <b>Сообщество</b>\n"
        "Если для вас что-то осталось непонятным, или вы хотите принять участие в обсуждении бота - добавляйтесь в наше дружелюбное комьюнити:\n"
        "https://t.me/notion_inbox_bot_chat\n"
    )
    update.message.reply_text(localize(help_text_2), parse_mode=ParseMode.HTML)


@get_or_create_user_and_chat
def community_command(update: Update, context: CallbackContext, *args, **kwargs) -> None:

    help_text_2 = (
        "🤝 <b>Сообщество</b>\n"
        "Добро пожаловать в наше дружелюбное комьюнити:\n"
        "https://t.me/notion_inbox_bot_chat\n"
    )
    update.message.reply_text(localize(help_text_2), parse_mode=ParseMode.HTML)

@cooldown_check
@get_or_create_user_and_chat
@check_notion_link_in_chat
def refresh_page_command(update: Update, context: CallbackContext, *args, **kwargs) -> None:
    update.message.reply_text(localize("👀 Обновляю страницу"))

    # Давай тут брать по чат-айди из базы ссылку на ноушен и его 
    telegram_chat:TelegramChat = kwargs.get(constants.P_TELEGRAM_CHAT_OBJ)

    notion_page_nullable:BasicBlock = global_services.get_notion_client().get_block(telegram_chat.notion_page_id, force_refresh=True)

    access_errors_list = common.check_notion_page_access(notion_page_nullable)

    if(len(access_errors_list) > 0):
        # Не делаю парсинга. Всё остаётся как раньше.
        common.send_lost_access_message(telegram_chat)
    else:
        # Урл и ИД не меняются, поэтому кроме тайтла ничего не нужно сохранять.
        telegram_chat.notion_page_title = '' if notion_page_nullable.title_plaintext is None else str(notion_page_nullable.title_plaintext)
        telegram_chat.save()
        parse_title_and_execute_from_command(telegram_chat, update=update, context=context)
        common.send_waiting_input_message(telegram_chat)



@get_or_create_user_and_chat
def unknown_command(update: Update, context: CallbackContext, *args, **kwargs):
    context.bot.send_message(chat_id=update.effective_chat.id, text=localize("К сожалению, не удалось распознать команду."))

# def run_async_messages():
#     for i in range(0, 10):
#         time.sleep(1.2)
#         print('message after sleep')
#         bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN) if settings.TELEGRAM_BOT_TOKEN else None
#         bot.send_message(chat_id='447478326', text='Игорь, привет! ' + str(i))
#         print('bot', bot)            

class Command(BaseCommand):
    help = "Telegram bot."


    def handle(self, *args, **options):
        """Start the bot."""

        global_services.start_client(notion_token=settings.NOTION_CLIENT_TOKEN)
        print('Notion client: ' + str(global_services.get_notion_client().current_user))

        updater = Updater(token=settings.TELEGRAM_BOT_TOKEN, use_context=True)
        print('Telegram client:' + str(updater.bot))

        updater.dispatcher.add_handler(greetings.conversation_handler)
        updater.dispatcher.add_handler(get_timezone.conversation_handler)
        updater.dispatcher.add_handler(CommandHandler("refresh", refresh_page_command))
        updater.dispatcher.add_handler(CommandHandler("help", help_command))
        updater.dispatcher.add_handler(CommandHandler("community", community_command))
        updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, input.input_command))
        updater.dispatcher.add_handler(MessageHandler(Filters.command, unknown_command))

# Вот тут джобы запустить бы все. Давай джоб для конкретного чата запустим.
# Инициализация сервисов.
# Обойти циклом чаты.




        chats_for_parsing_title_set = TelegramChat.objects.exclude(notion_page_title='')
        print('Обьектов с не нулл тайтлом ' + str(len(chats_for_parsing_title_set)))
        for telegram_chat in chats_for_parsing_title_set.iterator():
            parse_title_and_execute(telegram_chat)


        if not settings.IS_WEBHOOK:
            updater.start_polling()
            # ^ polling is useful for development since you don't need to expose endpoints
        else:
            print
            # print(updater.bot.get_webhook_info())
            # updater.start_webhook(
            #     listen=settings.TELEGRAM_BOT_WEBHOOK_HOST,
            #     port=settings.TELEGRAM_BOT_WEBHOOK_PORT,
            #     url_path=settings.TELEGRAM_BOT_TOKEN,
            #     key='certs/private.key',
            #     cert='certs/cert.pem'
            # )
            # updater.bot.set_webhook(url=settings.TELEGRAM_BOT_WEBHOOK_URL + settings.TELEGRAM_BOT_TOKEN)


        # Dispatcher.get_instance().run_async(run_async_messages)

        updater.idle()

        print('After idle')





