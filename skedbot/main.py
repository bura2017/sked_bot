from telebot import types
import re
import time
from skedbot import vars, reminder, db
import logging
from skedbot.planner import Planner
import googleapiclient


# start command
@vars.bot.message_handler(commands=['start'])
def start(message):
    logging.debug("Start from user %s" % message.from_user)
    if message.chat.id != message.from_user.id:
        db.add_chat(message.chat.id, message.chat.title, message.chat.type)
    db.add_user(message.from_user.id, message.from_user.username, message.chat.id)
    logging.info("User registered: id='%s', first_name='%s', last_name='%s', username='%s'"
                 % (message.from_user.id,
                    message.from_user.first_name,
                    message.from_user.last_name,
                    message.from_user.username))
    vars.bot.send_message(message.chat.id, "Привет. Я sked бот.", parse_mode='html')
    vars.bot.send_message(message.chat.id, vars.how_to_use_message, parse_mode='html')


# send to user all commands he can use
@vars.bot.message_handler(commands=['help'])
def helper(message):
    vars.bot.send_message(message.chat.id, vars.help_message, parse_mode='html')


# how to use bot
@vars.bot.message_handler(commands=['how_to_use'])
def how_to_use(message):
    vars.bot.send_message(message.chat.id, vars.how_to_use_message, parse_mode='html')


@vars.bot.message_handler(commands=['add_gs'])
def add_gs_handler(message):
    vars.bot_state[message.chat.id] = 'add_gs'
    vars.bot.send_message(message.chat.id, 'Отправьте ссылку на гугл таблицу')


def add_gs(message):
    sheet_search = re.search(r"/d/(.*?)/edit", message.text)
    try:
        if db.add_gs(message.chat.id, sheet_search.group(1)) == 0:
            vars.bot.send_message(message.chat.id, 'Не получилось добавить таблицу в базу. Попробуйте снова команду /start')
            raise AssertionError("0 rows affected for chat %s" % message.chat.id)
        vars.gs.SPREADSHEET_ID = sheet_search.group(1)
        vars.gs.init_sheet()
        logging.info("New spreadsheet %s" % sheet_search.group(1))
        vars.bot.send_message(message.chat.id, 'Вы добавили гугл таблицу')
    except AttributeError:
        vars.bot.send_message(message.chat.id, 'Не получилось достать ID таблицы из адреса. Попробуйте снова')
    except Exception as e:
        logging.error("Failed to add google sheet '%s': %s" % (message.text, e.args))

    vars.bot_state[message.chat.id] = vars.DEFAULT_BOT_STATE


