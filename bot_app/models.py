from django.db import models
from django.db.models.fields import TextField

class TelegramUser(models.Model):
    created_at_utc = models.DateTimeField(
        auto_now_add=True,
    )
    telegram_user_id = models.IntegerField(
        unique=True,
    )
    full_name = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )
    username = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )
    language_code = models.CharField(
        max_length=10,
        blank=True,
        default=''
    )
    last_message_at_utc = models.DateTimeField(
        null=True,
    )
    timezone = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )    
    messages_count = models.IntegerField(
        default=0,
    )    
    paid_up_to_utc = models.DateTimeField(
        null=True,
    )
    discount_code = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )

    # def __str__(self):
    #     return f'#{self.created_at_utc} {self.full_name}'

class TelegramChat(models.Model):
    telegram_user_fkey = models.ForeignKey(
        to='bot_app.TelegramUser',
        on_delete=models.CASCADE,
    )
    created_at_utc = models.DateTimeField(
        auto_now_add=True,
    )
    telegram_user_id_cache = models.IntegerField(
        blank=True,
        null=True
    )
    full_name_cache = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )
    telegram_chat_id = models.IntegerField(
        unique=True,
    )
    chat_type = models.CharField(
        max_length=100,
        blank=True,
        default='',
    )
    notion_page_url = models.TextField(
        blank=True,
        default='',
    )
    notion_page_id = models.TextField(
        blank=True,
        default=''
    )    
    notion_page_title = models.TextField(
        blank=True,
        default=''
    )
    last_waiting_message_id = models.TextField(
        blank=True,
        default=''
    )
    last_message_at_utc = models.DateTimeField(
        null=True,
    )
    last_message_text_cache = models.TextField(
        blank=True,
        default=''
    )

    # def __str__(self):
    #     return f'#{self.created_at} {self.telegram_chat_id}'


