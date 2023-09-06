from __future__ import print_function
import os.path
import pickle
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import logging
from threading import Semaphore

DEFAULT_DATE_FORMAT = "%d/%m/%y"
semaphore = Semaphore(1)


class GoogleSheet:
    SPREADSHEET_ID = "RAND_ID"
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    service = None

    def __init__(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'creds.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('sheets', 'v4', credentials=creds)

    def init_sheet(self):
        self._update_values('A1', [['date\student']])

    def _last_column(self):
        id_range = 'B3:Z3'

        id_values = self._get_values(id_range)
        column = chr(ord('A') + len(id_values[0]))
        return column

    def add_user(self, username, user_id):
        name_range = 'B1:Z1'
        id_range = 'B3:Z3'

        id_values = next(iter(self._get_values(id_range)), [])

        if str(user_id) not in id_values:
            next_column = chr(ord('B') + len(id_values))

            self._update_values(next_column + '1', [[username]])
            self._update_values(next_column + '2', [['=countif({c}4:{c}1000, "=-")/counta({c}4:{c}1000)'
                                .format(c=next_column)]])
            self._update_values(next_column + '3', [[user_id]])
            logging.info("User '%s' was successfully added to sheet" % username)
        else:
            logging.info("User '%s' was already added to sheet" % username)

    def insert_planner(self, user_id, pdate, text):
        assert user_id
        assert pdate
        assert text

        date_range = 'A4:A1000'
        user_id_range = 'B3:Z3'

        user_id_values = self._get_values(user_id_range)[0]

        existing_dates = next(iter(self._get_values(date_range)), [])
        last_row = 3 + len(existing_dates)

        dates = [pdate]
        first_exist_date = last_exist_date = None
        if len(existing_dates) > 0:
            first_exist_date = datetime.strptime(existing_dates[0], DEFAULT_DATE_FORMAT)
            last_exist_date = datetime.strptime(existing_dates[-1], DEFAULT_DATE_FORMAT)

            dates.append(first_exist_date)
            dates.append(last_exist_date)

        dates.sort()
        start_day = dates[0]
        end_day = dates[-1]

        if len(existing_dates) > 0:
            if start_day < first_exist_date:
                delta = first_exist_date - start_day
                self._insert_rows_before(delta.days, start_day)

        rows_after = 0
        if len(existing_dates) == 0:
            delta = end_day - start_day + timedelta(days=1)
            rows_after = delta.days
        elif len(existing_dates) > 0:
            delta = end_day - last_exist_date
            rows_after = delta.days
        if rows_after:
            self._insert_rows_after(last_row+1, rows_after, last_exist_date)

        delta = pdate - start_day
        planner_row = str(4 + delta.days)
        planner_column = chr(ord("B") + user_id_values.index(str(user_id)))
        old_text = next(iter(self._get_values(planner_column + planner_row)), None)
        if old_text is not None:
            new_text = "\n\n".join([old_text[0], text])
        else:
            new_text = text
        self._update_values(planner_column+planner_row, [[new_text]], raw=True)

    def _insert_rows_before(self, number_of_rows, start_day):
        last_column = self._last_column()
        number_of_columns = ord(last_column) - ord("A")
        insert_range = "A4:%s1000" % last_column
        existing_values = self._get_values(insert_range)
        for row in existing_values:
            row.extend(['']*(number_of_columns + 1 - len(row)))
            print("hm")
        new_dates = []
        for i in range(number_of_rows):
            temp_date = start_day + timedelta(days=i)
            new_dates.append([temp_date.strftime(DEFAULT_DATE_FORMAT)] + [''] * number_of_columns)
        new_values = new_dates + existing_values
        self._update_values(insert_range, new_values)

    def _insert_rows_after(self, start_row, number_of_rows, start_day):
        insert_range = "A%s:A1000" % start_row
        new_dates = []
        for i in range(number_of_rows):
            d = start_day + timedelta(days=i+1)
            new_dates.append([d.strftime(DEFAULT_DATE_FORMAT)])
        self._update_values(insert_range, new_dates)
        return

    def _update_values(self, range_, values, col=None, raw=False):
        body = {'values': values}
        if col is not None:
            range_ = range_[:1] + str(col) + range_[1:]

        semaphore.acquire()
        self.service.spreadsheets().values().update(
            spreadsheetId=self.SPREADSHEET_ID,
            range=range_,
            valueInputOption='RAW' if raw else 'USER_ENTERED',
            body=body
        ).execute()
        semaphore.release()

    def _get_values(self, range_):
        semaphore.acquire()
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.SPREADSHEET_ID,
            range=range_
        ).execute()
        values = result.get('values', [])
        semaphore.release()
        return values
