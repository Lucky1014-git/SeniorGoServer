from flask import Flask, request, jsonify
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import boto3
from botocore.exceptions import ClientError
import uuid
import random
from common import setup_login_routes,set_forgot_password_routes,set_change_password_routes,setup_update_status_routes,setup_update_status_bar_routes
from seniors import setup_signup_senior_routes,setup_request_ride_routes,setup_current_rides_routes
from volunteer import setup_signup_volunteer_routes, setup_active_requests_routes,setup_accept_requests_routes,setup_accepted_requests_routes
from admin import setup_admin_login_routes, setup_create_group_routes

dynamodb = boto3.resource('dynamodb')  # Set your region

app = Flask(__name__)
#excel_file = "senior_signups.xlsx"


# Setup login routes from common.py
setup_login_routes(app)
# Setup forgot password routes from common.py
set_forgot_password_routes(app)
# Setup change password routes from common.py
set_change_password_routes(app)

# Setup update status routes from common.py
setup_update_status_routes(app)
# Setup update status bar routes from common.py
setup_update_status_bar_routes(app)


# Setup signup routes from seniors.py
setup_signup_senior_routes(app)
# Setup request ride routes from seniors.py
setup_request_ride_routes(app)
# Setup current rides routes from seniors.py
setup_current_rides_routes(app)


# Setup signup routes from volunteer.py
setup_signup_volunteer_routes(app)
# Setup active requests routes from volunteer.py
setup_active_requests_routes(app)
# Setup accept requests routes from volunteer.py
setup_accept_requests_routes(app)
# Setup accepted requests routes from volunteer.py
setup_accepted_requests_routes(app)

# Setup admin login routes from admin.py
setup_admin_login_routes(app)
# Setup create group routes from admin.py
setup_create_group_routes(app)

@app.route("/")
def home():
    return "This is the home page of the SeniorGo server."



    
# The currentRides API is responsible for displaying the current rides.
if __name__ == "__main__":
   app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
if __name__ == "__main__":
   app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

