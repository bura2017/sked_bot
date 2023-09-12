from skedbot import vars, db
import multiprocessing
import time
from datetime import datetime, timedelta
import logging
import copy


def zeroing():
    while True:
        day_beginning = datetime.now().strftime("%Y-%m-%dT00:00:00")
        time_passed = datetime.now() - datetime.strptime(day_beginning, "%Y-%m-%dT%H:%M:%S")
        sleep_time = timedelta(days=1).total_seconds() - time_passed.total_seconds()
        time.sleep(sleep_time)

        reminder_days = db.get_all_reminder_days()
        weekday = datetime.now().weekday()
        for user_id, day in reminder_days.items():
            if day.get(weekday) is not None:
                db.update_if_remind(user_id, True)

        raise RestartReminder()


def _handle_reminders(reminders_list, is_open):
    now = datetime.now()

    loop_dict = copy.copy(reminders_list)
    for user_id, remind_time in loop_dict.items():
        delta = remind_time - now
        if delta.total_seconds() < 60:
            if delta.total_seconds() > 0:
                vars.bot.send_message(user_id, vars.reminder_open_message if is_open else vars.reminder_close_message)
            if is_open:
                db.update_if_remind(user_id, False)
            else:
                db.update_remind_close_time(user_id, None)
            reminders_list.pop(user_id)

    return reminders_list


def remind():
    while True:
        open_reminders = db.get_open_reminders()
        open_reminders = _handle_reminders(open_reminders, True)

        close_reminders = db.get_close_reminders()
        close_reminders = _handle_reminders(close_reminders, False)

        today_reminders = list(open_reminders.values()) + list(close_reminders.values())

        if today_reminders:
            next_reminder_time = min(today_reminders)
            time_to_pass = next_reminder_time - datetime.now()
            sleep_time = time_to_pass.total_seconds()
            logging.info("Next reminder at %s in %s seconds" % (next_reminder_time.strftime("%d-%m-%yT%H:%M"), sleep_time))
            time.sleep(sleep_time-10)
        else:
            logging.info("No reminders for today, sleep long")
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
        super(RestartReminder, self).__init__(args)
