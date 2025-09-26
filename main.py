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
from common import login_user, forgot_password, change_password, update_status, update_status_bar
from seniors import sign_up_senior,request_ride,current_rides,request_recurring_ride,cancel_ride
from volunteer import sign_up_volunteer, active_requests, accept_requests, accepted_requests
from admin import admin_login, create_group

dynamodb = boto3.resource('dynamodb')  # Set your region

app = Flask(__name__)
#excel_file = "senior_signups.xlsx"


@app.route("/")
def home():
    return "This is the home page of the SeniorGo server."

# Authentication & User Management APIs
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    return login_user(data)

@app.route("/signUpSenior", methods=["POST"])
def signUpSenior():
    data = request.get_json()
    return sign_up_senior(data)

@app.route("/signUpVolunteer", methods=["POST"])
def signUpVolunteer():
    data = request.get_json()
    return sign_up_volunteer(data)

@app.route("/changePassword", methods=["POST"])
def changePassword():
    data = request.get_json()
    return change_password(data)

@app.route("/forgotPassword", methods=["POST"])
def forgotPassword():
    data = request.get_json()
    return forgot_password(data)

# Admin APIs
@app.route("/adminLogin", methods=["POST"])
def adminLogin():
    data = request.get_json()
    return admin_login(data)

@app.route("/createGroup", methods=["POST"])
def createGroup():
    data = request.get_json()
    return create_group(data)

# Senior/Rider APIs
@app.route("/requestRide", methods=["POST"])
def requestRide():
    data = request.get_json()
    return request_ride(data)

@app.route("/requestRecurringRide", methods=["POST"])
def requestRecurringRide():
    data = request.get_json()
    return request_recurring_ride(data)

@app.route("/cancelRide", methods=["POST"])
def cancelRide():
    data = request.get_json()
    return cancel_ride(data)

@app.route("/currentRides", methods=["POST"])
def currentRides():
    data = request.get_json()
    return current_rides(data)

# Volunteer APIs
@app.route("/activeRequests", methods=["POST"])
def activeRequests():
    data = request.get_json()
    return active_requests(data)

@app.route("/acceptRequests", methods=["POST"])
def acceptRequests():
    data = request.get_json()
    return accept_requests(data)

@app.route("/acceptedRequests", methods=["POST"])
def acceptedRequests():
    data = request.get_json()
    return accepted_requests(data)

# Ride Status Management APIs
@app.route("/updateStatus", methods=["POST"])
def updateStatus():
    data = request.get_json()
    return update_status(data)

@app.route("/updateStatusBar", methods=["POST"])
def updateStatusBar():
    data = request.get_json()
    return update_status_bar(data)

   
# The currentRides API is responsible for displaying the current rides.
if __name__ == "__main__":
   app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

