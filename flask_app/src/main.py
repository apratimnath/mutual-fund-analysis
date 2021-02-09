'''
Created on Nov 28, 2020

@author: apratim
'''
import all_api_endpoints
import warnings
import datetime

warnings.filterwarnings('ignore')

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    current_server_time= datetime.datetime.now()
    print("The current server time is - ")
    print(current_server_time)
    all_api_endpoints.app.run(threaded=True, port=8085, debug=True)
