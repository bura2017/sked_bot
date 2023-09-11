import json

import psycopg2
import logging
import os
from skedbot import vars
from datetime import datetime


# connecting with database
database_url = os.getenv("DATABASE_URL")
if not database_url:
    logging.error("Missing environment variable: DATABASE_URL")
    raise ValueError("Missing DATABASE_URL")

connection = psycopg2.connect(database_url)
connection.autocommit = True


try:
    with connection.cursor() as cursor:
        cursor.execute(
            """CREATE TABLE users(
                id BIGINT not null PRIMARY KEY,
                username varchar(32),
                reminder_days varchar,
                hours_number INTEGER,
                open_tag varchar(32),
                close_tag varchar(32),
                chat_id BIGINT,
                if_remind_open boolean,
                remind_close_time varchar(20)
                );"""
        )
except psycopg2.errors.DuplicateTable as e:
    logging.warning("Database error: %s" % e.args)


try:
    with connection.cursor() as cursor:
        cursor.execute(
            """CREATE TABLE skeds(
                chat_id BIGINT not null PRIMARY KEY,
                title varchar(32),
                gs_id varchar(64),
                tg_type varchar(32)
                );"""
        )
except psycopg2.errors.DuplicateTable as e:
    logging.warning("Database error: %s" % e.args)


def _psql_insert(cmd):
    logging.info("Execute database command: %s" % cmd)
    try:
        with connection.cursor() as cursor1:
            cursor1.execute(cmd)
            r = cursor1.rowcount
            return r
    except psycopg2.errors.UniqueViolation as e:
        logging.warning("Duplicate error from postgres: %s" % e.args)


def _psql_select(cmd):
    logging.info("Execute database command: %s" % cmd)
    with connection.cursor() as cursor1:
        cursor1.execute(cmd)
        r = cursor1.fetchall()
        return r


def _psql_select_one(cmd):
    r = _psql_select_one(cmd)
    if len(r) > 1:
        raise ValueError()
    return next(iter(r), None)


def add_chat(chat_id, title, chat_type):
    _psql_insert("INSERT INTO skeds(chat_id, title, tg_type) VALUES "
                 "(%s, '%s', '%s');"
                 % (chat_id, title, chat_type))


def add_user(user_id, username, chat_id):
    _psql_insert("INSERT INTO users(id, username, reminder_days, hours_number, open_tag, close_tag, chat_id, "
                 "if_remind_open, remind_close_time) VALUES "
                 "(%s, '%s', '%s', %s, '%s', '%s', %s, %s, %s);"
                 % (user_id, username, '{}', 0, vars.DEFAULT_OPEN_TAG, vars.DEFAULT_CLOSE_TAG, chat_id, False, 'null'))


def get_users():
    users = _psql_select_one("SELECT id FROM users;")
    return users[0]


def get_days_and_time(user_id):
    days, time = _psql_select_one("SELECT reminder_days, hours_number FROM users where id='%s';" % user_id)
    return json.loads(days), time


def add_gs(chat_id, gs_id):
    return _psql_insert("update skeds set gs_id='%s' where chat_id='%s';" % (gs_id, chat_id))


def update_time(user_id, hours_num):
    _psql_insert("update users set hours_number='%s' where id='%s';" % (hours_num, user_id))


def update_days(user_id, days):
    _psql_insert("update users set reminder_days='%s' where id='%s';" % (json.dumps(days), user_id))


def get_keywords(user_id):
    r = _psql_select_one("select open_tag, close_tag from users where id='%s';" % user_id)
    if r is not None:
        open_tag, close_tag = r
    else:
        open_tag, close_tag = (None, None)

    return open_tag, close_tag


def update_open_tag(user_id, tag):
    _psql_insert("update users set open_tag='%s' where id='%s';" % (tag, user_id))


def update_close_tag(user_id, tag):
    _psql_insert("update users set close_tag='%s' where id='%s';" % (tag, user_id))


def get_gs(chat_id):
    r = _psql_select_one("select gs_id from skeds where chat_id='%s';" % chat_id)
    if r is None:
        return None
    return r[0]


def get_all_reminder_days():
    s = _psql_select("select id, reminder_days from users;")

    r = {x[0]: x[1] for x in s}
    return r


def get_open_reminders():
    s = _psql_select("select id, reminder_days from users where if_remind_open=true;")

    weekday = datetime.now().weekday()

    r = {x[0]: datetime.strptime(x[1][weekday], "%H:%M") for x in s if x[1].get(weekday) is not None}
    return r


def get_close_reminders():
    s = _psql_select("select id, remind_close_time from users where remind_close_time != null;")

    r = {x[0]: datetime.strptime(x[1], "%d-%m-%yT%H:%M") for x in s}
    return r


def update_if_remind(user_id, if_remind):
    _psql_insert("update users set if_remind_open=%s where id='%s';" % (if_remind, user_id))


def update_remind_close_time(user_id, rtime):
    if rtime is None:
        _psql_insert("update users set remind_close_time=null where id='%s';" % (user_id))
    else:
        time_string = rtime.strftime("%d-%m-%yT%H:%M")
        _psql_insert("update users set remind_close_time='%s' where id='%s';" % (time_string, user_id))
