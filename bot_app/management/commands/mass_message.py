from bot.translations import localize
from bot_app.models import TelegramChat,TelegramUser
from django.core.management import BaseCommand
from django.conf import settings
from telegram.ext.dispatcher import Dispatcher, run_async
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import telegram
import time

class Command(BaseCommand):

    def handle(self, *args, **options):

        mass_message_text = localize(
            "👋 <b>Всем привет!</b>\n"
            "Хорошие новости, бот обновился и стал лучше!\n\n"
            "✔️ <b>Новинка 1</b>\n"
            "Теперь работает команда \"at 17:00\" с помощью которой бот будет ежедневно присылать напоминание о том, что нужно что-то добавить в чат. Подробнее о настройке команд можете почитать в /help (который тоже добавился)\n\n"
            "✔️ <b>Новинка 2</b>\n"
            "Бот стал менее многословным, чтобы не засорять чат. Еще бот каждый раз присылает ссылку на страницу в Notion для удобства. А также исправлен ряд ошибок\n\n"
            "✔️ <b>Новинка 3</b>\n"
            "И самое интересное - это сообщество пользователей в виде телеграм-группы.\n"
            "Тут мы сможем обсуждать разработку этого бота и других инструментов для улучшения работы с Notion.\n\n"
            "🤝 Было бы очень интересно узнать ваш опыт первых дней использования бота.\n"
            "Напишите пожалуйста что было полезным, а что нет и какие у вас есть еще идеи?\n\n"
            "<b>Ссылка на сообщество:</b> https://t.me/notion_inbox_bot_chat\n"
        )

        test_list = ['igor', 'beaver']
        print('igor' in test_list)

        already_sent = []

# telegram_user_id='447478326'
        objects = TelegramUser.objects.all().filter()
        telegram_user:TelegramUser
        for telegram_user in objects:
            print(telegram_user.telegram_user_id, telegram_user.full_name)
            bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN) if settings.TELEGRAM_BOT_TOKEN else None
            if telegram_user.telegram_user_id not in already_sent:
                try:
                    bot.send_message(chat_id=telegram_user.telegram_user_id, text=mass_message_text, parse_mode=ParseMode.HTML)
                    print('Отправляю')
                except:
                    print('Не удалось отправить ' + str(telegram_user))
                time.sleep(1.5)





