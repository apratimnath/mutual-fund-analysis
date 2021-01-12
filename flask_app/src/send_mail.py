'''
Created on Nov 28, 2020

@author: apratim
'''
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import json
import load_from_gspread
import os
import warnings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

warnings.filterwarnings('ignore')


def driver_function(frame_data, list_data):
    list_to_insert = create_list_to_insert(frame_data, list_data)
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
    
    server = smtplib.SMTP("smtp.gmail.com", 587)
        
    try:
        json_str = os.environ.get('GMAIL_CREDENTIALS')
        is_local = False
        
        if(not json_str or len(json_str) == 0):
            is_local = True
            
        print("The state of application is Local", end=" ")
        print(is_local)
        
        if(is_local):
            print(os.getcwd())
            file_path = os.getcwd() + "/src/secret_config/gmail_credentials.json"
            gmail_credentials_file = open(file_path)
            gmail_credentials = json.load(gmail_credentials_file)
        else:
            gmail_credentials = json.loads(json_str)
        
        sender = gmail_credentials['email']
        password = gmail_credentials['password']
        
        msg['from'] = sender 
    
        server.starttls()
        server.login(sender, password)
        
        server.send_message(msg)
        
        return True
    except:
        return False
    finally: 
        server.quit()

        
def email_mutipart__alert(subject, to, daily_change, current_date, text_color):
    msg = MIMEMultipart('related')
    msg['subject'] = subject
    msg['to'] = to
    msg.preamble = 'This is a multi-part message in MIME format.'
    
    # Create the Alternative Text
    alt_text = '''
    Hi Apratim,
    
    Hope you're doing well!
    There was some problem in showing the HTML Content in the mailer. But don't worry, our teams are working on it!
    
    Meanwhile, here's your daily change details -
    
    Daily mutual fund change - {daily_change}
    
    Keep Investing!
    
    Best Regards,
    Personal Finance Ananlysis App
    '''.format(daily_change=daily_change)
    
    html_text = '<b>Your Daily Fund Analysis for {current_date} !</b><br><br><i>PFB a snapshot of the performance of your fund(s) over time -</i> <br><img src="cid:image1"><br><b><span style="color:{text_color}">Your daily change is {daily_change}.</b><br><br><i>You keep investing, we keep tracking!</i><br><br>Best Regards,<br>Team Personal Finance Analysis'.format(current_date=current_date, text_color=text_color, daily_change=daily_change)
    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msg.attach(msgAlternative)
    
    msgText = MIMEText(alt_text)
    msgAlternative.attach(msgText)
    
    # We reference the image in the IMG SRC attribute by the ID we give it below
    msgText = MIMEText(html_text, 'html')
    msgAlternative.attach(msgText)
    
    # This example assumes the image is in the current directory
    fp = open('current_data_plot.png', 'rb')
    msgImage = MIMEImage(fp.read())
    
    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', '<image1>')
    msg.attach(msgImage)  
    
    server = smtplib.SMTP("smtp.gmail.com", 587)
        
    try:
        json_str = os.environ.get('GMAIL_CREDENTIALS')
        is_local = False
        
        if(not json_str or len(json_str) == 0):
            is_local = True
            
        print("The state of application is Local", end=" ")
        print(is_local)
        
        if(is_local):
            print(os.getcwd())
            file_path = "D:/Codebase/Mutual_Fund_Analysis/Backend/mutual-fund-analysis/config/gmail_credentials.json"
            gmail_credentials_file = open(file_path)
            gmail_credentials = json.load(gmail_credentials_file)
        else:
            gmail_credentials = json.loads(json_str)
        
        sender = gmail_credentials['email']
        password = gmail_credentials['password']
        
        msg['from'] = sender 
    
        server.starttls()
        server.login(sender, password)
        
        server.sendmail(sender, to, msg.as_string())
        
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        fp.close() 
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
    to = "apratimnath7@gmail.com"
    
    return email_alert(subject, body, to)

'''
Created on 01.12.2020

The requirement is to send a mail to the registered user from the Dev ID, so that the Dev ID can have a track of the request
And created a corresponding user in Okta
'''


def register_user(user_details):
    first_name = user_details['firstName']
    last_name = user_details['lastName']
    email = user_details['email']
    contact_number = str(user_details['mobileNumber'])
    
    try:
        body = '''
        Hi {first_name},
        
        Thank you for registering for the Personal Finance Management App.
        Our teams are working on providing you the required access.
        In the mean time, you can go through some of the links, regarding the application -
        
        1. Dashboard GitHub Repo - https://github.com/apratimnath/mutual-fund-analysis-dashboard
        2. API GitHub Repo - https://github.com/apratimnath/mutual-fund-analysis
        3. LinkedIn Contact - https://www.linkedin.com/in/apratim-nath-871a69145
        
        We're creating your profile with the following information as provided - 
        
        1. First Name - {first_name}
        2. Last Name - {last_name}
        3. Email (Identifier) - {email}
        4. Contact - {contact_number}
        
        If the Email ID is incorrect please revert back within 48 hours so that our teams can make the necessary changes.
        Rest assured we're committed to cater to your every need of Financial Analysis
        
        Regards,
        Dev Team,
        Personal Finance Analysis Team
        '''.format(first_name=first_name, last_name=last_name, email=email, contact_number=contact_number)
        
        subject = "Welcome to Personal Finance Analysis App"
        
        return email_alert(subject, body, email)
    except:
        return False
