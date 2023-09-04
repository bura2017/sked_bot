from __future__ import print_function
import os.path
import pickle
import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dateutil.parser import parse
import re


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

    def add_username(self, username):
        name_range = 'B2:Z2'
        name_values = self.service.spreadsheets().values().get(
            spreadsheetId=self.SPREADSHEET_ID,
            range=name_range
        ).execute().get('values', [])

        if len(name_values) > 0:
            next_column = chr(ord('B') + len(name_values[0]))
        else:
            next_column = 'B'

        self._update_values(next_column + '2', [[username]])

    def add_id(self, user_id):
        name_range = 'B3:Z3'

        name_values = self.service.spreadsheets().values().get(
            spreadsheetId=self.SPREADSHEET_ID,
            range=name_range
        ).execute().get('values', [])

        if len(name_values) > 0:
            next_column = chr(ord('B') + len(name_values[0]))
        else:
            next_column = 'B'

        self._update_values(next_column + '3', [[user_id]])

    def _update_values(self, range_, values, col=None):
        body = {'values': values}
        if col is not None:
            range_ = range_[:1] + str(col) + range_[1:]
        self.service.spreadsheets().values().update(
            spreadsheetId=self.SPREADSHEET_ID,
            range=range_,
            valueInputOption='RAW',
            body=body
        ).execute()

    def find_and_write_name(self, name_to_find, text_to_put):
        date_range = 'A5:A'

        existing_dates = self.service.spreadsheets().values().get(
            spreadsheetId=self.SPREADSHEET_ID,
            range=date_range
        ).execute().get('values', [])

        existing_dates = [parse(date[0]).date() for date in existing_dates if date and date[0]]
        today = datetime.date.today()



        date_string = re.search(r'\b\d{1,2}\.\d{1,2}\.\d{2}\b', text_to_put)
        if date_string:
            parsed_date = parse(date_string.group(), dayfirst=True).date()
        else:
            parsed_date = today

        if parsed_date in existing_dates:
            return

        next_row = (len(existing_dates) * 2) + 5


        cell_to_write = f'A{next_row}'
        self.service.spreadsheets().values().update(
            spreadsheetId=self.SPREADSHEET_ID,
            range=cell_to_write,
            valueInputOption='RAW',
            body={'values': [[parsed_date.strftime('%Y-%m-%d')]]}
        ).execute()


    def put_text(self, name, text):
        today = datetime.date.today()
        date_string = re.search(r'\b\d{1,2}\.\d{1,2}\.\d{2}\b', text)

        if date_string:
            parsed_date = parse(date_string.group(), dayfirst=True).date()
        else:
            parsed_date = today

        names_range = 'B2:Z2'
        result = self.service.spreadsheets().values().get(spreadsheetId=self.SPREADSHEET_ID,
                                                          range=names_range).execute()
        names = result.get('values', [])
        column_index = None
        for i, col_name in enumerate(names[0]):
            if col_name == name:
                column_index = i + 2
                break

        if column_index is not None:

            date_range = 'A:A'
            result = self.service.spreadsheets().values().get(spreadsheetId=self.SPREADSHEET_ID,
                                                              range=date_range).execute()
            dates = result.get('values', [])
            row_index = None
            for i, date in enumerate(dates):
                if len(date) > 0 and isinstance(date[0], str):
                    date_value = parse(date[0]).date()
                    if date_value == parsed_date:
                        row_index = i + 1
                        break

            if row_index is not None:

                cell_range = f"{chr(column_index + 64)}{row_index}"

                value_range_body = {
                    'values': [[text]]
                }
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.SPREADSHEET_ID,
                    range=cell_range,
                    valueInputOption='RAW',
                    body=value_range_body
                ).execute()
                print(f"Text '{text}' placed at cell {cell_range}.")
            else:
                print(f"No matching date found for {parsed_date}. Text not placed.")
        else:
            print(f"No matching name found for {name}. Text not placed.")

    def put_answer(self, name, text_to_find, text):
        names_range = 'B2:Z2'
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.SPREADSHEET_ID,
            range=names_range
        ).execute()
        names = result.get('values', [])

        column_index = None
        for i, col_name in enumerate(names[0]):
            if col_name == name:
                column_index = i + 2
                break

        if column_index is not None:
            text_range = f'{chr(column_index + 64)}3:Z'
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.SPREADSHEET_ID,
                range=text_range
            ).execute()
            texts = result.get('values', [])

            row_index = None
            for i, row in enumerate(texts):
                if len(row) > 0 and row[0] == text_to_find:
                    row_index = i + 3
                    break

            if row_index is not None:
                cell_range = f'{chr(column_index + 64)}{row_index + 1}'
                value_range_body = {
                    'values': [[text]]
                }
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.SPREADSHEET_ID,
                    range=cell_range,
                    valueInputOption='RAW',
                    body=value_range_body
                ).execute()
                print(f"Text '{text}' placed after '{text_to_find}' for {name}.")
            else:
                print(f"No matching text '{text_to_find}' found for {name}. Text not placed.")
        else:
            print(f"No matching name found for {name}. Text not placed.")

    def _get_values(self, range_):
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.SPREADSHEET_ID,
            range=range_
        ).execute()
        values = result.get('values', [])
        return values

    def _insert_blank_row(self, row_number):
        body = {
            'requests': [
                {
                    'insertDimension': {
                        'range': {
                            'sheetId': 0,  # Assuming the sheet ID is 0
                            'dimension': 'ROWS',
                            'startIndex': row_number - 1,
                            'endIndex': row_number
                        },
                        'inheritFromBefore': False
                    }
                }
            ]
        }

        self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.SPREADSHEET_ID,
            body=body
        ).execute()
