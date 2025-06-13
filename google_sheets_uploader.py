from __future__ import print_function
import os
import re
import time
import sys
import webbrowser
import requests
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

# Define the Google Sheets API scope
SCOPES = ["https://www.googleapis.com/auth/drive.file"]



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

    client_config = {
        "installed": {
            "client_id": "304904465571-0bcd8ru3v1r25vjcjo5l435bop0ql2l6.apps.googleusercontent.com",
            "project_id": "os-awakenings-overlay-app",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "NULL", #insert your secret here.
            "redirect_uris": ["http://localhost"]
        }
    }

    # Load existing token if it exists
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid creds, run the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for next time
        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())

    return creds


def initialize_sheets_service(spreadsheet_id=None):
    creds = get_credentials()

    service = build('sheets', 'v4', credentials=creds)

    if spreadsheet_id:
        try:
            # Try to access the spreadsheet metadata
            metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            print(f"✅ Successfully accessed spreadsheet: {metadata.get('properties', {}).get('title', 'Untitled')}")
        except HttpError as e:
            status = e.resp.status
            link = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
            print(f"\n🚫 Failed to access spreadsheet: {spreadsheet_id}")

            if status == 403:
                print("🔒 Permission denied.")
                print("👉 Make sure the Google account you used to log in with the app has access to this spreadsheet.")
                print(f"🔗 Open the spreadsheet link and click 'Share', then add your account email:\n{link}")
            elif status == 404:
                print("❌ Spreadsheet not found. The ID may be incorrect or the file may have been deleted.")
                print(f"🔗 Attempted to open:\n{link}")
            else:
                print(f"Unexpected error ({status}): {e}")

            # Open link in browser to help the user resolve it
            try:
                webbrowser.open(link)
            except Exception:
                print("⚠️ Unable to open browser automatically. Please open the link manually.")

            input("\n🔁 After you've shared access, press Enter to exit...")
            sys.exit(1)

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
