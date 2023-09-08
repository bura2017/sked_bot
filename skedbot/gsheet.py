from __future__ import print_function
import os.path
import pickle
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import logging
from threading import Semaphore

DEFAULT_DATE_FORMAT = "%d/%m/%Y"
semaphore = Semaphore(1)


class GoogleSheet:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    service = None

    def __init__(self, spreadsheet_id):
        self.spreadsheet_id = spreadsheet_id

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

        # INSERT ESSENTIALS
        self._update_values('A1', [['date\student']])
        self.user_id_range = 'B3:Z3'
        self.last_column = None
        # Update last_column value
        self.get_user_ids()

    def get_user_ids(self):
        id_values = next(iter(self._get_values(self.user_id_range)), [])
        self.last_column = chr(ord("A") + len(id_values))
        return id_values

    def add_user(self, username, user_id):
        id_values = self.get_user_ids()

        if str(user_id) not in id_values:
            next_column = chr(ord('B') + len(id_values))
            new_values = [[username],
                          ['=countif({c}4:{c}1000, "=-")/counta({c}4:{c}1000)'
                           .format(c=next_column)],
                          [user_id]]

            self._update_values('%s1:%s3' % (next_column, next_column), new_values)
            logging.info("User '%s' was successfully added to sheet" % username)
            return next_column
        else:
            logging.info("User '%s' was already added to sheet" % username)
            user_column = chr(ord('B') + id_values.index(str(user_id)))
            return user_column

    def insert_planner(self, user_id, p, user_column=None):
        assert user_id
        assert p

        if user_column is None:
            id_values = self.get_user_ids()
            user_column = chr(ord('B') + id_values.index(str(user_id)))

        date_range = 'A4:A1000'
        dates_from_sheet = self._get_values(date_range)
        existing_dates = [d[0] for d in dates_from_sheet]
        last_row = 3 + len(existing_dates)

        if p.end_day is None:
            dates = [p.day]
        else:
            dates = [p.start_day, p.end_day]

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

        pdate = p.start_day or p.day
        rows_after = 0
        if len(existing_dates) == 0:
            delta = end_day - start_day + timedelta(days=1)
            rows_after = delta.days
        elif len(existing_dates) > 0:
            delta = end_day - last_exist_date
            rows_after = delta.days
        if rows_after:
            insert_from = pdate if last_exist_date is None else last_exist_date+timedelta(days=1)
            self._insert_rows_after(last_row+1, rows_after, insert_from)

        delta = pdate - start_day
        planner_row = str(4 + delta.days)
        if p.end_day is None:
            extra_values_number = 0
            planner_range = user_column+planner_row
        else:
            pdays_delta = p.end_day-p.start_day
            extra_values_number = pdays_delta.days
            planner_range = "%s%s:%s%s" % (user_column, planner_row, user_column, int(planner_row)+pdays_delta.days)

        old_text_values = self._get_values(planner_range)
        new_text = "\n".join(p.body)
        planner_values = [[new_text]] + [[p.continue_char]] * extra_values_number

        for i, row in enumerate(old_text_values):
            if row:
                planner_values[i] = ["\n\n".join(row+planner_values[i])]

        self._update_values(planner_range, planner_values, raw=True)

    def _insert_rows_before(self, number_of_rows, start_day):
        number_of_columns = ord(self.last_column) - ord("A")
        insert_range = "A4:%s1000" % self.last_column
        existing_values = self._get_values(insert_range)
        for row in existing_values:
            row.extend(['']*(number_of_columns + 1 - len(row)))
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
            d = start_day + timedelta(days=i)
            new_dates.append([d.strftime(DEFAULT_DATE_FORMAT)])
        self._update_values(insert_range, new_dates)
        return

    def _update_values(self, range_, values, col=None, raw=False):
        body = {'values': values}
        if col is not None:
            range_ = range_[:1] + str(col) + range_[1:]

        semaphore.acquire()
        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_,
                valueInputOption='RAW' if raw else 'USER_ENTERED',
                body=body
            ).execute()
        finally:
            semaphore.release()

    def _get_values(self, range_):
        semaphore.acquire()
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_
            ).execute()
            values = result.get('values', [])
        finally:
            semaphore.release()
        return values
