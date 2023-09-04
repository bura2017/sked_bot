import json

import psycopg2
import logging
import os


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
                days varchar,
                time INTEGER
                );"""
        )
except psycopg2.errors.DuplicateTable as e:
    logging.warning("Database error: %s" % e.args)


try:
    with connection.cursor() as cursor:
        cursor.execute(
            """CREATE TABLE skeds(
                id BIGINT,
                chat_id BIGINT, 
                mes_id BIGINT
                );"""
        )
except psycopg2.errors.DuplicateTable as e:
    logging.warning("Database error: %s" % e.args)


def psql_execute(cmd):
    logging.info("Execute database command: %s" % cmd)
    try:
        with connection.cursor() as cursor1:
            cursor1.execute(cmd)
    except psycopg2.errors.UniqueViolation as e:
        logging.warning("Duplicate error from postgres: %s" % e.args)


def create_user(user_id, username, time, days):
    psql_execute("INSERT INTO users(id, username, time, days) VALUES "
                 "(%s, '%s', %s, '%s');" % (user_id, username, time, days))


def get_time(user_id):
    with connection.cursor() as cursor1:
        time = cursor1.execute(f"""SELECT time FROM users where id = {user_id}""")
        logging.info("Got time from database %s" % time)
        return time


def get_users():
    with connection.cursor() as cursor1:
        cursor1.execute("SELECT id FROM users")
        users = cursor1.fetchall()
        logging.debug("Got users from database: %s" % users)
        return users[0]
