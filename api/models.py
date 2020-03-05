from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField
from django.contrib.auth.models import User


class AussieShopperModel(models.Model):
    created_at = models.DateTimeField(verbose_name='Created At',
                                      auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Updated At',
                                      auto_now=True)

    class Meta:
        abstract = True


class LogChatMessage(AussieShopperModel):
    KIND_MSG_UNKNOWN = 'MU'
    KIND_MSG_CMD_ADD_INTEREST = 'MCAI'
    KIND_MSG_CMD_REMOVE_INTEREST = 'MCRI'
    KIND_MSG_CMD_LIST_INTEREST = 'MCLI'
    KIND_MSG_CMD_START = 'MCS'
    KIND_MSG_CMD_LATEST = 'MCL'
    KIND_MSG_CMD_HELP = 'MCH'
    KIND_MSG_CMD_RESET = 'MRES'
    KIND_MSG_CMD_CONTACT = 'MCON'
    KIND_MSG_RESPONSE = 'MR'
    MSG_KIND = [
        (KIND_MSG_UNKNOWN, 'Unknown'),
        (KIND_MSG_CMD_ADD_INTEREST, 'Add Interest'),
        (KIND_MSG_CMD_REMOVE_INTEREST, 'Remove Interest'),
        (KIND_MSG_CMD_LATEST, 'Latest Deals'),
        (KIND_MSG_CMD_LIST_INTEREST, 'List Interests'),
        (KIND_MSG_CMD_START, 'Start'),
        (KIND_MSG_CMD_HELP, 'Help'),
        (KIND_MSG_RESPONSE, 'Response'),
        (KIND_MSG_CMD_REMOVE_INTEREST, 'Reset'),
        (KIND_MSG_CMD_CONTACT, 'Contact')
    ]
    DIRECTION_INCOMING = 'I'
    DIRECTION_OUTGOING = 'O'
    MSG_DIRECTION = [
        (DIRECTION_INCOMING, 'Incoming'),
        (DIRECTION_OUTGOING, 'Outgoing')
    ]

    text = models.CharField(verbose_name='Text',
                            max_length=100)
    original_msg = JSONField(null=True)
    kind = models.CharField(verbose_name='Kind',
                            max_length=5,
                            default=KIND_MSG_UNKNOWN,
                            choices=MSG_KIND)
    fromwhom = models.CharField(verbose_name='Who sent this',
                                max_length=150,
                                default=str)
    direction = models.CharField(verbose_name='Message Direction',
                                 max_length=1,
                                 choices=MSG_DIRECTION,
                                 default=DIRECTION_INCOMING)

    class Meta:
        verbose_name = 'LogChatMessage'
        verbose_name_plural = 'LogChatMessages'

    def __str__(self):
        return '{0}'.format(self.id)


class UserProfile(AussieShopperModel):
    duser = models.OneToOneField(User,
                                 null=True,
                                 on_delete=models.SET_NULL)
    chat_id = models.IntegerField(verbose_name='Chat ID',
                                  default=0)
    telegram_user_id = models.IntegerField(verbose_name='Telegram User ID',
                                           default=0)
    last_deal_sent_id = models.IntegerField(verbose_name='Last Deal Sent',
                                            default=0)
    last_deal_checked_id = models.IntegerField(verbose_name='Last Deal Checked',
                                               default=0)
    interests = ArrayField(verbose_name='Interests',
                           base_field=models.CharField(max_length=50, blank=True),
                           default=list)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return '{0} - {1}'.format(self.duser, self.chat_id)


class Deal(AussieShopperModel):
    title = models.CharField(verbose_name='Deal',
                             max_length=250)
    link = models.URLField(verbose_name='Deal URL',
                           default=str)
    raw = JSONField(null=True)
    meta = JSONField(null=True)

    class Meta:
        verbose_name = 'Deal'
        verbose_name_plural = 'Deals'

    def __str__(self):
        return '{0}'.format(self.title)


class DataStore(AussieShopperModel):
    key = models.CharField(verbose_name='Store Key',
                           max_length=50,
                           unique=True)
    data = JSONField(verbose_name='Data Store',
                     default=dict)

    class Meta:
        verbose_name = 'Data Store'
        verbose_name_plural = 'Data Stores'

    def __str__(self):
        return '{0}'.format(self.key)
