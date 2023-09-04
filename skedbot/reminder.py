from skedbot import vars
import threading
import logging
import json


def answer():
    while True:
        keys = vars.redis.keys('*')
        logging.debug("Keys: %s" % json.dumps(keys))

        for i in keys:
            try:
                with vars.connection.cursor() as cursor5:
                    cursor5.execute(f"""SELECT chat_id FROM skeds WHERE mes_id = {int(i)}""")
                    chat_id = cursor5.fetchone()[0]
                    if not vars.redis.exists(i):
                        print(i)
                        vars.bot.send_message(chat_id, vars.reminderMessage, reply_to_message_id=int(i))
                        with vars.connection.cursor() as cursor6:
                            cursor6.execute(f"""DELETE FROM skeds where mes_id = {int(i)}""")
            except Exception as excep:
                print(f'Вы не зарегистрированы {excep}')


def start():
    thread_for_answering = threading.Thread(target=answer, args=(), daemon=True)
    thread_for_answering.start()
