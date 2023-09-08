import re
from datetime import datetime


class Planner(object):
    continue_char = '👆🏽'

    def __init__(self, text, today=None):
        self._text = text
        if today is None:
            today = datetime.now()

        lines = text.split('\n')
        self._header = lines[0]
        self.body = []
        for i in range(1, len(lines)):
            if lines[i]:
                self.body = lines[i:]
                break

        splitted = re.split(r'\s|-', self._header)
        if re.match(r"^#\w+$", splitted[0]):
            self.tag = splitted[0]
        self.day = today
        self.start_day = None
        self.end_day = None
        for i in range(1, len(splitted)):
            available_formats = ["%d/%m/%y", "%d/%m/%Y", "%d.%m.%y", "%d.%m.%Y", "%d.%m"]
            for format in available_formats:
                try:
                    if self.start_day is None:
                        self.day = datetime.strptime(splitted[i], format)
                        self.start_day = self.day
                    else:
                        self.end_day = datetime.strptime(splitted[i], format)

                except ValueError:
                    pass

