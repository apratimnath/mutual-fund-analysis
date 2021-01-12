'''
Created on Nov 28, 2020

@author: apratim
'''
import flask
from flask import request, jsonify, render_template
from flask_cors.extension import CORS
from flask_ask import Ask, statement, question, session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
from datetime import datetime
import load_from_gspread
import personal_finance
import pandas as pd
from http.client import HTTPException
import internal_calculations
import update_mf_changes
import send_mail
import warnings
import json
import logging
import math

warnings.filterwarnings('ignore')

app = flask.Flask(__name__)
CORS(app)
app.config["DEBUG"] = True

# Alexa Ask Config
ask = Ask(app, "/alexa-skill")

logging.getLogger("flask_ask").setLevel(logging.DEBUG)

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
        calculations_dict = internal_calculations.get_initial_results_dict(
            frame_data)

        if(calculations_dict == None or len(calculations_dict) == 0):
            return internal_server_error("Issue in calculating the daily changes. Please refer logs for fore details")
        else:
            return jsonify(calculations_dict), 200, {'Content-Type': 'application/json'}


# Update the data based on NAV data updated via Google
# This will be used called regularly via CRON Scheduler to keep the alive, and update the data
@app.route('/api/v1/update-mf-data', methods=['GET'])
def update_mf_data():
    is_success_update = update_mf_changes.driver_function()

    if(is_success_update):
        success_dict = {}
        success_dict['code'] = 200
        success_dict['message'] = "Successfully updated the Base MF Spreadsheet"

        return jsonify(success_dict), 200, {'Content-Type': 'application/json'}
    return internal_server_error("Issue in updating the Base MF Spreadsheet")


# This method will will be called regularly at the end of the day to send a mail to the user with daily update.
# The contents of the mail will be -
# Daily Change
# Daily Change graph
# Next day change
# Next day change graph
@app.route('/api/v1/send-daily-mailer', methods=['GET'])
def send_daily_mailer():
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
        
        mail_status = internal_calculations.create_mailer_data(frame_data)
        
        if(not mail_status):
            return internal_server_error("Error in sending daily mailer.")
        
        response = {}
        response['status'] = "Success"
        response['message'] = "Successfully sent daily mailer"

        return jsonify(response), 200, {'Content-Type': 'application/json'}


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
            response['status'] = "Success"
            response['message'] = "Successfully sent mail"

            return jsonify(response), 200, {'Content-Type': 'application/json'}
    else:
        return no_content("No Content found in request body")

'''
The following methods deals with personal savings.
List of API Enpoints are - 

1. Get the initial difference (MoM Changes)
'''

# Get the MoM Changes


@app.route('/api/v1/money-manager/get-mom', methods=['GET'])
def get_last_mom_changes():
    try:
        is_loaded_initil_data = personal_finance.get_the_data_from_gspread()
        if(is_loaded_initil_data):
            mom_data = personal_finance.load_mom_change()

            if(mom_data == None):
                return internal_server_error('MoM calculation gives error')

            return jsonify(mom_data), 200, {'Content-Type': 'appliction/json'}
        else:
            return internal_server_error('Error in loading the initial data!')
    except Exception as e:
        print(str(e))

        return internal_server_error('Error while MoM Calculation')

# Get the month-name


@app.route('/api/v1/money-manager/month-names', methods=['GET'])
def get_month_names():
    try:
        result = personal_finance.get_all_month_names()

        if(result != None):
            return jsonify(result), 200, {'Content-Type': 'appliction/json'}
        else:
            return no_content("No Content found")
    except Exception as e:
        print(str(e))

        return internal_server_error('Error while fetching all month names')

# Get the box-plot for expenses


@app.route('/api/v1/money-manager/boxplot-expenses', methods=['GET'])
def get_boxplot_expenses():
    try:
        result = personal_finance.get_box_plot_expense()

        if(result != None):
            return json.dumps(result), 200, {'Content-Type': 'appliction/json'}
        else:
            return no_content("No Content found")
    except Exception as e:
        print(str(e))

        return internal_server_error('Error while creating box plot for expenses')

# Get the box-plot for incomes


@app.route('/api/v1/money-manager/boxplot-income', methods=['GET'])
def get_boxplot_income():
    try:
        result = personal_finance.get_box_plot_income()

        if(result != None):
            return json.dumps(result), 200, {'Content-Type': 'appliction/json'}
        else:
            return no_content("No Content found")
    except Exception as e:
        print(str(e))

        return internal_server_error('Error while creating box plot for income')

# Get the multi-series line of Expense VS Income (Monthwise)


@app.route('/api/v1/money-manager/monthwise-expense-income', methods=['GET'])
def get_monthwise_expense_income():
    try:
        result = personal_finance.get_sum_change_expenditure_income()

        if(result != None):
            return json.dumps(result), 200, {'Content-Type': 'appliction/json'}
        else:
            return no_content("No Content found")
    except Exception as e:
        print(str(e))

        return internal_server_error('Error while creating multi-series line of Expense VS Income (Monthwise)')

# Get the Expenditure Pie (Monthwise)


@app.route('/api/v1/money-manager/monthwise-expense', methods=['POST'])
def get_monthwise_expense():
    try:
        request_body = request.json
        month_name = request_body['month_name']
        result = personal_finance.get_expenditure_category_by_month_name(
            month_name)

        if(result != None):
            return json.dumps(result), 200, {'Content-Type': 'appliction/json'}
        else:
            return no_content("No Content found")
    except Exception as e:
        print(str(e))

        return internal_server_error('Error while creating Pie of Expense (Monthwise)')

