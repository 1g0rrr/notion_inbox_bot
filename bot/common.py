from bot.page_commands import parse_title_and_execute_from_command
from telegram.ext.dispatcher import Dispatcher
from bot_app.models import TelegramChat
from bot.translations import localize
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from notion.block import BasicBlock
from notion.client import NotionClient
from telegram.replymarkup import ReplyMarkup
from bot import constants
from notion.utils import InvalidNotionIdentifier
from telegram import Update, ParseMode
from telegram.message import Message
from bot import global_services

ERROR_WRONG_NOTION_LINK = 'ERROR_WRONG_NOTION_LINK'
ERROR_WRONG_NOTION_ACCESS = 'ERROR_WRONG_NOTION_ACCESS'
ERROR_SOMETHING_WRONG_WITH_NOTION = 'ERROR_SOMETHING_WRONG_WITH_NOTION'


def delete_last_waiting_message(telegram_chat:TelegramChat):
    if(telegram_chat.last_waiting_message_id != ''):
        # Dispatcher.get_instance().bot.edit_message_text(chat_id=telegram_chat.telegram_chat_id, message_id=telegram_chat.last_waiting_message_id,text="Complete.", parse_mode=ParseMode.MARKDOWN)
        try:
            Dispatcher.get_instance().bot.delete_message(chat_id=telegram_chat.telegram_chat_id, message_id=int(telegram_chat.last_waiting_message_id))
        except:
            print

        telegram_chat.last_waiting_message_id = ''
        telegram_chat.save()

def send_waiting_input_message(telegram_chat:TelegramChat):

    waiting_message = Dispatcher.get_instance().bot.send_message(chat_id=telegram_chat.telegram_chat_id, text=get_listen_message_string(telegram_chat), parse_mode=ParseMode.MARKDOWN, disable_notification=True)

    telegram_chat.last_waiting_message_id = '' if waiting_message.message_id is None else str(waiting_message.message_id)
    telegram_chat.save()


def update_waiting_input_message(telegram_chat:TelegramChat):

    if(telegram_chat.last_waiting_message_id != ''):
        new_text = get_listen_message_string(telegram_chat)
        Dispatcher.get_instance().bot.edit_message_text(chat_id=telegram_chat.telegram_chat_id, message_id=telegram_chat.last_waiting_message_id,text=new_text, parse_mode=ParseMode.MARKDOWN)    


def get_listen_message_string(telegram_chat:TelegramChat):
        # [" + inbox_page.title + "](https://t.me/)
    #TODO удалить
    #  notion_page = global_services.get_notion_client().get_block(telegram_chat.notion_page_id)
    return localize('Ожидаю ввод в "[{}]({})":').format(telegram_chat.notion_page_title, telegram_chat.notion_page_url)

def send_lost_access_message(telegram_chat:TelegramChat):
    Dispatcher.get_instance().bot.send_message(chat_id=telegram_chat.telegram_chat_id, text=localize('Не удалось подключиться к странице "[{}]({})". Пожалуйста, проверьте доступ, или добавьте другую страницу командой /start').format(telegram_chat.notion_page_title, telegram_chat.notion_page_url), parse_mode=ParseMode.MARKDOWN)
        
def check_notion_url_or_id_syntax(url_or_id:str) -> list:

    errors_list = []
    try:
        notion_page = global_services.get_notion_client().get_block(url_or_id)
        # if(isinstance(notion_page, BasicBlock)):
        #     print('Notion link is good')
        # else:
        #     errors_list.append(ERROR_WRONG_NOTION_ACCESS)
            
    except InvalidNotionIdentifier:
        errors_list.append(ERROR_WRONG_NOTION_LINK)
    except:
        errors_list.append(ERROR_SOMETHING_WRONG_WITH_NOTION)

    return errors_list

def check_notion_page_access(notion_page:BasicBlock) -> list:

    errors_list = []
    # Если бот удалили из доступа, то будет или страница None или эксплисит акксесс - Фолс.
    if(isinstance(notion_page, BasicBlock) and notion_page.space_info['userHasExplicitAccess']):
        if(notion_page.role == constants.NOTION_PAGE_ROLE_READ_WRITE or notion_page.role == constants.NOTION_PAGE_ROLE_EDITOR):
            print('Notion page is good')
        else:
            # Тут можно вывести дополнительное сообщение о неудаче в доступе.
            errors_list.append(ERROR_WRONG_NOTION_ACCESS)
    else:
        errors_list.append(ERROR_WRONG_NOTION_ACCESS)

    return errors_list



# def check_and_save_notion_link(notion_link: str, telegram_chat: TelegramChat, update: Update, context: CallbackContext) -> bool:
# # Сюда надо передать чат обджект. Беру его из кваргсов выше
# # Надо передать чат тайп? Может быть и апдейт весь, но лучше только тайп.
#     notion_client = global_services.get_notion_client()

#     raw_inbox_page = None
#     try:
#         raw_inbox_page = notion_client.get_block(notion_link, force_refresh=True)
#         if(isinstance(raw_inbox_page, BasicBlock)):
#             print('raw_inbox_page.role' + str(raw_inbox_page.role))
#                 # Вот с этого момента можно уже выделить
#             telegram_chat.notion_page_url = '' if notion_link is None else str(notion_link)
#             telegram_chat.notion_page_id = '' if raw_inbox_page.id is None else str(raw_inbox_page.id)
#             telegram_chat.save()

#             if(raw_inbox_page.role == constants.NOTION_PAGE_ROLE_READ_WRITE or raw_inbox_page.role == constants.NOTION_PAGE_ROLE_EDITOR):
                    
#             # Сохраняем тут инбокс пейдж. Блин, прийдется помнить когда обновлять все эти переменные в context.
#                 telegram_chat.notion_page_title = '' if raw_inbox_page.title_plaintext is None else str(raw_inbox_page.title_plaintext)
                    
#                 telegram_chat.save()
                
#                 parse_title_and_execute_from_command(telegram_chat, update=update, context=context)

#                 return True
#             else:
#                 # Тут можно вывести дополнительное сообщение о неудаче в доступе.
#                 return False
#     except InvalidNotionIdentifier:
#         print('InvalidNotionIdentifier')
#         return False
#     else:
#         return False