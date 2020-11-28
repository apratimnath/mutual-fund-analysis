'''
Created on Nov 29, 2020

@author: apratim
'''

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

    
def get_app_based_data(last_date_rows, previous_date_rows):
    try:
        # App-wise calculation
        grouped_last = last_date_rows.groupby('App', as_index=False).agg({'Return':[np.sum, np.mean, np.std]})
        grouped_previous = previous_date_rows.groupby('App', as_index=False).agg({'Return':[np.sum, np.mean, np.std]})
        
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
        grouped_last = last_date_rows.groupby('Policy Name', as_index=False).agg({'Return':[np.sum]})
        grouped_previous = previous_date_rows.groupby('Policy Name', as_index=False).agg({'Return':[np.sum]})
        
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
        grouped_last = last_date_rows.groupby('Date', as_index=False).agg({'Return':[np.sum, np.mean, np.std]})
        grouped_previous = previous_date_rows.groupby('Date', as_index=False).agg({'Return':[np.sum, np.mean, np.std]})
        
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

