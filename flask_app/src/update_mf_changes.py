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

# Load the base data frame
def driver_function():
    is_success = load_base_spreadsheet()

    if(is_success):
        is_success = load_nav_data_frame()

        if(is_success):
            is_success = clean_nav_frame()

            if(is_success):
                is_success = update_data()

                if(is_success):
                    return True

                return False
            return False
        return False
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

    try:
        nav_data_frame = nav_data_frame.drop(
            ['MF Code', 'Latest NAV', 'Units'], axis=1)

        # Round the current values
        nav_data_frame['Current Value'] = nav_data_frame['Current Value'].apply(
            lambda x: round(x, 2))

        current_values_list = list(map(lambda x: x[2], nav_data_frame.values))

        return True
    except Exception as e:
        print(str(e))

        return False

# Insert/Update the latest data into base_data_frame
def update_data():
    global base_data_list
    global base_data_frame
    global current_values_list

    try:
        is_update = False

        current_length = len(base_data_list)

        # Getting the last date
        last_date = base_data_frame.values[current_length - 1][0]

        # Getting all the rows corresponding to the last date
        data_filtered = base_data_frame.loc[base_data_frame['Date'] == last_date]

        # Get the fund names list
        fund_names = list(map(lambda x: x[1], data_filtered.values))

        # Get the current date in the same format
        current_date = date.today().strftime("%m/%d/%Y")

        if(current_date == last_date):
            is_update = True

        # Get the starting column and row number
        column_number = 5
        start_row_number = current_length - len(current_values_list) + 2
        end_row_number = current_length + 1

        # If Update
        if(is_update):
            for value in current_values_list:
                load_from_gspread.update_nav_cell(
                    value, start_row_number, column_number)
                print(
                    "Updated Row - {} and Column - {}".format(start_row_number, column_number))

                start_row_number += 1

        # If Insert
        else:
            current_data_list = data_filtered.values

            for index in range(0, len(current_values_list)):
                current_data_list[index][0] = current_date
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
