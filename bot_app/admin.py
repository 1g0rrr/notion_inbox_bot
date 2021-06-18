from django.contrib import admin
from .models import TelegramUser
from .models import TelegramChat


# Register your models here.
@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = [field.name for field in TelegramUser._meta.get_fields() if (not field.is_relation and field.name != 'id')]
    search_fields = ['full_name', 'telegram_user_id', 'username']

@admin.register(TelegramChat)
class TelegramChatAdmin(admin.ModelAdmin):
    list_display = [field.name for field in TelegramChat._meta.get_fields() if (not field.is_relation and field.name != 'id')]
    search_fields = ['full_name_cache', 'telegram_user_id_cache']
    
 
