import json

from django.contrib import admin
from django.utils.safestring import mark_safe

from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLexer

from api import models


class AussieShopperModelAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    list_display = ['__str__', 'created_at']

    def get_list_display(self, request):
        list_to_display = self.list_display

        if hasattr(self, 'extra_list_display'):
            list_to_display = self.extra_list_display.copy()
            list_to_display.extend(self.list_display[1:])

        return list_to_display

    def get_readonly_fields(self, request, obj=None):
        read_only_fields_to_display = self.readonly_fields

        if hasattr(self, 'extra_readonly_fields'):
            read_only_fields_to_display = self.extra_readonly_fields.copy()
            read_only_fields_to_display.extend(self.readonly_fields)

        return read_only_fields_to_display

    def get_pretty_json(self, data):
        """
        Function to display pretty version of our json field
        """
        # Convert the data to sorted, indented JSON
        response = json.dumps(data, sort_keys=True, indent=2)

        # Truncate the data. Alter as needed
        response = response[:5000]

        # Get the Pygments formatter
        formatter = HtmlFormatter(style='colorful')

        # Highlight the data
        response = highlight(response, JsonLexer(), formatter)

        # Get the stylesheet
        style = "<style>" + formatter.get_style_defs() + "</style><br>"

        # Safe the output
        return mark_safe(style + response)


@admin.register(models.LogChatMessage)
class LogChatMessageAdmin(AussieShopperModelAdmin):
    readonly_fields = ['pretty_message']
    list_filter = ['kind', 'fromwhom', 'direction']
    extra_list_display = ['kind', 'fromwhom', 'direction', 'towhom']

    def pretty_message(self, lcmessage: models.LogChatMessage):
        return self.get_pretty_json(lcmessage.original_msg)

    def towhom(self, lcmessage: models.LogChatMessage):
        if lcmessage.direction == models.LogChatMessage.DIRECTION_INCOMING:
            # incoming message so receiver is bot
            return 'Bot'

        if 'chat' in lcmessage.original_msg:
            message_chat = lcmessage.original_msg['chat']

            if 'first_name' in message_chat:
                return message_chat['first_name']
            elif 'username' in message_chat:
                return message_chat['username']
            else:
                return '-'

        return '-'

@admin.register(models.UserProfile)
class UserProfileAdmin(AussieShopperModelAdmin):
    pass


@admin.register(models.Deal)
class DealAdmin(AussieShopperModelAdmin):
    readonly_fields = ['pretty_meta', 'pretty_raw']

    def pretty_meta(self, deal: models.Deal):
        return self.get_pretty_json(deal.meta)

    def pretty_raw(self, deal: models.Deal):
        return self.get_pretty_json(deal.raw)


@admin.register(models.DataStore)
class DataStoreAdmin(AussieShopperModelAdmin):
    readonly_fields = ['pretty_data']

    def pretty_data(self, datastore: models.DataStore):
        return self.get_pretty_json(datastore.data)
