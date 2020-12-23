'''
Created on Nov 28, 2020

@author: apratim
'''
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import os
import json
import warnings

warnings.filterwarnings('ignore')


sheet = None
money_manager_sheet = None
nav_sheet = None


def get_credential_and_connect():
    global sheet
    # Defining the scope of the OAuth Authentication
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    # Getting the credentials

    '''
    There are two methods defined to get the credentials
    
    If in local, get from the JSON file.
    If deployed on Heroku, get from the env.
    '''
    try:
        # Trying with Env
        json_str = os.environ.get('GOOGLE_CREDENTIALS')
        is_local = False

        if(not json_str or len(json_str) == 0):
            is_local = True

        print("The state of application is Local", end=" ")
        print(is_local)

        if(is_local):
            print(os.getcwd())
            file_path = os.getcwd() + "/src/secret_config/google_credentials.json"
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                file_path, scope)
            # Connecting to the Google Spreadsheet Client
            client = gspread.authorize(creds)

        else:
            cred_data = json.loads(json_str)
            cred_data['private_key'] = cred_data['private_key'].replace(
                '\\n', '\n')
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                cred_data, scope)
            # Connecting to the Google Spreadsheet Client
            client = gspread.authorize(creds)

        # Getting the spreadsheet
        sheet = client.open("Daily_MF_Returns").sheet1

        return sheet.get_all_records()
    except Exception as e:
        print(str(e))

        return None


def update_row(value, total_rows):
    try:
        sheet.insert_row(value, total_rows, 'RAW')
    except:
        raise Exception


'''
Function to load the data from the gspread contatining data from -
Money Manager

Will load and return the sheet
'''


def load_data_from_money_manager():
    global money_manager_sheet
    # Defining the scope of the OAuth Authentication
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    # Getting the credentials

    '''
    There are two methods defined to get the credentials
    
    If in local, get from the JSON file.
    If deployed on Heroku, get from the env.
    '''
    try:
        # Trying with Env
        json_str = os.environ.get('GOOGLE_CREDENTIALS')
        is_local = False

        if(not json_str or len(json_str) == 0):
            is_local = True

        print("The state of application is Local", end=" ")
        print(is_local)

        if(is_local):
            print(os.getcwd())
            file_path = os.getcwd() + "/src/secret_config/google_credentials.json"
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                file_path, scope)
            # Connecting to the Google Spreadsheet Client
            client = gspread.authorize(creds)

        else:
            cred_data = json.loads(json_str)
            cred_data['private_key'] = cred_data['private_key'].replace(
                '\\n', '\n')
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                cred_data, scope)
            # Connecting to the Google Spreadsheet Client
            client = gspread.authorize(creds)

        # Getting the spreadsheet
        money_manager_sheet = client.open("Personal_Expenditure").sheet1

        return money_manager_sheet.get_all_records()
    except Exception as e:
        print(str(e))

        return None


'''
Function to load the data from the gspread contatining data from -
Google NAV Change (Auto updated by Google Finance)

Will load and return the sheet
'''


def load_data_from_nav_sheet():
    global nav_sheet
    # Defining the scope of the OAuth Authentication
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    # Getting the credentials

    '''
    There are two methods defined to get the credentials
    
    If in local, get from the JSON file.
    If deployed on Heroku, get from the env.
    '''
    try:
        # Trying with Env
        json_str = os.environ.get('GOOGLE_CREDENTIALS')
        is_local = False

        if(not json_str or len(json_str) == 0):
            is_local = True

        print("The state of application is Local", end=" ")
        print(is_local)

        if(is_local):
            print(os.getcwd())
            file_path = os.getcwd() + "/src/secret_config/google_credentials.json"
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                file_path, scope)
            # Connecting to the Google Spreadsheet Client
            client = gspread.authorize(creds)

        else:
            cred_data = json.loads(json_str)
            cred_data['private_key'] = cred_data['private_key'].replace(
                '\\n', '\n')
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                cred_data, scope)
            # Connecting to the Google Spreadsheet Client
            client = gspread.authorize(creds)

        # Getting the spreadsheet
        nav_sheet = client.open("Daily_NAV_Change").sheet1

        return nav_sheet.get_all_records()
    except Exception as e:
        print(str(e))

        return None


def insert_nav_row(value, row_number):
    try:
        sheet.insert_row(value, row_number, 'RAW')
    except:
        raise Exception


def update_nav_cell(value, row_number, column_number):
    try:
        sheet.update_cell(row_number, column_number, value)
    except:
        raise Exception
