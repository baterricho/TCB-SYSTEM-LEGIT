from django.contrib import admin

from .models import Conversation, Message, MessageAttachment


admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(MessageAttachment)
