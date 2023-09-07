import telebot
from skedbot import gsheet
import redis
import os
import logging
import sys


LOGGING_FORMAT = "%(asctime)s %(levelname)s %(message)s"
logging.basicConfig(level=logging.INFO,
                    format=LOGGING_FORMAT,
                    stream=sys.stdout)
                    # filename='/var/log/sked.log',
                    # filemode='a')


reminder_open_message = ""
reminder_close_message = 'Время написать закрывающий планнер для сегодня'

time_timer = 0

WEEKDAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

RETURN_BUTTON = "В главное меню"
DEFAULT_CLOSE_TIME = 0
DEFAULT_KEYWORDS = (DEFAULT_OPEN_TAG, DEFAULT_CLOSE_TAG) = ("#sked", "#done")

how_to_use_message = """
Я умею напоминать о планнерах на день и собирать ваши планнеры из разных групп/каналов.

Чтобы использовать меня как напоминалку:
Шаг 1: Добавьте меня в группу/канал, в которой вы пишете планнеры. 
Шаг 2: Настройте время, дни недели и чаты, используя команду /settings.

Чтобы я собирал планнеры в таблицу:
Шаг 1: Добавьте меня в группу/канал, в которой вы пишете планнеры. 
Шаг 2: Добавьте ссылку на пустой Google Sheet командой /add_gs, чтобы я мог туда сохранять ваши планнеры. 

По умолчанию используются теги #sked и #done для открывающего и закрывающего планнеров соответственно. 
Чтобы это изменить используйте команду /keywords 
"""

help_message = "Вот команды, которые вы можете использовать" \
               "\n\n" \
               "/start - включить бота\n" \
               "/help - открыть список всех команд\n" \
               "/how_to_use - как использовать бота\n" \
               "/add_gs - добавить гугл таблицу\n" \
               "/settings - настройки напоминания о планнере\n" \
               "/keywords - теги для открывающего и закрывающего планнера\n" \
               "/clear - сбросить все настройки"

redis_url = os.getenv("REDIS_URL")
if not redis_url:
    logging.error("Missing environment variable: REDIS_URL")
    raise ValueError("Missing REDIS_URL")

redis = redis.Redis.from_url(redis_url)

TOKEN = os.getenv("BOT_TOKEN")
if TOKEN is None:
    # Then try to get TOKEN another way
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            key, value = line.strip().split('=', 1)
            if key == 'BOT_TOKEN':
                TOKEN = value

bot = telebot.TeleBot(TOKEN)
logging.info("Bot successfully started")

google_sheets = {}

bot_state = {}
DEFAULT_BOT_STATE = 'start'
