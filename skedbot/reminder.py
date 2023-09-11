from skedbot import vars, db
import multiprocessing
import time
from datetime import datetime, timedelta
import logging
import json


def zeroing():
    while True:
        day_beginning = datetime.now().strftime("%Y-%m-%dT00:00:00")
        time_passed = datetime.now() - datetime.strptime(day_beginning, "%Y-%m-%dT%H:%M:%S")
        sleep_time = time_passed.seconds - timedelta(days=1).seconds
        time.sleep(sleep_time)

        reminder_days = db.get_all_reminder_days()
        weekday = datetime.now().weekday()
        for user_id, day in reminder_days.items():
            if day.get(weekday) is not None:
                db.update_if_remind(user_id, True)
        return


def remind():
    while True:
        now = datetime.now()
        open_reminders = db.get_open_reminders()
        for user_id, remind_time in open_reminders.items():
            delta = now - remind_time
            if delta.seconds < 60:
                vars.bot.send_message(user_id, vars.reminder_open_message)
                db.update_if_remind(user_id, False)
                open_reminders.pop(user_id)

        close_reminders = db.get_close_reminders()
        for user_id, remind_time in close_reminders.items():
            delta = now - remind_time
            if delta.seconds < 60:
                vars.bot.send_message(user_id, vars.reminder_close_message)
                db.update_remind_close_time(user_id, None)
                close_reminders.pop(user_id)

        today_reminders = list(open_reminders.values()) + list(close_reminders.values())

        if today_reminders:
            next_reminder_time = min(today_reminders)
            time_to_pass = now - next_reminder_time
            sleep_time = time_to_pass.seconds
            time.sleep(sleep_time)
        else:
            time.sleep(timedelta(days=100).total_seconds())


def start():
    process_for_zeroing = multiprocessing.Process(target=zeroing, args=(), daemon=True)
    process_for_zeroing.start()
    process_for_reminding = multiprocessing.Process(target=remind, args=(), daemon=True)
    process_for_reminding.start()
    return process_for_reminding


class RestartReminder(Exception):
    def __init__(self):
        args = ['Restart Reminder called']
        super(RestartReminder).__init__(args)
