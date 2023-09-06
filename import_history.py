import sys
import json
from skedbot import vars, db
from skedbot.main import handle_planner, search_for_planners
from datetime import datetime


def main(path):
    messages = []
    chat_title = '[unknown]'
    chat_id = '-944947277'
    with open(path, "r") as f:
        data = f.read()
        pdata = json.loads(data)
        chat_title = pdata.get('name', '[not specified]')
        messages = pdata.get('messages', [])

    for mes in messages:
        text = mes['text']
        # TODO
        username = mes['from']
        user_id = mes['from_id'].match(r"^user(.*)$").group(1)
        mes_date = datetime.strptime(mes['date'], "%Y-%m-%dT%H:%M:%s")
        keywords = db.get_keywords(user_id)
        planners = search_for_planners(text, keywords)
        handle_planner(text, chat_id, chat_title, username, user_id, mes_date=mes_date)


if __name__ == '__main__':
    args = sys.argv[1:]  # pass arguments if given and whatnot
    if len(args) > 0:
        main(args[0])
    else:
        AssertionError("Specify path to the exported history")