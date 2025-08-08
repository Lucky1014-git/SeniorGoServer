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
from common import setup_login_routes,set_forgot_password_routes,set_change_password_routes    
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


# ...existing code...

@app.route("/updateStatus", methods=["POST"])
def update_status():
    data = request.get_json()
    print(f"Received data in updateStatus: {data}")  # Debug: see all incoming data
    ride_id = data.get("rideId")
    print(f"Extracted ride_id: '{ride_id}' (type: {type(ride_id)})")  # Debug: see exact value and type
    
    # Also check for alternative parameter names
    if not ride_id:
        ride_id = data.get("id")  # Fallback to 'id' if 'rideId' not found
        print(f"Fallback ride_id from 'id': '{ride_id}'")
    
    if not ride_id:
        print("No ride ID found in request data")
        return jsonify({"message": "Missing ride id"}), 400
    try:
        ride_table = dynamodb.Table('rideinfo')
        ride_resp = ride_table.get_item(Key={"id": ride_id})
        current_status = ride_resp.get("Item", {}).get("status", "unknown")
        print(f"Current status for ride {ride_id}: {current_status}")

        if current_status == "volunteerstarted":
            new_status = "ridestarted"
        elif current_status == "ridestarted":
            new_status = "rideended"
        else:
            new_status = "rideended"

        ride_table.update_item(
            Key={"id": ride_id},
            UpdateExpression="SET #status = :newstatus",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":newstatus": new_status}
        )
        return jsonify({"status": new_status}), 200
    except Exception as e:
        print(f"Error updating ride status: {e}")
        return jsonify({"message": f"Failed to update ride status: {str(e)}"}), 500

@app.route("/updateStatusBar", methods=["POST"])
def update_status_bar():
    data = request.get_json()
    ride_id = data.get("rideId")
    if not ride_id:
        return jsonify({"message": "Missing ride id"}), 400
    try:
        ride_table = dynamodb.Table('rideinfo')
        ride_resp = ride_table.get_item(Key={"id": ride_id})
        status = ride_resp.get("Item", {}).get("status", None)
        if status == "volunteerstarted":
            return jsonify({"status": "volunteerstarted"}), 200
        elif status == "ridestarted":
            return jsonify({"status": "ridestarted"}), 200
        elif status == "rideended":
            return jsonify({"status": "rideended"}), 200
        else:
            return jsonify({"status": status}), 200
    except Exception as e:
        print(f"Error in updateStatusBar: {e}")
        return jsonify({"message": f"Failed to get ride status: {str(e)}"}), 500
    
# The currentRides API is responsible for displaying the current rides.
if __name__ == "__main__":
   app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
if __name__ == "__main__":
   app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

