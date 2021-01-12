import warnings
import load_from_gspread
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import highcharts_converter

warnings.filterwarnings('ignore')

'''
This component is created to - 
1. Fetch data from gspread
2. Modify and do internal manipulations on the data
3. Data Clean up
4. Send the data to highcharts server for support
'''

# List to store the data from gspread
all_personal_finance_data = None

# All dataframes
base_data = None
expense_data = None
income_data = None


def get_the_data_from_gspread():
    global all_personal_finance_data
    global base_data

    # Load the data
    all_personal_finance_data = load_from_gspread.load_data_from_money_manager()

    if(all_personal_finance_data == None):
        return False

    # Convert the data to data frame
    base_data = pd.DataFrame(all_personal_finance_data)

    data_cleanup()
    drop_columns()
    rename_columns()
    add_columns()
    seperate_dataframes()

    return True


# Replace the empty values (all columns) with 'Unknown'
def data_cleanup():
    global base_data

    base_data.replace([''], 'Unknown', inplace=True)

# Drop the Memo column contating description


def drop_columns():
    global base_data

    base_data = base_data.drop(['Memo'], axis=1)


# Rename the columns based on proper formatting
def rename_columns():
    global base_data

    base_data.columns = ['date', 'type', 'category', 'amount']

# Add MMM-YYYY and Day of week columns


def add_columns():
    global base_data

    base_data['month_year'] = base_data['date'].apply(month_year)
    base_data['day_of_week'] = base_data['date'].apply(day_of_week)


# Adding the Month-Year Column
def month_year(date_text):
    try:
        return datetime.strptime(date_text, '%m/%d/%Y').strftime("%b-%Y")
    except ValueError:
        print(date_text)
        return date_text

# Adding the Day of Week Column


def day_of_week(date_text):
    try:
        return datetime.strptime(date_text, '%m/%d/%Y').strftime("%A")
    except ValueError:
        print(date_text)
        return date_text


# Seperate the dataframes based on income/expense
def seperate_dataframes():
    global income_data
    global expense_data

    expense_data = base_data.loc[base_data['type'] == 'Expenses']
    income_data = base_data.loc[base_data['type'] == 'Income']

    # Convert the negative strings of expense to positive
    expense_data['amount'] = pd.to_numeric(expense_data['amount'])
    # Since expenses are recorded as negative, converting them to positive
    expense_data['amount'] = expense_data['amount'].apply(lambda x: abs(x))

    # Convert Income data to Integer
    income_data['amount'] = pd.to_numeric(income_data['amount'])

    # Sort both the dataframes
    expense_data = expense_data.sort_values(by=['date'], ascending=True)
    income_data = income_data.sort_values(by=['date'], ascending=True)


# Load MoM Change for the last two months
def load_mom_change():
    try:
        grouped_expense_date = expense_data.groupby(
            'month_year', as_index=False).agg({'amount': [np.sum]})

        # Sort the date
        grouped_expense_date['date'] = grouped_expense_date['month_year'].apply(
            lambda x: datetime.strptime(x, '%b-%Y').strftime("%m/%d/%Y"))
        grouped_expense_date = grouped_expense_date.sort_values(by=['date'])

        grouped_expense_date = grouped_expense_date.drop(['date'], axis=1)

        grouped_expense_date = grouped_expense_date.tail(2)

        mom_expense_change = {}
        list_mom_change = grouped_expense_date.values.tolist()

        # Getting the difference
        diff_change = list(map(lambda x: x[1], list_mom_change))

        mom_expense_change['mom'] = round(diff_change[0] - diff_change[1], 2)

        return mom_expense_change
    except Exception as e:
        print(str(e))

        return None


