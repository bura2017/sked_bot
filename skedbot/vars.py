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


reminderMessage = 'Время ответить за скед!!'
notYourDayReminder = 'Вообще ты мог сегодня не писать, но раз уж написал - ответь за скед!'

google_sheet = 'rand'

time_timer = 0
all_users = {}

list_with_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

list_with_hours = {"6 часов": 6, "10 часов": 10, "12 часов": 12}

list_with_sked_hours = {"Обнови на 5": 5, "Обнови на 6": 6, "Обнови на 7": 7, "Обнови на 8": 8, "Обнови на 9": 9,
                        "Обнови на 10": 10}

hello_button = 'Привет'


keyWords = ['#sked']

how_to_use_message = "Для настройки бота: \n" \
                     "Шаг 1: задайте гугл таблицу <b>/add_gs [link на таблицу]</b>\n"\
                     "Шаг 2: настройте удобное вам время и дни недели командой <b>/settings</b>\n" \
                     "Шаг 3: добавьте ключевые теги, которые буду отслеживаться.\n" \
                     "Тег #sked там уже есть. Для добавленя новых используйте команду <b>/keywords.</b>\n" \
                     "Для этого напишите\n<b>/keywords - слово, которое хотите добавить.</b>\n" \
                     "Вот и все. Бот настроен."

help_message = "Вот команды, которые вы можете использовать" \
               "\n\n" \
               "/start - включить бота\n" \
               "/help - открыть список всех команд\n" \
               "/how_to_use - как использовать бота\n" \
               "<b>/add_gs - добавить гугл таблицу</b>\n" \
               "/settings - настройки\n" \
               "/time - изменить время полученмя напоминалок\n" \
               "/keywords - добавить новое ключевое слово"

dic = []
dict_with_mes_id = {}

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

messages_need_to_answer = []

gs = gsheet.GoogleSheet()

bot_state = {}
default_bot_state = 'start'
