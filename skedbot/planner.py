import re
from datetime import datetime


class Planner(object):
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

        splitted = self._header.split()
        if re.match(r"^#\w+$", splitted[0]):
            self.tag = splitted[0]
        self.day = today
        if len(splitted) > 1:
            available_formats = ["%d/%m/%y", "%d/%m/%Y", "%d.%m.%y", "%d.%m.%Y", "%d.%m"]
            for format in available_formats:
                try:
                    self.day = datetime.strptime(splitted[1], format)
                    break
                except ValueError:
                    pass