# Alexa Skill to get monthly expense
def load_mom_expense_change_alexa():
    try:
        grouped_expense_date = expense_data.groupby(
            'month_year', as_index=False).agg({'amount': [np.sum]})

        # Sort the date
        grouped_expense_date['date'] = grouped_expense_date['month_year'].apply(
            lambda x: datetime.strptime(x, '%b-%Y').strftime("%m/%d/%Y"))
        grouped_expense_date = grouped_expense_date.sort_values(by=['date'])

        grouped_expense_date = grouped_expense_date.drop(['date'], axis=1)

        grouped_expense_date = grouped_expense_date.tail(2)
        list_mom_change = grouped_expense_date.values.tolist()

        # Getting the difference
        diff_change = list(map(lambda x: x[1], list_mom_change))

        return round(diff_change[1] - diff_change[0], 2)
    except Exception as e:
        print(str(e))

        return 0


# Alexa Skill to get monthly income
def load_mom_income_change_alexa():
    try:
        grouped_income_date = income_data.groupby(
            'month_year', as_index=False).agg({'amount': [np.sum]})

        # Sort the date
        grouped_income_date['date'] = grouped_income_date['month_year'].apply(
            lambda x: datetime.strptime(x, '%b-%Y').strftime("%m/%d/%Y"))
        grouped_income_date = grouped_income_date.sort_values(by=['date'])

        grouped_income_date = grouped_income_date.drop(['date'], axis=1)

        grouped_income_date = grouped_income_date.tail(2)

        list_mom_change = grouped_income_date.values.tolist()

        # Getting the difference
        diff_change = list(map(lambda x: x[1], list_mom_change))

        return round(diff_change[1] - diff_change[0], 2)
    except Exception as e:
        print(str(e))

        return 0


# Calculate the overall expenditure change every Month (SUM, MEAN & STD)
# And get all the month names
def get_box_plot_expense():
    global expense_data

    grouped_expense_date = expense_data.groupby('month_year', as_index=False).agg(
        {'amount': [np.sum, np.median, np.mean, np.average, np.std]})
    grouped_expense_date.columns = [
        'month_year', 'sum', 'median', 'mean', 'averagae', 'standard_deviation']

    # Sort the date
    grouped_expense_date['date'] = grouped_expense_date['month_year'].apply(
        lambda x: datetime.strptime(x, '%b-%Y').strftime("%m/%d/%Y"))
    grouped_expense_date = grouped_expense_date.sort_values(by=['date'])

    grouped_expense_date = grouped_expense_date.drop(['date'], axis=1)

    # Round the three numeric columns
    grouped_expense_date['sum'] = grouped_expense_date['sum'].apply(
        lambda x: round(x, 2))
    grouped_expense_date['median'] = grouped_expense_date['median'].apply(
        lambda x: round(x, 2))
    grouped_expense_date['mean'] = grouped_expense_date['mean'].apply(
        lambda x: round(x, 2))
    grouped_expense_date['averagae'] = grouped_expense_date['averagae'].apply(
        lambda x: round(x, 2))
    grouped_expense_date['standard_deviation'] = grouped_expense_date['standard_deviation'].apply(
        lambda x: round(x, 2))

    series_dict = highcharts_converter.create_box_plot(
        grouped_expense_date, 'Month-Year', 'Observations')

    return series_dict


# Calculate the overall income change every Month (SUM, MEAN & STD)
# And get all the month names
def get_box_plot_income():
    global income_data

    grouped_income_date = income_data.groupby('month_year', as_index=False).agg(
        {'amount': [np.sum, np.median, np.mean]})
    grouped_income_date.columns = [
        'month_year', 'sum', 'median', 'mean']

    # Sort the date
    grouped_income_date['date'] = grouped_income_date['month_year'].apply(
        lambda x: datetime.strptime(x, '%b-%Y').strftime("%m/%d/%Y"))
    grouped_income_date = grouped_income_date.sort_values(by=['date'])

    grouped_income_date = grouped_income_date.drop(['date'], axis=1)

    # Round the three numeric columns
    grouped_income_date['sum'] = grouped_income_date['sum'].apply(
        lambda x: round(x, 2))
    grouped_income_date['median'] = grouped_income_date['median'].apply(
        lambda x: round(x, 2))
    grouped_income_date['mean'] = grouped_income_date['mean'].apply(
        lambda x: round(x, 2))

    series_dict = highcharts_converter.create_box_plot(
        grouped_income_date, 'Month-Year', 'Observations')

    return series_dict


