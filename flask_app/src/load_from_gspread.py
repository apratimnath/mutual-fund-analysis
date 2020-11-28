'''
Created on Nov 28, 2020

@author: apratim
'''
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import os
import json


sheet = None

def get_credential_and_connect():
    global sheet
    # Defining the scope of the OAuth Authentication
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
             
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
            creds = ServiceAccountCredentials.from_json_keyfile_name("../../secret_config/google_credentials.json", scope)
            # Connecting to the Google Spreadsheet Client
            client = gspread.authorize(creds)
            
        else: 
            cred_data = json.loads(json_str)            
            cred_data['private_key'] = cred_data['private_key'].replace('\\n', '\n')
            creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_data, scope)
            # Connecting to the Google Spreadsheet Client
            client = gspread.authorize(creds)
        
        # Getting the spreadsheet
        sheet = client.open("Daily_MF_Returns").sheet1
        
        return sheet.get_all_records()
    except:
        return None
    
def update_row(value, total_rows):
    try:
        sheet.insert_row(value, total_rows, 'RAW')
    except:
        raise Exception
        
