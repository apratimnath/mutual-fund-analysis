'''
Created on Nov 29, 2020

@author: apratim
'''

'''
This file is intended to auto-update the data to the base spreadsheet

1. Fetch the base spreadsheet as list
2. Convert the list into DataFrame
3. Repeat the cleaning process
4. Fetch the NAV spreadsheet as list
5. Convert the spreadsheet into DataFrame
6. Insert/Update the latest changes
'''

import numpy as np
import warnings
import pandas as pd
import load_from_gspread
from datetime import date
import send_mail
warnings.filterwarnings('ignore')

# Base list
base_data_list = None

# Frames
base_data_frame = None
nav_data_frame = None

# List of latest Changes
current_values_list = None
current_investment_list = None


# Load the base data frame
def driver_function():
    is_success = load_base_spreadsheet()

    if(is_success):
        is_success = check_and_update_nav_frame()
        
        if(is_success): 
            is_success = load_nav_data_frame()
            
            if(is_success):
                is_success = clean_nav_frame()
                
                if(is_success):
                    is_success = update_data()
                    
                    if(is_success):
                        return True
    return False


def load_base_spreadsheet():
    global base_data_frame
    global base_data_list
    try:
        base_data_list = load_from_gspread.get_credential_and_connect()

        base_data_frame = pd.DataFrame(base_data_list)
        do_data_cleaning()

        return True
    except Exception as e:
        print(str(e))

        return False


def check_and_update_nav_frame():
    global nav_data_frame
    try:
        nav_data_list = load_from_gspread.load_data_from_nav_sheet()

        nav_data_frame = pd.DataFrame(nav_data_list)        
        date_of_update = list(map(lambda x:str(x[7]), nav_data_frame.values))
        last_update_month_date = list(map(lambda x:str(x[9]), nav_data_frame.values))
        
        date_list = []
        
        for value in date_of_update:
            each_value_list = value.split(",")            
            date_list.append(list(map(int, list(map(lambda x: x.strip(), each_value_list)))))
        
        current_date = int(date.today().strftime("%d"))
        current_month = date.today().strftime("%d-%b")
        
        # No of days required for processing, though that is tentative
        processing_days = 3
        
        # Row Number
        row_number = 2
        
        current_values_list = nav_data_frame.values
        
        for index in range(0, len(date_list)):
            dates_for_current_mf = date_list[index]
            is_renewed = False
            
            # Check the if SIP is renewed
            for each_date in dates_for_current_mf:
                if(each_date + processing_days == current_date and last_update_month_date[index] != current_month):
                    is_renewed = True
                    break
            
            if(is_renewed):
                current_values_list[index][4] += round(current_values_list[index][6] / current_values_list[index][3], 3)
                current_values_list[index][5] = current_values_list[index][3] * current_values_list[index][4]
                current_values_list[index][8] += current_values_list[index][6]
                current_values_list[index][9] = current_month
                
                load_from_gspread.update_master_cell(current_values_list[index][4], row_number, 5)
                load_from_gspread.update_master_cell(current_values_list[index][5], row_number, 6)
                load_from_gspread.update_master_cell(current_values_list[index][8], row_number, 9)
                load_from_gspread.update_master_cell(current_values_list[index][9], row_number, 10)
                
                print("Updated Row - {} in the Master Sheet".format(row_number))
                
            else:
                print("No update required for Row - {} in the Master Sheet".format(row_number))
                
            row_number += 1                 
            
        return True
    except Exception as e:
        print(str(e))
        
        return False


# Load the NAV Data Frame
def load_nav_data_frame():
    global nav_data_frame
    try:
        nav_data_list = load_from_gspread.load_data_from_nav_sheet()

        nav_data_frame = pd.DataFrame(nav_data_list)

        return True
    except Exception as e:
        print(str(e))

        return False


# Cleanup NAV Data Frame
def clean_nav_frame():
    global nav_data_frame
    global current_values_list
    global current_investment_list

    try:
        nav_data_frame = nav_data_frame.drop(
            ['MF Code', 'Latest NAV', 'Units', 'Renew Amount', 'Renew Date', 'Last Update'], axis=1)

        # Round the current values
        nav_data_frame['Current Value'] = nav_data_frame['Current Value'].apply(
            lambda x: round(x, 2))

        current_values_list = list(map(lambda x: x[2], nav_data_frame.values))
        current_investment_list = list(map(lambda x: x[3], nav_data_frame.values))

        return True
    except Exception as e:
        print(str(e))

        return False


# Insert/Update the latest data into base_data_frame
def update_data():
    global base_data_list
    global base_data_frame
    global current_values_list
    global nav_data_frame
    global current_investment_list

    try:
        is_update = False
        
        current_length = len(base_data_list)
        
        # Getting the last date
        last_date = base_data_frame.values[current_length - 1][0]
        
        # Getting all the rows corresponding to the last date
        data_filtered = base_data_frame.loc[base_data_frame['Date'] == last_date]
        
        # Get the fund names list
        fund_names = list(map(lambda x: x[1], data_filtered.values))
        
        fund_names_nav_sheet = list(map(lambda x: x[0], nav_data_frame.values))
        
        # Check whether the NAV Frame has the same data for all the names from original Data (All MFs are registered)
        if(fund_names != fund_names_nav_sheet):
            return False
        
        # Get the current date in the same format
        current_date = date.today().strftime("%m/%d/%Y")
        
        if(current_date == last_date):
            is_update = True
            
        # Get the starting column and row number
        # 1 row added to each because of the heading row
        column_number = 5
        start_row_number = current_length - len(current_values_list) + 2
        end_row_number = current_length + 1

        # If Update
        if(is_update):
            # Validate whether update is actually required
            is_update_required = False
            
            current_data_list = data_filtered.values
            
            for index in range(0, len(current_values_list)):
                if(current_values_list[index] != current_data_list[index][4]):
                    is_update_required = True
                    break
            
            if(is_update_required): 
                for index in range(0, len(current_values_list)):
                    # Update the principal
                    load_from_gspread.update_nav_cell(current_investment_list[index], start_row_number, column_number - 1)
                    
                    # Update the current amount
                    load_from_gspread.update_nav_cell(current_values_list[index], start_row_number, column_number)
                    
                    # Update the change
                    load_from_gspread.update_nav_cell(round(current_values_list[index] - current_investment_list[index], 2), start_row_number, column_number + 1)
                    
                    print(
                        "Updated Row - {}".format(start_row_number))
                        
                    start_row_number += 1
                    
            else:
                print("No update required")
                
        # If Insert
        else:
            current_data_list = data_filtered.values
            
            for index in range(0, len(current_values_list)):
                current_data_list[index][0] = current_date
                current_data_list[index][3] = current_investment_list[index]
                current_data_list[index][4] = current_values_list[index]
                current_data_list[index][5] = round(
                    current_data_list[index][4] - current_data_list[index][3], 2)
                    
            for each_data in current_data_list:
                end_row_number += 1
                each_data_list = each_data.tolist()
                load_from_gspread.insert_nav_row(
                    each_data_list, end_row_number)
                print("Inserted Row - {}".format(end_row_number))

        return True
    except Exception as e:
        print(str(e))

        return False


# Clean the data
def do_data_cleaning():
    global base_data_frame
    base_data_frame.replace([''], 'Unknown', inplace=True)
