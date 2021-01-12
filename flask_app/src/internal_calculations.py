'''
Created on Nov 29, 2020

@author: apratim
'''
from datetime import datetime
from matplotlib import pyplot
import send_mail
import os

'''
After we get the initial data loaded from google spreadsheet, we will do the following -

1. Create a dict to be sent as the initial response.
2. The initial response will contain the daily change (sum, mean and standard deviation), based on the following categories -
    a. Grouped based on App
    b. Grouped based on Fund
    c. Overall
3. No assumption are predefined, and everything is calculated based on the data received.
4. This will prevent errors in case any fund is started or ended
5. The function further calls three sub routines to calculate for each category.
6. Calcultions are done by first groupby, then aggregate (numpy), then creating common dataframe with value comparision using numpy
'''
import numpy as np
import warnings
import pandas as pd

warnings.filterwarnings('ignore')


def get_initial_results_dict(original_data):
    # Subset of data containing returns
    valid_data_with_returns = original_data.loc[original_data['Return'] != 'Unknown']    
    length_of_valid_returns = valid_data_with_returns.shape[0]
    
    # Getting the last date
    last_date = valid_data_with_returns.values[length_of_valid_returns - 1][0]
    
    # Get the last date and the date before that data
    last_date_rows = valid_data_with_returns.loc[valid_data_with_returns['Date'] == last_date]
    previous_date_rows = valid_data_with_returns.loc[valid_data_with_returns['Date'] != last_date].tail(last_date_rows.shape[0])
    
    # last_date_rows_list = last_date_rows.values.tolist()
    # previous_date_rows_list = previous_date_rows.values.tolist()
    
    # Convert to numeric
    last_date_rows['Investment'] = pd.to_numeric(last_date_rows['Investment'])
    last_date_rows['Return'] = pd.to_numeric(last_date_rows['Return'])
    last_date_rows['Net Change'] = pd.to_numeric(last_date_rows['Net Change'])
    
    previous_date_rows['Investment'] = pd.to_numeric(previous_date_rows['Investment'])
    previous_date_rows['Return'] = pd.to_numeric(previous_date_rows['Return'])
    previous_date_rows['Net Change'] = pd.to_numeric(previous_date_rows['Net Change'])
    
    dict_to_return = {}
    
    try:
        app_based_list = get_app_based_data(last_date_rows, previous_date_rows)
        policy_based_list = get_policy_based_data(last_date_rows, previous_date_rows)
        overall_list = get_overall_data(last_date_rows, previous_date_rows)
        
        dict_to_return['app_based_calculations'] = app_based_list
        dict_to_return['policy_based_calculation'] = policy_based_list
        dict_to_return['overall_list'] = overall_list
        
        return dict_to_return
    except:
        return None


def get_change_by_alexa(original_data):
    # Subset of data containing returns
    valid_data_with_returns = original_data.loc[original_data['Return'] != 'Unknown']    
    length_of_valid_returns = valid_data_with_returns.shape[0]
    
    # Getting the last date
    last_date = valid_data_with_returns.values[length_of_valid_returns - 1][0]
    
    # Get the last date and the date before that data
    last_date_rows = valid_data_with_returns.loc[valid_data_with_returns['Date'] == last_date]
    previous_date_rows = valid_data_with_returns.loc[valid_data_with_returns['Date'] != last_date].tail(last_date_rows.shape[0])
    
    # last_date_rows_list = last_date_rows.values.tolist()
    # previous_date_rows_list = previous_date_rows.values.tolist()
    
    # Convert to numeric
    last_date_rows['Investment'] = pd.to_numeric(last_date_rows['Investment'])
    last_date_rows['Return'] = pd.to_numeric(last_date_rows['Return'])
    last_date_rows['Net Change'] = pd.to_numeric(last_date_rows['Net Change'])
    
    previous_date_rows['Investment'] = pd.to_numeric(previous_date_rows['Investment'])
    previous_date_rows['Return'] = pd.to_numeric(previous_date_rows['Return'])
    previous_date_rows['Net Change'] = pd.to_numeric(previous_date_rows['Net Change'])
    
    dict_to_return = {}
    
    try:
        overall_list = get_overall_data(last_date_rows, previous_date_rows)
        
        if(len(overall_list) == 1):
            return overall_list[0]['sum_difference']
        return 0
    except:
        return 0

    
