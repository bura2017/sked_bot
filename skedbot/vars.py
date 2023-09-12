import telebot
import os
import logging
import sys


import gettext
_ = gettext.gettext


LOGGING_FORMAT = "%(asctime)s %(levelname)s %(message)s"
logging.basicConfig(level=logging.INFO,
                    format=LOGGING_FORMAT,
                    # stream=sys.stdout)
                    filename='/var/log/sked.log',
                    filemode='a')


reminder_open_message = _("Время написать планнер на сегодня")
reminder_close_message = _('Время написать закрывающий планнер на сегодня')

how_to_import_history = _("""1. Зайдите в настройки чата, чью историю вы бы хотели загрузить
2. Выберите команду 'Export chat history'
3. Снимите все галочки, чтобы остался только текст
4. В поле 'Format' выберите 'Machine-readable JSON'
5. 'Save' -> 'Export' 
6. Загрузите файл result.json в чат с ботом и отправьте""")

WEEKDAYS = [_('Понедельник'), _('Вторник'), _('Среда'), _('Четверг'), _('Пятница'), _('Суббота'), _('Воскресенье')]

RETURN_BUTTON = _("В главное меню")
DEFAULT_CLOSE_TIME = 0
DEFAULT_KEYWORDS = (DEFAULT_OPEN_TAG, DEFAULT_CLOSE_TAG) = ("#sked", "#done")

how_to_use_message = _("""
Я умею напоминать о планнерах на день и собирать ваши планнеры из разных групп/каналов.

Чтобы использовать меня как напоминалку:
Шаг 1: Добавьте меня в группу/канал, в которой вы пишете планнеры. 
Шаг 2: Настройте время, дни недели и чаты, используя команду /settings.

Чтобы я собирал планнеры в таблицу:
Шаг 1: Добавьте меня в группу/канал, в которой вы пишете планнеры. 
Шаг 2: Добавьте ссылку на пустой Google Sheet командой /add_gs, чтобы я мог туда сохранять ваши планнеры. 

По умолчанию используются теги #sked и #done для открывающего и закрывающего планнеров соответственно. 
Чтобы это изменить используйте команду /keywords 
""")

help_message = _("Вот команды, которые вы можете использовать" 
               "\n\n" 
               "/start - включить бота\n" 
               "/help - открыть список всех команд\n" 
               "/how_to_use - как использовать бота\n" 
               "/add_gs - добавить гугл таблицу\n" 
               "/settings - настройки напоминания о планнере\n" 
               "/keywords - теги для открывающего и закрывающего планнера\n" 
               "/clear - сбросить все настройки\n"
               "/import_history - добавить планнеры из истории")

TOKEN = os.getenv("BOT_TOKEN")
if TOKEN is None:
    # Then try to get TOKEN another way
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                key, value = line.strip().split('=', 1)
                if key == 'BOT_TOKEN':
                    TOKEN = value
    except FileNotFoundError:
        logging.error("Couldn't find env variable BOT_TOKEN or file .env")
        exit(-1)

bot = telebot.TeleBot(TOKEN)
logging.info("Bot successfully started")

google_sheets = {}

bot_state = {}
DEFAULT_BOT_STATE = 'start'
