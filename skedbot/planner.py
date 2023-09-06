import re
from datetime import datetime


class Planner(object):
    def __init__(self, text):
        self._text = text

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
        if len(splitted) > 1:
            try:
                self.day = datetime.strptime(splitted[1], "%d/%m/%y")
            except ValueError:
                try:
                    self.day = datetime.strptime(splitted[1], "%d.%m.%y")
                except ValueError:
                    self.day = None
        else:
            self.day = datetime.now()
