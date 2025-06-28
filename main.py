from flask import Flask, request, jsonify
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')  # Set your region
table = dynamodb.Table('rider-info')  # Replace with your table name

app = Flask(__name__)
#excel_file = "senior_signups.xlsx"

@app.route("/")
def home():
    return "This is the home page of the SeniorGo server."

@app.route("/signUpSenior", methods=["POST"])
def sign_up_senior():
    data = request.get_json()
    print(data)

    required_fields = ["fullName", "phone", "email", "password", "confirmPassword", "address", "agree"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    row = {
        "email-address": data["email"],
        "full-name": data["fullName"],
        "phone": data["phone"],
        "password": data["password"],  # ⚠️ Hash in production
        "address": data["address"]
    }

    try:
        # ✅ Prevent duplicate email using conditional expression
        table.put_item(
            Item=row,
            ConditionExpression="attribute_not_exists(#email)",
            ExpressionAttributeNames={"#email": "email-address"}
        )

        # ✅ Email setup
        sender_email = "vkalpsm@gmail.com"
        receiver_email = data["email"]
        app_password = "wkmu kctm vpje coib"

        subject = "Account Signup Confirmation"
        body = (
            "Hi there,\n\nYou have successfully signed up for SeniorGo! "
            "Thank you for joining our community.\n\nBest regards,\nSeniorGo Team"
        )

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)
            print("✅ Email sent successfully!")

        return jsonify({"message": "Signup saved successfully!"}), 200

    except ClientError as e:
        # ✅ Specific handling for duplicate email
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return jsonify({"message": "This email already exists. Please try logging in instead"}), 400
        else:
            print(f"Unexpected ClientError: {e}")
            return jsonify({"message": f"Unexpected error: {str(e)}"}), 500

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": f"Failed to save data: {str(e)}"}), 500

@app.route("/signUpVolunteer", methods=["POST"])
def sign_up_volunteer():
    data = request.get_json()
    print(data)

    required_fields = [
        "fullName", "dob", "email", "password", "phone", "address",
        "hasLicense", "licenseNumber", "hasVehicle", "vehicleType", "proof",
        "backgroundCheck", "volunteeredBefore", "firstAid", "mobilityHelp"
    ]
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    row = {
        "email-address": data["email"],
        "password": data["password"],  
        "full-name": data["fullName"],
        "date-of-birth": data["dob"],
        "phone": data["phone"],
        "address": data["address"],
        "has-driver's-license": data["hasLicense"],
        "license-number": data["licenseNumber"],
        "has-vehicle": data["hasVehicle"],
        "vehicle-type": data["vehicleType"],
        "proof-of-insurance": data["proof"],
        "background-check-consent": data["backgroundCheck"],
        "volunteered-before": data["volunteeredBefore"],
        "first-aid-trained": data["firstAid"],
        "comfortable-with-mobility-assistance": data["mobilityHelp"]
    }

    try:
        volunteer_table = boto3.resource('dynamodb').Table('volunteers-info')

        volunteer_table.put_item(
            Item=row,
            ConditionExpression="attribute_not_exists(#email)",
            ExpressionAttributeNames={"#email": "email-address"}
        )

        # Send confirmation email
        sender_email = "vkalpsm@gmail.com"
        receiver_email = data["email"]
        app_password = "wkmu kctm vpje coib"

        subject = "Volunteer Signup Confirmation"
        body = (
            "Hi there,\n\nYou have successfully signed up to volunteer with SeniorGo! "
            "We truly appreciate your willingness to help.\n\nBest regards,\nSeniorGo Team"
        )

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)
            print("✅ Email sent successfully!")

        return jsonify({"message": "Volunteer signup saved successfully!"}), 200

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return jsonify({"message": "This email already exists. Please try logging in instead"}), 400
        else:
            print(f"Unexpected ClientError: {e}")
            return jsonify({"message": f"Unexpected error: {str(e)}"}), 500

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": f"Failed to save data: {str(e)}"}), 500

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "email" not in data or "password" not in data:
        return jsonify({"message": "Missing email or password"}), 400

    email = data["email"]
    password = data["password"]

    # Check in rider-info table (senior)
    try:
        response = table.get_item(Key={"email-address": email})
        senior = response.get("Item")
        if senior:
            if senior.get("password") == password:
                return jsonify({
                    "message": "Senior account login successful",
                    "accountType": "senior",
                    "data": senior
                }), 200
            else:
                return jsonify({"message": "Incorrect password"}), 401
    except Exception as e:
        print(f"Error querying rider-info: {e}")

    # Check in volunteers-info table
    try:
        volunteer_table = boto3.resource('dynamodb').Table('volunteers-info')
        response = volunteer_table.get_item(Key={"email-address": email})
        volunteer = response.get("Item")
        if volunteer:
            if volunteer.get("password") == password:
                return jsonify({
                    "message": "Volunteer account login successful",
                    "accountType": "volunteer",
                    "data": volunteer
                }), 200
            else:
                return jsonify({"message": "Incorrect password"}), 401
    except Exception as e:
        print(f"Error querying volunteers-info: {e}")

    return jsonify({"message": "Account does not exist"}), 404

    
if __name__ == "__main__":
   app.run(debug=True, host='10.0.0.24', port=5000)  # Change host and port as needed