def get_app_based_data(last_date_rows, previous_date_rows):
    try:
        # App-wise calculation
        grouped_last = last_date_rows.groupby('App', as_index=False).agg({'Net Change':[np.sum, np.mean, np.std]})
        grouped_previous = previous_date_rows.groupby('App', as_index=False).agg({'Net Change':[np.sum, np.mean, np.std]})
        
        # Rename previos frame colums
        grouped_previous.columns = ['app', 'prev_sum', 'prev_mean', 'prev_std']
        
        # Create single comparision frame
        compare_frame = grouped_last
        compare_frame.columns = ['app', 'current_sum', 'current_mean', 'current_std']
        
        compare_frame['prev_sum'] = grouped_previous['prev_sum']
        compare_frame['prev_mean'] = grouped_previous['prev_mean']
        compare_frame['prev_std'] = grouped_previous['prev_std']
        
        compare_frame['sum_diff'] = np.where(compare_frame['current_sum'] == compare_frame['prev_sum'], 0 , compare_frame['current_sum'] - compare_frame['prev_sum'])
        compare_frame['mean_diff'] = np.where(compare_frame['current_mean'] == compare_frame['prev_mean'], 0 , compare_frame['current_mean'] - compare_frame['prev_mean'])
        compare_frame['std_diff'] = np.where(compare_frame['current_std'] == compare_frame['prev_std'], 0 , compare_frame['current_std'] - compare_frame['prev_std'])
        
        compare_frame = compare_frame.drop(['current_sum', 'current_mean', 'current_std', 'prev_sum', 'prev_mean', 'prev_std'], axis=1)
        
        app_diff_list = compare_frame.values.tolist()
        
        app_dict_list = []
        for each_app in app_diff_list:
            current_dict = {}
            current_dict['app_name'] = each_app[0]
            current_dict['sum_difference'] = round(each_app[1], 2)
            current_dict['mean_difference'] = round(each_app[2], 2)
            current_dict['standard_deviation_difference'] = round(each_app[3], 2)
            
            app_dict_list.append(current_dict)
        
        return app_dict_list
    except:
        raise ValueError
    

def get_policy_based_data(last_date_rows, previous_date_rows):
    try:
        # Fund-wise calculation
        grouped_last = last_date_rows.groupby('Policy Name', as_index=False).agg({'Net Change':[np.sum]})
        grouped_previous = previous_date_rows.groupby('Policy Name', as_index=False).agg({'Net Change':[np.sum]})
        
        # Rename previos frame colums
        grouped_previous.columns = ['policy_name', 'prev_sum']
        
        # Create single comparision frame
        compare_frame = grouped_last
        compare_frame.columns = ['policy_name', 'current_sum']
        
        compare_frame['prev_sum'] = grouped_previous['prev_sum']
        
        compare_frame['sum_diff'] = np.where(compare_frame['current_sum'] == compare_frame['prev_sum'], 0 , compare_frame['current_sum'] - compare_frame['prev_sum'])
        
        compare_frame = compare_frame.drop(['current_sum', 'prev_sum'], axis=1)
        
        policy_diff_list = compare_frame.values.tolist()
        
        policy_dict_list = []
        for each_policy in policy_diff_list:
            current_dict = {}
            current_dict['policy_name'] = each_policy[0]
            current_dict['sum_difference'] = round(each_policy[1], 2)
            
            policy_dict_list.append(current_dict)
        
        return policy_dict_list
    except:
        raise ValueError

    
