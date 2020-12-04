'''
Created on Nov 28, 2020

@author: apratim
'''
import flask
from flask import request, jsonify
from flask_cors.extension import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
from datetime import datetime
import load_from_gspread
import pandas as pd
from http.client import HTTPException
import internal_calculations
import send_mail
import warnings

warnings.filterwarnings('ignore')

app = flask.Flask(__name__)
CORS(app)
app.config["DEBUG"] = True

frame_data = None
list_data = None


# Create all the error handlers
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


@app.errorhandler(500)
def internal_server_error(e):
    return "<h1>500</h1><p>" + e + "</p>", 500


@app.errorhandler(HTTPException)
def no_content(e):
    return "<h1>204</h1><p>" + e + "</p>", 204


@app.route('/', methods=['GET'])
def home():
    return '''<h1>APIs to get the mutual fund data</h1>
    <p>Over the years, investors have tried and tested various methodologies to keep a track of all investements. The various problems faced for the same are -</p>
    
    <ul>
        <li>Multi-vendor - The Mutual Funds are invested via multiple vendors, like Groww, Paytm Money, etc., hence no unified interface to track all investments.</li>
        <li>The historic data is not accurately predicted - Over time the historic data loses importance and is overriden to be fitted only in Time Series Graph.</li>
        <li>Periodic Tracking of data - Everyday net change in the invested amount.</li>
        <li>Personalized Prediction - Currently all Mutual Fund Predictions are not personalized, only based on overall NAV chnages.</li>
    </ul>
    
    <h2>API Sets</h2>
    <p>The app will consist of two major sets of API -</p>
    <ul>
        <li>Current Data - Various APIs to fetch the current investment data details to be show in the Current Investment Dashboard</li>
        <li>Prediction Data - Will predict the futur return, both overall, and per-investment basis, based on the user investment trend (will be available, only when the current dataset reached significant entires)</li>
    </ul>
    
    <h2>Data collection, Storage and Analysis Blueprint</h2>
    <p>Data from different apps will be collected in the following way -</p>
    <ul>
        <li>Per day data of return is manually entered in Google Sheet.</li>
        <li>Success or failure mails for everyday update is triggered based on the storage of data in the respective database.</li>
        <li>APIs expose the various data, grouped by various factors to be used in the UI.</li>
        <li>Once the stored data crosses a significant volume, this data is splitted into train and test data for future analysis.</li>
        <li>The predicted data is again exposed over APIs, grouped by various factors.</li>
    </ul>
    
    <h2>Deployment</h2>
    <p>The app is deployed using Heroku</p>
    '''


# A route to connect to spreadsheet and get all the data
@app.route('/api/v1/connect-gspread', methods=['GET'])
def connect_gspread():
    global frame_data
    global list_data
    
    list_data = load_from_gspread.get_credential_and_connect()
    if(list_data == None):
        return internal_server_error("Issue in connecting to GSpread")
    elif(len(list_data) == 0):
        return no_content("No Content found in the spreadsheet")
    else:
        # Creating the dataframe
        frame_data = pd.DataFrame(list_data)
        do_data_cleaning()
        calculations_dict = internal_calculations.get_initial_results_dict(frame_data)
        
        if(calculations_dict == None or len(calculations_dict) == 0):
            return internal_server_error("Issue in calculating the daily changes. Please refer logs for fore details")
        else:
            return jsonify(calculations_dict), 200, {'Content-Type': 'application/json'}


# Send mail to register new users
@app.route('/api/v1/register-user', methods=['POST'])
def register_user():
    global frame_data
    global list_data
    user_details = request.json
    
    if(user_details != None):
        is_success = send_mail.register_user(user_details)
        
        if(is_success):
            response = {}
            response['status'] = "Success";
            response['message'] = "Successfully sent mail"
            
            return jsonify(response), 200, {'Content-Type': 'application/json'}
    else:
        return no_content("No Content found in request body")


# Method to do data cleaning of all kind
def do_data_cleaning():
    frame_data.replace([''], 'Unknown', inplace=True)
    
'''
The following method will run a job, to store the next 5 days for the upcoming wee in Google Sheet
The method runs every Saturday at 5:00 PM
On success or error, it sends a mail accordingly
'''


def weekly_insert_in_sheet():
    global frame_data
    global list_data
    
    schedule_success = True
    
    print("Scheduled Job started")
    # Reload the intial data
    list_data = load_from_gspread.get_credential_and_connect()
    
    if(list_data == None or len(list_data) == 0):
        schedule_success = False
        print("Unable to refresh the spreadsheet from google")
    else:
        # Creating the dataframe
        frame_data = pd.DataFrame(list_data)        
        schedule_success = send_mail.driver_function(frame_data, list_data)
    
    if(schedule_success): 
        current_date = datetime.now()
        print("Scheduled Job successful at -", end=" ")
        print(current_date)
    else:
        current_date = datetime.now()
        print("Scheduled Job failed at -", end=" ")
        print(current_date)

    
scheduler = BackgroundScheduler()
scheduler.add_job(weekly_insert_in_sheet, CronTrigger.from_crontab('00 17 * * SAT'))
scheduler.start()

atexit.register(lambda: scheduler.shutdown())
