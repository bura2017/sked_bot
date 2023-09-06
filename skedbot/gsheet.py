from __future__ import print_function
import os.path
import pickle
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import re
import logging

DEFAULT_DATE_FORMAT = "%d/%m/%y"


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
            self._insert_rows_after(last_row+1, rows_after, end_day)

        delta = pdate - start_day
        planner_row = str(4 + delta.days)
        planner_column = chr(ord("B") + user_id_values.index(str(user_id)))
        old_text = next(iter(self._get_values(planner_column + planner_row)), None)
        if old_text is not None:
            new_text = "\n\n".join([old_text, text])
        else:
            new_text = text
        self._update_values(planner_column+planner_row, [[new_text]])

    def _insert_rows_before(self, number_of_rows, start_day):
        last_column = self._last_column()
        insert_range = "A4:%s1000" % last_column
        existing_values = self._get_values(insert_range)
        new_dates = []
        for i in range(number_of_rows):
            new_dates.append([start_day + timedelta(days=i)])
        new_values = new_dates + existing_values
        self._update_values(insert_range, new_values)

    def _insert_rows_after(self, start_row, number_of_rows, start_day):
        insert_range = "A%s:A1000" % start_row
        new_dates = []
        for i in range(number_of_rows):
            d = start_day + timedelta(days=i)
            new_dates.append(d.strftime(DEFAULT_DATE_FORMAT))
        self._update_values(insert_range, [new_dates])

    def _update_values(self, range_, values, col=None):
        body = {'values': values}
        if col is not None:
            range_ = range_[:1] + str(col) + range_[1:]

        self.service.spreadsheets().values().update(
            spreadsheetId=self.SPREADSHEET_ID,
            range=range_,
            # valueInputOption='RAW',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

    def _get_values(self, range_):
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.SPREADSHEET_ID,
            range=range_
        ).execute()
        values = result.get('values', [])
        return values

    # def find_and_write_name(self, name_to_find, text_to_put):
    #     date_range = 'A5:A'
    #     existing_dates = self.service.spreadsheets().values().get(
    #         spreadsheetId=self.SPREADSHEET_ID,
    #         range=date_range
    #     ).execute().get('values', [])
    #
    #     existing_dates = self.service.spreadsheets().values().get(
    #         spreadsheetId=self.SPREADSHEET_ID,
    #         range=date_range
    #     ).execute().get('values', [])
    #
    #     existing_dates = [parse(date[0]).date() for date in existing_dates if date and date[0]]
    #     today = datetime.date.today()
    #
    #     date_string = re.search(r'\b\d{1,2}\.\d{1,2}\.\d{2}\b', text_to_put)
    #     if date_string:
    #         parsed_date = parse(date_string.group(), dayfirst=True).date()
    #     else:
    #         parsed_date = today
    #
    #     if parsed_date in existing_dates:
    #         return
    #
    #     next_row = (len(existing_dates) * 2) + 5
    #
    #
    #     cell_to_write = f'A{next_row}'
    #     self.service.spreadsheets().values().update(
    #         spreadsheetId=self.SPREADSHEET_ID,
    #         range=cell_to_write,
    #         valueInputOption='RAW',
    #         body={'values': [[parsed_date.strftime('%Y-%m-%d')]]}
    #     ).execute()

    # def put_text(self, name, text):
    #     today = datetime.date.today()
    #     date_string = re.search(r'\b\d{1,2}\.\d{1,2}\.\d{2}\b', text)
    #
    #     if date_string:
    #         parsed_date = parse(date_string.group(), dayfirst=True).date()
    #     else:
    #         parsed_date = today
    #
    #     names_range = 'B2:Z2'
    #     result = self.service.spreadsheets().values().get(spreadsheetId=self.SPREADSHEET_ID,
    #                                                       range=names_range).execute()
    #     names = result.get('values', [])
    #     column_index = None
    #     for i, col_name in enumerate(names[0]):
    #         if col_name == name:
    #             column_index = i + 2
    #             break
    #
    #     if column_index is not None:
    #
    #         date_range = 'A:A'
    #         result = self.service.spreadsheets().values().get(spreadsheetId=self.SPREADSHEET_ID,
    #                                                           range=date_range).execute()
    #         dates = result.get('values', [])
    #         row_index = None
    #         for i, date in enumerate(dates):
    #             if len(date) > 0 and isinstance(date[0], str):
    #                 # date_value = parse(date[0]).date()
    #                 # if date_value == parsed_date:
    #                     row_index = i + 1
    #                     break
    #
    #         if row_index is not None:
    #
    #             cell_range = f"{chr(column_index + 64)}{row_index}"
    #
    #             value_range_body = {
    #                 'values': [[text]]
    #             }
    #             self.service.spreadsheets().values().update(
    #                 spreadsheetId=self.SPREADSHEET_ID,
    #                 range=cell_range,
    #                 valueInputOption='RAW',
    #                 body=value_range_body
    #             ).execute()
    #             print(f"Text '{text}' placed at cell {cell_range}.")
    #         else:
    #             print(f"No matching date found for {parsed_date}. Text not placed.")
    #     else:
    #         print(f"No matching name found for {name}. Text not placed.")

    # def put_answer(self, name, text_to_find, text):
    #     names_range = 'B2:Z2'
    #     result = self.service.spreadsheets().values().get(
    #         spreadsheetId=self.SPREADSHEET_ID,
    #         range=names_range
    #     ).execute()
    #     names = result.get('values', [])
    #
    #     column_index = None
    #     for i, col_name in enumerate(names[0]):
    #         if col_name == name:
    #             column_index = i + 2
    #             break
    #
    #     if column_index is not None:
    #         text_range = f'{chr(column_index + 64)}3:Z'
    #         result = self.service.spreadsheets().values().get(
    #             spreadsheetId=self.SPREADSHEET_ID,
    #             range=text_range
    #         ).execute()
    #         texts = result.get('values', [])
    #
    #         row_index = None
    #         for i, row in enumerate(texts):
    #             if len(row) > 0 and row[0] == text_to_find:
    #                 row_index = i + 3
    #                 break
    #
    #         if row_index is not None:
    #             cell_range = f'{chr(column_index + 64)}{row_index + 1}'
    #             value_range_body = {
    #                 'values': [[text]]
    #             }
    #             self.service.spreadsheets().values().update(
    #                 spreadsheetId=self.SPREADSHEET_ID,
    #                 range=cell_range,
    #                 valueInputOption='RAW',
    #                 body=value_range_body
    #             ).execute()
    #             print(f"Text '{text}' placed after '{text_to_find}' for {name}.")
    #         else:
    #             print(f"No matching text '{text_to_find}' found for {name}. Text not placed.")
    #     else:
    #         print(f"No matching name found for {name}. Text not placed.")

    # def _insert_blank_row(self, row_number):
    #     body = {
    #         'requests': [
    #             {
    #                 'insertDimension': {
    #                     'range': {
    #                         'sheetId': 0,  # Assuming the sheet ID is 0
    #                         'dimension': 'ROWS',
    #                         'startIndex': row_number - 1,
    #                         'endIndex': row_number
    #                     },
    #                     'inheritFromBefore': False
    #                 }
    #             }
    #         ]
    #     }
    #
    #     self.service.spreadsheets().batchUpdate(
    #         spreadsheetId=self.SPREADSHEET_ID,
    #         body=body
    #     ).execute()