def get_overall_data(last_date_rows, previous_date_rows):
    try:
        # Overall calculation
        grouped_last = last_date_rows.groupby('Date', as_index=False).agg({'Net Change':[np.sum, np.mean, np.std]})
        grouped_previous = previous_date_rows.groupby('Date', as_index=False).agg({'Net Change':[np.sum, np.mean, np.std]})
        
        # Rename previos frame colums
        grouped_previous.columns = ['date', 'prev_sum', 'prev_mean', 'prev_std']
        
        # Create single comparision frame
        compare_frame = grouped_last
        compare_frame.columns = ['date', 'current_sum', 'current_mean', 'current_std']
        
        compare_frame['prev_sum'] = grouped_previous['prev_sum']
        compare_frame['prev_mean'] = grouped_previous['prev_mean']
        compare_frame['prev_std'] = grouped_previous['prev_std']
        
        compare_frame['sum_diff'] = np.where(compare_frame['current_sum'] == compare_frame['prev_sum'], 0 , compare_frame['current_sum'] - compare_frame['prev_sum'])
        compare_frame['mean_diff'] = np.where(compare_frame['current_mean'] == compare_frame['prev_mean'], 0 , compare_frame['current_mean'] - compare_frame['prev_mean'])
        compare_frame['std_diff'] = np.where(compare_frame['current_std'] == compare_frame['prev_std'], 0 , compare_frame['current_std'] - compare_frame['prev_std'])
        
        compare_frame = compare_frame.drop(['current_sum', 'current_mean', 'current_std', 'prev_sum', 'prev_mean', 'prev_std'], axis=1)
        
        overall_diff_list = compare_frame.values.tolist()
        
        overall_dict_list = []
        for each_overall in overall_diff_list:
            current_dict = {}
            current_dict['date'] = each_overall[0]
            current_dict['sum_difference'] = round(each_overall[1], 2)
            current_dict['mean_difference'] = round(each_overall[2], 2)
            current_dict['standard_deviation_difference'] = round(each_overall[3], 2)
            
            overall_dict_list.append(current_dict)
        
        return overall_dict_list
    except:
        raise ValueError

'''
The below function(s) serves the following purpose - 

1. Create a graph using pyplot for the sum of each date
2. Create HTML Content
3. Save the plot in the local storage (temp)
4. Create a mailer
5. Send the mailer

TODO - Add the future component in the same mailer. 
'''


def create_mailer_data(mf_data):
    try:
        grouped_mf_data = mf_data.groupby('Date', as_index=False).agg({'Return':[np.sum]})
        # Renaming the columns
        grouped_mf_data.columns = ['Date', 'Value']
        
        # Create a new date column to sort the data
        grouped_mf_data['Modified_Date'] = grouped_mf_data['Date'].apply(lambda x: datetime.strptime(x, '%m/%d/%Y'))
        grouped_mf_data.sort_values(by=['Modified_Date'], inplace=True, ascending=True)
        
        # Create the sting equivalent of the date olum
        grouped_mf_data['Date_Modified_Str'] = grouped_mf_data['Date'].apply(lambda x: datetime.strptime(x, '%m/%d/%Y').strftime("%Y-%m-%d"))
        
        # Drop the extra columns and rename
        grouped_mf_data = grouped_mf_data.drop(['Date', 'Modified_Date'], axis=1)
        grouped_mf_data.columns = ['Value', 'Date']
        grouped_mf_data = grouped_mf_data[['Date', 'Value']]
        
        if(len(grouped_mf_data) > 0):
            values_list = list(map(lambda x: x[1], grouped_mf_data.values.tolist()))
            daily_change = round(values_list[-1] - values_list[-2], 2)
            date_list = list(map(lambda x: x[0], grouped_mf_data.values.tolist()))
            current_date = datetime.strptime(date_list[-1], '%Y-%m-%d').strftime("%A, %b %d, %Y")
            
            #Get the text color
            text_color = 'red'
            if(daily_change > 0):
                text_color = 'green'
                
            print(daily_change)
            print(current_date)
            
            create_plot = create_and_save_plot(grouped_mf_data)
            
            if(create_plot):
                subject = "Daily Updates | " + current_date
                receiver = "apratimnath7@gmail.com"
                mail_sent = send_mail.email_mutipart__alert(subject, receiver, daily_change, current_date, text_color)
                
                if(mail_sent):
                    return True
        
        return False
    except Exception as e:
        print(e)
        return False
    finally:
        os.remove('current_data_plot.png') 


# Function to create and save the plot
def create_and_save_plot(grouped_mf_data):
    try:
        fig, ax = pyplot.subplots()
        grouped_mf_data['Actual_Date'] = grouped_mf_data['Date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))
        ax.plot(grouped_mf_data['Actual_Date'], grouped_mf_data['Value'], color=get_line_color(grouped_mf_data.values.tolist()))
        ax.xaxis_date()  # interpret the x-axis values as dates
        fig.set_size_inches(9, 5, forward=True)
        fig.autofmt_xdate()  # make space for and rotate the x-axis tick labels
        
        fig.savefig('current_data_plot.png')
        return True
    except Exception as e:
        print(e)
        return False


# Function to determine the color
def get_line_color(values):
    if(values[-1][1] > values[-2][1]):
        return 'green'
    return 'red'
