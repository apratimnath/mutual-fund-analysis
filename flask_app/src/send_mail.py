'''
Created on Nov 28, 2020

@author: apratim
'''
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import json
import load_from_gspread


def driver_function(frame_data, list_data):
    list_to_insert = create_list_to_insert(frame_data, list_data);
    days_chunk = create_day_chunks(list_to_insert)
    
    return update_data_and_create_message_body(days_chunk, frame_data, list_data)


def create_list_to_insert(frame_data, list_data):
    current_pointer = len(list_data)

    # Getting the last date
    last_date = frame_data.values[current_pointer - 1][0]
    
    # Getting all the rows corresponding to the last date
    data_filtered = frame_data.loc[frame_data['Date'] == last_date]    
    data_filtered = data_filtered.drop(['Return', 'Net Change', 'date_formatted'], axis=1)
    
    # List of dictionaries
    list_to_insert = data_filtered.values.tolist()
    
    return list_to_insert


def create_day_chunks(list_to_insert):
    final_insert_list = []

    for i in range(0, 5):
        for each_row in list_to_insert: 
            final_insert_list.append(each_row)
    
    # Yield successive n-sized 
    # chunks from l. 
    def divide_chunks(l, n): 
        # looping till length l 
        for i in range(0, len(l), n): 
            yield l[i:i + n]
            
    days_chunk = list(divide_chunks(final_insert_list, len(list_to_insert)))
    
    return days_chunk


def email_alert(subject, body, to):
    msg = EmailMessage()
    msg.set_content(body)
    msg['subject'] = subject
    msg['to'] = to
    
    # Might give error 9due to relative path
    gmail_credentials_file = open("./config/gmail_credentials.json")
    gmail_credentials = json.load(gmail_credentials_file)
    
    sender = gmail_credentials['email']
    password = gmail_credentials['password']    
    
    msg['from'] = sender
    
    server = smtplib.SMTP("smtp.gmail.com", 587)
        
    try:
        server.starttls()
        server.login(sender, password)
        
        server.send_message(msg)
        
        return True
    except:
        return False
    finally: 
        server.quit()

        
def update_data_and_create_message_body(days_chunk, frame_data, list_data):
    success_insert = True
    total_rows = frame_data.shape[0] + 2  # 1st Row is heading
    
    current_pointer = len(list_data)
    # Getting the last date
    last_date = frame_data.values[current_pointer - 1][0]
    
    days_delta = 3
    
    for each_chunk in days_chunk:
        if(success_insert):
            date_to_add = (datetime.strptime(last_date, '%m/%d/%Y') + timedelta(days=days_delta)).strftime('%m/%d/%Y')
            for value in each_chunk:
                value[0] = date_to_add
                try:
                    load_from_gspread.update_row(value, total_rows)
                    print("Updated Row - " + str(total_rows))
                    total_rows += 1                
                except:
                    print("Error in Row - " + str(total_rows))
                    success_insert = False
                    break
            days_delta += 1
        else:
            break
    
    start_date = (datetime.strptime(last_date, '%m/%d/%Y') + timedelta(days=3)).strftime('%d-/%b-%Y')
    
    if(success_insert):
        body = '''
        Hi Apratim,
        
        The weekly scheduled insert of data is successful. Data is inserted for the next 5 days, starting from Tuesday - {var}.
        Please update the returns accordingly.
        
        Best Regards,
        Dev Team
        Mutual Fund Analysis App'''.format(var=start_date)
    else:
        body = '''
        Hi Apratim,
        
        There was some issue in updating your data. Rest assured our team is working on it.
        Meanwhile please update the data and returns manually, starting from - {var}.
        Sorry for the incovenience caused.
        
        Best Regards,
        Dev Team
        Mutual Fund Analysis App'''.format(var=start_date)
        
    subject = "Mutual Funds - Weekly Insertion of Base Data"
    to = "apratimnath7@gmail.com";
    
    return email_alert(subject, body, to)
