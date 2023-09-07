import logging
import sys
import json
import re
import six

from skedbot import db
from skedbot.main import handle_planner
from skedbot.vars import DEFAULT_KEYWORDS
from datetime import datetime
from googleapiclient.errors import HttpError


def search_for_planners(text, keywords):
    # Text is expected to be list
    is_planner = False
    planner_text = ''
    r = []
    for t in text:
        if isinstance(t, six.string_types):
            # handle planner maybe
            planner_text += t
        elif isinstance(t, dict):
            # familiar_types = ['hashtag', 'link', 'mention', 'pre', 'code', 'italic', 'mention_name', 'phone', 'bold',
            #                   'text_link', 'strikethrough', 'bot_command', 'spoiler']
            # if t['type'] not in familiar_types:
            #     print("New type %s " % t['type'])
            if t['type'] == 'hashtag' and t['text'] in keywords:
                if is_planner:
                    r.append(planner_text)
                is_planner = True
                planner_text = t['text']
            else:
                planner_text += t['text']
        else:
            logging.critical("I don't know what is it")
            assert False

    if is_planner:
        r.append(planner_text)
    return r


def main(path, start_from_mes=None):
    messages = []
    chat_title = '[unknown]'
    chat_id = '-944947277'
    with open(path, "r") as f:
        data = f.read()
        pdata = json.loads(data)
        chat_title = pdata.get('name', '[not specified]')
        messages = pdata.get('messages', [])

    for mes in messages:
        if start_from_mes is not None and mes['id'] < int(start_from_mes):
            continue
        text = mes.get('text', None)
        if isinstance(text, list):
            username = mes['from']
            user_id = re.match(r"^user(.*)$", mes['from_id']).group(1)
            mes_date = datetime.strptime(mes['date'], "%Y-%m-%dT%H:%M:%S")
            keywords = db.get_keywords(user_id)
            if None in keywords:
                db.add_user(user_id, username, user_id)
                keywords = DEFAULT_KEYWORDS
            planners = search_for_planners(text, keywords)
            for p_text in planners:
                try:
                    handle_planner(p_text, chat_id, chat_title, username, user_id, mes_date=mes_date)
                except Exception as e:
                    print(json.dumps(mes))
                    raise e


if __name__ == '__main__':
    args = sys.argv[1:]  # pass arguments if given and whatnot
    if len(args) > 0:
        main(args[0], None if len(args) == 1 else args[1])
    else:
        AssertionError("Specify path to the exported history")