# command to change settings
@vars.bot.message_handler(commands=['settings'])
def settings(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Дни и время открывающего планнера")
    button2 = types.KeyboardButton("Время закрывающего планнера")
    button3 = types.KeyboardButton(vars.RETURN_BUTTON)
    markup.add(button1, button2, button3)
    days, time = db.get_days_and_time(message.from_user.id)
    if days:
        days_as_string = 'Напоминание по дням:\n'
    else:
        days_as_string = 'Напоминания выключены. \n'
    for d, t in days.items():
        days_as_string += '%s %s\n' % (vars.WEEKDAYS[int(d)], t)
    vars.bot_state[message.from_user.id] = 'settings'
    vars.bot.send_message(message.from_user.id, f'Режим настройки напоминалки.\nТекущие настройки:\n%s\n'
                                           f'Напоминание о закрывающем планнере через %s часов после открывающего'
                          % (days_as_string, time), reply_markup=markup)


# adding special words to search for
@vars.bot.message_handler(commands=['keywords'])
def keyword(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Тег для открывающего планнера")
    button2 = types.KeyboardButton("Тег для закрывающего планнера")
    button3 = types.KeyboardButton(vars.RETURN_BUTTON)
    markup.add(button1, button2, button3)
    open_tag, close_tag = db.get_keywords(message.from_user.id)
    vars.bot_state[message.from_user.id] = 'keywords'
    vars.bot.send_message(message.from_user.id, "Ваши текущие теги %s и %s для открывающего и закрывающего планнеров "
                                           "соответственно. \nВыберите тег, который хотите поменять"
                          % (open_tag, close_tag), reply_markup=markup)


# all cases when user sent text message
@vars.bot.message_handler(content_types=['text'])
def just_text(message):
    state = vars.bot_state.get(message.chat.id, vars.DEFAULT_BOT_STATE)
    if message.text == vars.RETURN_BUTTON:
        vars.bot.send_message(message.from_user.id, vars.help_message, reply_markup=types.ReplyKeyboardRemove())
        vars.bot_state[message.chat.id] = vars.DEFAULT_BOT_STATE
    elif state == 'add_gs':
        add_gs(message)
    elif state == 'settings':
        if message.text == "Время закрывающего планнера":
            vars.bot_state[message.chat.id] = 'time'
            time_mes = "Напишите числом через сколько часов напоминать о закрывающем планнере. \n" \
                       "Если число 0 - то напоминания о закрывающем планнере будут выключены"
            vars.bot.send_message(message.chat.id, time_mes, parse_mode='html')
        elif message.text == "Дни и время открывающего планнера":
            vars.bot_state[message.chat.id] = 'days'
            day_mes = """Напишите на каждой строке день недели и время для этого дня. Например,
            
Понедельник 13:00
Среда 11:00
Четверг 11:00"""
            vars.bot.send_message(message.chat.id, day_mes, parse_mode='html')
        elif message.text == 'Теги Расписаний':
            keyword(message)
    elif state == 'time':
        db.update_time(message.from_user.id, message.text)
        settings(message)
    elif state == 'days':
        days = {}
        for l in message.text.split("\n"):
            parsed_line = re.search(r'(\w+) (\d{1,2}:\d{1,2})', l)
            if parsed_line is None:
                vars.bot.send_message(message.chat.id, "Не смог разобрать строку: %s" % l, parse_mode='html')
            else:
                try:
                    day_number = vars.WEEKDAYS.index(parsed_line.group(1))
                    time.strptime(parsed_line.group(2), '%H:%M')
                    days[day_number] = parsed_line.group(2)
                except ValueError:
                    vars.bot.send_message(message.chat.id, "Не смог разобрать строку: %s" % l, parse_mode='html')
        db.update_days(message.from_user.id, days)
        vars.bot.send_message(message.chat.id, "Время напоминаний успешно обновлено")
        settings(message)
    elif state == 'keywords':
        if message.text == 'Тег для открывающего планнера':
            vars.bot_state[message.chat.id] = 'open_tag'
        elif message.text == 'Тег для закрывающего планнера':
            vars.bot_state[message.chat.id] = 'close_tag'
    elif state == 'open_tag':
        db.update_open_tag(message.from_user.id, message.text)
        keyword(message)
    elif state == 'close_tag':
        db.update_close_tag(message.from_user.id, message.text)
        keyword(message)
    else:
        keywords = db.get_keywords(message.from_user.id)
        if not keywords[0]:
            db.add_user(message.from_user.id, message.from_user.username, message.chat.id)
            keywords = vars.DEFAULT_KEYWORDS
        if message.text.split(maxsplit=1)[0] in keywords:
            # This code implements planners handling
            p = Planner(message.text)
            gs_id = db.get_gs(message.chat.id)
            if gs_id:
                vars.gs.SPREADSHEET_ID = gs_id
                try:
                    if message.forward_from is None:
                        user_id = message.from_user.id
                        username = message.from_user.username
                    else:
                        user_id = message.forward_from.id
                        username = message.forward_from.username
                    vars.gs.add_user(username, user_id)
                    vars.gs.insert_planner(user_id, p.day, "\n".join(p.body))
                    logging.info("Planner from user '%s', chat '%s', date '%s' was added to google sheet" %
                                 (username, message.chat.title, p.day.strftime('%d/%m/%y')))

                except googleapiclient.errors.HttpError as e:
                    logging.error(e)
                    if e.resp.status == 404:
                        vars.bot.send_message(message.chat.id, "Добавьте сначала google sheet для использования /add_gs")
                    elif e.resp.status == 403:
                        vars.bot.send_message(message.chat.id, "У меня нет прав вносить изменения в эту таблицу")
                    else:
                        vars.bot.send_message(message.chat.id, "Неизвестная ошибка")
                except AssertionError:
                    logging.warning("Tag was triggered but not parsed: %s" % message.text)
        else:
            # This is for unparsed messages which are ignored if chat is not private
            if message.chat.id == message.from_user.id:
                vars.bot.send_message(message.chat.id, "Не смог понять, чего вы хотите")


reminder.start()
vars.bot.polling(none_stop=True, logger_level=logging.INFO)