# Get the Income Pie (Monthwise)


@app.route('/api/v1/money-manager/monthwise-income', methods=['POST'])
def get_monthwise_income():
    try:
        request_body = request.json
        month_name = request_body['month_name']
        result = personal_finance.get_income_category_by_month_name(month_name)

        if(result != None):
            return json.dumps(result), 200, {'Content-Type': 'appliction/json'}
        else:
            return no_content("No Content found")
    except Exception as e:
        print(str(e))

        return internal_server_error('Error while creating Pie of Expense (Monthwise)')

# Method to do data cleaning of all kind


def do_data_cleaning():
    frame_data.replace([''], 'Unknown', inplace=True)

'''
The following API and the intents are created for Alexa
'''


@ask.launch
def start_skill():
    current_date = datetime.today()
    current_date_str = current_date.strftime("%d %B, %Y")

    welcome_msg = render_template('welcome', date_str=current_date_str)
    return question(welcome_msg)


@ask.intent("YesIntent", convert={'code': int})
def verify_code(code):
    if(code == 1023):
        choice_msg = render_template('choice')

        return question(choice_msg)
    else:
        error_msg = render_template('failure')
        return statement(error_msg)


@ask.intent("CurrentTypeIntent")
def give_current_results():
    global frame_data
    global list_data

    # Get the d-t-d mutual fund change
    list_data = load_from_gspread.get_credential_and_connect()
    frame_data = pd.DataFrame(list_data)
    do_data_cleaning()

    mf_change = internal_calculations.get_change_by_alexa(frame_data)

    if(mf_change >= 0):
        mf_message = render_template('mf_increase', mf_change=mf_change)
    else:
        mf_change = math.fabs(mf_change)
        mf_message = render_template('mf_decrease', mf_change=mf_change)

    # Personal Finance Change
    is_loaded_initil_data = personal_finance.get_the_data_from_gspread()
    expense_change = 0
    income_change = 0

    if(is_loaded_initil_data):
        # Get the expense MoM Change
        expense_change = personal_finance.load_mom_expense_change_alexa()
        income_change = personal_finance.load_mom_income_change_alexa()

        if(expense_change > 0):
            expense_message = render_template(
                'expense_increase', expense_change=expense_change)
        else:
            expense_change = math.fabs(expense_change)
            expense_message = render_template(
                'expense_decrease', expense_change=expense_change)

        if(income_change >= 0):
            income_message = render_template(
                'income_increase', income_change=income_change)
        else:
            income_change = math.fabs(income_change)
            income_message = render_template(
                'income_decrease', income_change=income_change)
    else:
        expense_message = render_template(
            'expense_decrease', expense_change=expense_change)
        income_message = render_template(
            'income_increase', income_change=income_change)

    redirect_message = render_template('redirect_predict')

    final_message = mf_message + "..." + \
        expense_message + "..." + income_message + "..." + redirect_message

    return question(final_message)


@ask.intent("FutureTypeIntent")
def give_future_results(code):
    # TO DO
    # Fetch the future type intent
    future_pending_msg = render_template('future_pending')

    return statement(future_pending_msg)


@ask.intent("NoIntent")
def end_skill():
    end_msg = render_template('stop_skill')

    return statement(end_msg)


@ask.intent("AMAZON.HelpIntent")
def help_skill():
    current_date = datetime.today()
    current_date_str = current_date.strftime("%d %B, %Y")

    help_msg = render_template('help', date_str=current_date_str)
    return question(help_msg)

# Test the Skill Main API


@app.route('/api/v1/alexa-skill/test', methods=['GET'])
def test_alexa_skill_main_intent():
    global frame_data
    global list_data
    # Get the d-t-d mutual fund change
    list_data = load_from_gspread.get_credential_and_connect()
    frame_data = pd.DataFrame(list_data)
    do_data_cleaning()

    mf_change = internal_calculations.get_change_by_alexa(frame_data)

    if(mf_change >= 0):
        mf_message = render_template('mf_increase', mf_change=mf_change)
    else:
        mf_change = math.fabs(mf_change)
        mf_message = render_template('mf_decrease', mf_change=mf_change)

    # Personal Finance Change
    is_loaded_initil_data = personal_finance.get_the_data_from_gspread()
    expense_change = 0
    income_change = 0

    if(is_loaded_initil_data):
        # Get the expense MoM Change
        expense_change = personal_finance.load_mom_expense_change_alexa()
        income_change = personal_finance.load_mom_income_change_alexa()

        if(expense_change > 0):
            expense_message = render_template(
                'expense_increase', expense_change=expense_change)
        else:
            expense_change = math.fabs(expense_change)
            expense_message = render_template(
                'expense_decrease', expense_change=expense_change)

        if(income_change >= 0):
            income_message = render_template(
                'income_increase', income_change=income_change)
        else:
            income_change = math.fabs(income_change)
            income_message = render_template(
                'income_decrease', income_change=income_change)

    else:
        expense_message = render_template(
            'expense_decrease', expense_change=expense_change)
        income_message = render_template(
            'income_increase', income_change=income_change)

    final_message = mf_message + "..." + expense_message + "..." + income_message

    return json.dumps(final_message), 200, {'Content-Type': 'appliction/json'}

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

# Disabled Scheduler currently as it is handled by Google NAV
# scheduler = BackgroundScheduler()
# scheduler.add_job(weekly_insert_in_sheet,
#                   CronTrigger.from_crontab('00 17 * * SAT'))
# scheduler.start()

# atexit.register(lambda: scheduler.shutdown())
