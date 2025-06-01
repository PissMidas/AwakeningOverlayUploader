from watchdog.observers import Observer
from observer import LogObserver
from google_sheets_uploader import initialize_sheets_service
import os
import sys
import time
import pygetwindow
from dotenv import load_dotenv

#pyinstaller --noconfirm AwakeningOverlayUploader.spec


SPREADSHEET_ID= 'test'
SHEET_NAME= 'test'
TEST_LOG_FLAG=False
TEST_LOG_FILEPATH="some filepath"

def is_omega_strikers_window_open():
    game_title = "OmegaStrikers"
    windows = pygetwindow.getAllWindows()
    for window in windows:
        if game_title in window.title:
            return True
    print("Omega strikers is not running. closing app.")
    return False  # Set to True for testing; change to False for actual use

def loadfromenv():
    load_dotenv()

    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    SHEET_NAME = os.getenv("SHEET_NAME")
    #SPREADSHEET_ID = '1HbF_0IPMC_fZmMwPHXvmyhIlY5JFu1S2lp7Y3AwdDyU'
    #SHEET_NAME = 'Sheet1'
    TEST_LOG_FLAG = os.getenv('TEST_LOG_FLAG', 'False').lower() == 'true' # this stores a boolean!

    if (TEST_LOG_FLAG is True):
        #then we read the .env file's value for filepath.
        TEST_LOG_FILEPATH = os.getenv('TEST_LOG_FILEPATH')
    else:
        #check if there is a window called omega strikers.
        TEST_LOG_FILEPATH = os.path.join(os.getenv('LOCALAPPDATA'), 'OmegaStrikers', 'Saved', 'Logs', 'OmegaStrikers.log')

    return SPREADSHEET_ID, SHEET_NAME, TEST_LOG_FLAG, TEST_LOG_FILEPATH

def main():

    # Initialize Google Sheets uploader
    SPREADSHEET_ID, SHEET_NAME, TEST_LOG_FLAG, TEST_LOG_FILEPATH = loadfromenv()

    #if TEST_LOG_FLAG is false, then we need to check if
    if(TEST_LOG_FLAG is False):
        #check if omega strikers is open.
        if(is_omega_strikers_window_open() is False):
                print('Omega Strikers is not open. Exiting App in 10 seconds.')
                time.sleep(10)
                os._exit(0)

    google_service = initialize_sheets_service()

    #observer = Observer()
    # Start log monitoring
    log_observer = LogObserver(TEST_LOG_FILEPATH, google_service, SPREADSHEET_ID, SHEET_NAME)
    log_observer.start_monitoring()

    #if its a test log then we need to append something to the log so that it triggers the monitoring.
    if(TEST_LOG_FLAG is True):
        try:
            with open(TEST_LOG_FILEPATH, 'a') as log_file:  # 'a' mode opens the file for appending
                log_file.write('.\n')  # Write the dot and add a newline for readability
        except Exception as e:
            print(f"An error occurred while writing to log file: {e}")
    # Additional error handling (retry logic, logging, etc.)
if __name__ == "__main__":
    main()
