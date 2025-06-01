from __future__ import print_function
import os
import re
import time
import sys

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

# Define the Google Sheets API scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def resourcePath(relativePath):
    # Get absolute path to resource, works for dev and for PyInstaller
    try:
        basePath = sys._MEIPASS
    except Exception:
        basePath = os.path.abspath(".")
    return os.path.join(basePath, relativePath)

def get_token_path():
    # Store token.json in a writable location (user's home directory)
    home = os.path.expanduser("~")
    token_dir = os.path.join(home, ".awakening_overlay_uploader")
    os.makedirs(token_dir, exist_ok=True)
    return os.path.join(token_dir, "token.json")

def get_credentials():
    creds = None
    token_path = get_token_path()
    client_secret_path = resourcePath('credentials/client_secret.json')

    # Load credentials if they exist
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If credentials are invalid or don't exist, start OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())

    return creds

def initialize_sheets_service():
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)
    return service

def find_first_empty_row(service, spreadsheet_id, sheetstring='Sheet1'):
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=sheetstring).execute()
        values = result.get('values', [])
        return len(values) + 1 if values else 1
    except HttpError as e:
        print(f"Error finding empty row: {e}")
        return None

def append_column_as_values(service, spreadsheet_id, sheetstring, start_row, column_letter, data):
    if start_row:
        values = [[item] if not isinstance(item, list) else [' '.join(item)] for item in data]
        range_to_append = f'{sheetstring}!{column_letter}{start_row}'

        request = {
            'valueInputOption': 'USER_ENTERED',
            'data': [{'range': range_to_append, 'values': values}]
        }
        response = service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id, body=request).execute()
        print(f'Column {column_letter} data appended successfully.')
    else:
        print('No empty row found in the specified sheet.')

def append_2d_table_as_values(service, spreadsheet_id, sheetstring, start_row, data_2d):
    if start_row and data_2d:
        max_columns = max(len(row) for row in data_2d)
        data_2d_padded = [row + [''] * (max_columns - len(row)) for row in data_2d]
        range_to_append = f'{sheetstring}!A{start_row}:{chr(ord("A") + max_columns - 1)}{start_row + len(data_2d) - 1}'

        request = {
            'valueInputOption': 'USER_ENTERED',
            'data': [{'range': range_to_append, 'values': data_2d_padded}]
        }

        retries = 3
        max_retries = 6
        backoff_factor = 2

        while retries < max_retries:
            try:
                response = service.spreadsheets().values().batchUpdate(
                    spreadsheetId=spreadsheet_id, body=request).execute()
                print('2D table data appended successfully.')
                return
            except HttpError as error:
                if error.resp.status == 429:
                    retries += 1
                    wait_time = backoff_factor ** retries
                    print(f'Rate limit exceeded. Retrying in {wait_time} seconds...')
                    time.sleep(wait_time)
                else:
                    raise error

        print('Max retries reached. Could not append data due to API rate limit.')
    else:
        print('No data or empty row found in the specified sheet.')

def main():
    service = initialize_sheets_service()
    spreadsheet_id = '1HbF_0IPMC_fZmMwPHXvmyhIlY5JFu1S2lp7Y3AwdDyU'
    first_empty_row = find_first_empty_row(service, spreadsheet_id, 'Sheet1')

    # Example usage
    # append_2d_table_as_values(service, spreadsheet_id, 'Sheet1', first_empty_row, [['Big Fish', 'Egoist', 'Super Surge']])
    # append_column_as_values(service, spreadsheet_id, 'Sheet1', first_empty_row, 'A', ['Big Fish', 'Egoist', 'Super Surge'])

if __name__ == '__main__':
    main()
