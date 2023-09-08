from skedbot import vars, db
import threading
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
                db.update_if_remind_today(user_id, True)
        return


def remind():
    while True:
        hour_beginning = datetime.now().strftime("%Y-%m-%dT%H:00:00")
        time_passed = datetime.now() - datetime.strptime(hour_beginning, "%Y-%m-%dT%H:%M:%S")
        sleep_time = timedelta(hours=1).seconds-time_passed.seconds
        time.sleep(sleep_time)


def start():
    thread_for_zeroing = threading.Thread(target=zeroing, args=(), daemon=True)
    thread_for_zeroing.start()
    thread_for_reminding = threading.Thread(target=remind, args=(), daemon=True)
    thread_for_reminding.start()