# Get the multiple-line sum change of expenditure VS income line
def get_sum_change_expenditure_income():
    global expense_data
    global income_data

    # Expense
    grouped_expense_date = expense_data.groupby(
        'month_year', as_index=False).agg({'amount': [np.sum]})
    grouped_expense_date.columns = ['month_year', 'sum']

    # Sort the date
    grouped_expense_date['date'] = grouped_expense_date['month_year'].apply(
        lambda x: datetime.strptime(x, '%b-%Y').strftime("%m/%d/%Y"))
    grouped_expense_date = grouped_expense_date.sort_values(by=['date'])

    grouped_expense_date = grouped_expense_date.drop(['date'], axis=1)

    # Round the three numeric columns
    grouped_expense_date['sum'] = grouped_expense_date['sum'].apply(
        lambda x: round(x, 2))

    # Income
    grouped_income_date = income_data.groupby(
        'month_year', as_index=False).agg({'amount': [np.sum]})
    grouped_income_date.columns = ['month_year', 'sum']

    # Sort the date
    grouped_income_date['date'] = grouped_income_date['month_year'].apply(
        lambda x: datetime.strptime(x, '%b-%Y').strftime("%m/%d/%Y"))
    grouped_income_date = grouped_income_date.sort_values(by=['date'])

    grouped_income_date = grouped_income_date.drop(['date'], axis=1)

    # Round the three numeric columns
    grouped_income_date['sum'] = grouped_income_date['sum'].apply(
        lambda x: round(x, 2))

    multiple_series_line_dict = highcharts_converter.create_multiple_series(
        grouped_expense_date, grouped_income_date, 'Total Count', 'Expense/Month', 'Income/Month')
    return multiple_series_line_dict


# Get Expense by Month
def get_expenditure_category_by_month_name(month_name):
    global expense_data
    expense_month_year = expense_data.loc[expense_data['month_year'] == month_name]

    expense_month_year = expense_month_year.groupby(
        'category', as_index=False).agg({'amount': [np.sum]})
    expense_month_year.columns = ['category_name', 'sum_amount']
    return highcharts_converter.create_single_series_pie(expense_month_year, 'Monthly Expenditure')


# Get Income by Month
def get_income_category_by_month_name(month_name):
    global income_data
    income_month_year = income_data.loc[income_data['month_year'] == month_name]

    income_month_year = income_month_year.groupby(
        'category', as_index=False).agg({'amount': [np.sum]})
    return highcharts_converter.create_single_series_pie(income_month_year, 'Monthly Income')


# Get all the month names
def get_all_month_names():
    global expense_data

    try:
        grouped_expense_date = expense_data.groupby('month_year', as_index=False).agg(
            {'amount': [np.sum, np.median, np.mean, np.average, np.std]})
        grouped_expense_date.columns = [
            'month_year', 'sum', 'median', 'mean', 'averagae', 'standard_deviation']

        # Sort the date
        grouped_expense_date['date'] = grouped_expense_date['month_year'].apply(
            lambda x: datetime.strptime(x, '%b-%Y').strftime("%m/%d/%Y"))
        grouped_expense_date = grouped_expense_date.sort_values(by=['date'])

        grouped_expense_date = grouped_expense_date.drop(['date'], axis=1)

        month_names_dict = {}

        month_names_list = list(
            map(lambda x: x[0], grouped_expense_date.values.tolist()))
        month_names_dict['month_names'] = month_names_list
        return month_names_dict
    except Exception as e:
        print(str(e))

        return None
