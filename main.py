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

dynamodb = boto3.resource('dynamodb')  # Set your region

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
        "emailaddress": data["email"],
        "fullname": data["fullName"],
        "phone": data["phone"],
        "password": data["password"],  # ⚠️ Hash in production
        "address": data["address"]
    }

    try:
        rider_table = dynamodb.Table('riderinfo')
        # ✅ Prevent duplicate email using conditional expression
        rider_table.put_item(
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
    print("lucky")

    required_fields = [
        "fullName", "dob", "email", "password", "phone", "address",
        "hasLicense", "licenseNumber", "hasVehicle", "vehicleType", "proof",
        "backgroundCheck", "volunteeredBefore", "firstAid", "mobilityHelp"
    ]
    if not data or not all(field in data for field in required_fields):
        print("Missing required fields")
        return jsonify({"message": "Missing required fields"}), 400

    row = {
        "emailaddress": data["email"],
        "password": data["password"],  
        "fullname": data["fullName"],
        "dateofbirth": data["dob"],
        "phone": data["phone"],
        "address": data["address"],
        "hasdriverlicense": data["hasLicense"],
        "licensenumber": data["licenseNumber"],
        "hasvehicle": data["hasVehicle"],
        "vehicletype": data["vehicleType"],
        "proofofinsurance": data["proof"],
        "backgroundcheckconsent": data["backgroundCheck"],
        "volunteeredbefore": data["volunteeredBefore"],
        "firstaidtrained": data["firstAid"],
        "mobilityassistance": data["mobilityHelp"]
    }
    print("shakthi")

    try:
        volunteer_table = boto3.resource('dynamodb').Table('volunteerinfo')

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
    rider_table = dynamodb.Table('riderinfo')
    volunteer_table = dynamodb.Table('volunteerinfo')

    # Check in rider-info table (senior)
    try:
        response = rider_table.get_item(Key={"emailaddress": email})
        senior = response.get("Item")
        if senior:
            if senior.get("password") == password:
                return jsonify({
                    "message": "success",
                    "accountType": "senior",
                    "userInfo": senior
                }), 200
            else:
                return jsonify({"message": "Incorrect password"}), 401
    except Exception as e:
        print(f"Error querying rider-info: {e}")

    # Check in volunteers-info table
    try:
        volunteer_table = boto3.resource('dynamodb').Table('volunteerinfo')
        response = volunteer_table.get_item(Key={"emailaddress": email})
        volunteer = response.get("Item")
        if volunteer:
            if volunteer.get("password") == password:
                return jsonify({
                    "message": "success",
                    "accountType": "volunteer",
                    "userInfo": volunteer
                }), 200
            else:
                return jsonify({"message": "Incorrect password"}), 401
    except Exception as e:
        print(f"Error querying volunteers-info: {e}")

    return jsonify({"message": "Account does not exist"}), 404

@app.route("/requestRide", methods=["POST"])
def request_ride():
    data = request.get_json()
    try: 
        print(data)

        required_fields = ["currentLocation", "dropoffLocation", "pickupDateTime", "userEmailAddress"]
        if not data or not all(field in data for field in required_fields):
            print("Line 210")
            return jsonify({"message": "Missing required fields"}), 400

        pickup_datetime = data["pickupDateTime"]
        print("Pickup date and time:", pickup_datetime)

        ride_row = {
            "id": str(uuid.uuid4()),  # Unique ride id
            "currentlocation": data["currentLocation"],
            "dropofflocation": data["dropoffLocation"],
            "pickupDateTime": pickup_datetime,
            "userEmailAddress": data["userEmailAddress"],
            "acceptedby": "",  # New attribute for accepted volunteer, initially empty
            "status": "requested"  # Set status to "requested" when ride is created
        }
        print(ride_row)
        print("Ride row to be saved:", ride_row)
    
        ride_table = dynamodb.Table('rideinfo')  # Use the shared resource
        response = ride_table.put_item(Item=ride_row)
        print("DynamoDB put_item response:", response)

        # --- Notify all volunteers ---
        volunteer_table = dynamodb.Table('volunteerinfo')
        volunteer_emails = []
        scan_kwargs = {}
        done = False
        start_key = None

        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = volunteer_table.scan(ProjectionExpression="emailaddress")
            volunteer_emails.extend([item["emailaddress"] for item in response.get("Items", []) if "emailaddress" in item])
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None

        print("Volunteer emails:", volunteer_emails)

        # Email details
        sender_email = "vkalpsm@gmail.com"
        app_password = "wkmu kctm vpje coib"
        subject = "SeniorGo: New Ride Request"
        body = (
            f"A senior has requested a ride.\n\n"
            f"Current Location: {data['currentLocation']}\n"
            f"Dropoff Location: {data['dropoffLocation']}\n"
            f"Pickup DateTime: {pickup_datetime}\n"
            f"Senior Email: {data['userEmailAddress']}\n\n"
            f"Please log in to the SeniorGo platform for more details."
        )

        for volunteer_email in volunteer_emails:
            try:
                msg = MIMEMultipart()
                msg["From"] = sender_email
                msg["To"] = volunteer_email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))

                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(sender_email, app_password)
                    server.send_message(msg)
                print(f"✅ Email sent to {volunteer_email}")
            except Exception as e:
                print(f"Failed to send email to {volunteer_email}: {e}")

        return jsonify({"message": "Ride request saved successfully!"}), 200
    except Exception as e:
        print(f"Error saving ride request: {e}")
        return jsonify({"message": f"Failed to save ride request: {str(e)}"}), 500

@app.route("/activeRequests", methods=["GET"])
def active_requests():
    try:
        print("Fetching active ride requests...")
        ride_table = dynamodb.Table('rideinfo')
        response = ride_table.scan()
        items = response.get("Items", [])
        active_requests = []
        for item in items:
            # Only include rides that are not accepted
            if item.get("status", "") != "Accepted":
                ride = {
                    "id": item.get("id", ""),
                    "currentlocation": item.get("currentlocation", ""),
                    "dropofflocation": item.get("dropofflocation", ""),
                    "pickupDateTime": item.get("pickupDateTime", ""),
                    "userEmailAddress": item.get("userEmailAddress", ""),
                    "acceptedby": item.get("acceptedby", ""),
                    "status": item.get("status", "")
                }
                active_requests.append(ride)
        print(f"Active requests found: {len(active_requests)}")
        return jsonify({"activeRequests": active_requests}), 200
    except Exception as e:
        print(f"Error fetching active ride requests: {e}")
        return jsonify({"message": f"Failed to fetch active ride requests: {str(e)}"}), 500

@app.route("/acceptRequests", methods=["POST"])
def accept_requests():
    data = request.get_json()
    try:
        print("Received data for acceptRequests:", data)  # Add this line
        ride_id = data.get("id")
        volunteer_email = data.get("emailaddress")
        if not ride_id or not volunteer_email:
            return jsonify({"message": "Missing ride id or volunteer email"}), 400

        ride_table = dynamodb.Table('rideinfo')
        print(f"Accepted by volunteer: {volunteer_email}")
        response = ride_table.update_item(
            Key={"id": ride_id},
            UpdateExpression="SET #status = :accepted, #acceptedby = :vol_email",
            ExpressionAttributeNames={
                "#status": "status",
                "#acceptedby": "acceptedby"
            },
            ExpressionAttributeValues={
                ":accepted": "Accepted",
                ":vol_email": volunteer_email
            },
            ReturnValues="UPDATED_NEW"
        )
        print(f"Ride {ride_id} accepted by {volunteer_email}. Update response: {response}")
        return jsonify({"message": "Ride accepted successfully!"}, 200)
    except Exception as e:
        print(f"Error accepting ride request: {e}")
        return jsonify({"message": f"Failed to accept ride request: {str(e)}"}), 500

@app.route("/acceptedRequests", methods=["POST"])
def accepted_requests():
    data = request.get_json()
    try:
        print("Fetching accepted ride requests...")
        emailaddress = data.get("emailaddress")
        print("The email address is:", emailaddress)
        ride_table = dynamodb.Table('rideinfo')
        response = ride_table.scan()
        items = response.get("Items", [])
        accepted_requests = []
        for item in items:
            print(f"Checking item: status={item.get('status', '')}, acceptedby={item.get('acceptedby', '')}")
            if (
                item.get("status", "") == "Accepted"
                and item.get("acceptedby", "") == emailaddress
            ):
                ride = {
                    "id": item.get("id", ""),
                    "currentlocation": item.get("currentlocation", ""),
                    "dropofflocation": item.get("dropofflocation", ""),
                    "pickupDateTime": item.get("pickupDateTime", ""),
                    "userEmailAddress": item.get("userEmailAddress", ""),
                    "acceptedby": item.get("acceptedby", ""),
                    "status": item.get("status", "")
                }
                accepted_requests.append(ride)
        print(f"Accepted requests found: {len(accepted_requests)}")
        return jsonify({"acceptedRequests": accepted_requests}), 200
    except Exception as e:
        print(f"Error fetching accepted ride requests: {e}")
        return jsonify({"message": f"Failed to fetch accepted ride requests: {str(e)}"}), 500

@app.route("/currentRides", methods=["POST"])
def current_rides():
    data = request.get_json()
    try:
        print("Fetching ride status for user:", data)
        user_email = data.get("emailaddress")
        print("User email address:", user_email)
        if not user_email:
            return jsonify({"message": "Missing emailaddress"}), 400
        print("User email address:", user_email)
        ride_table = dynamodb.Table('rideinfo')
        response = ride_table.scan()
        items = response.get("Items", [])
        rides = []
        for item in items:
            if item.get("userEmailAddress", "") == user_email:
                rides.append({
                    "id": item.get("id", ""),
                    "status": item.get("status", ""),
                    "currentlocation": item.get("currentlocation", ""),
                    "dropofflocation": item.get("dropofflocation", ""),
                    "acceptedby": item.get("acceptedby", ""),
                    "pickupDateTime": item.get("pickupDateTime", "")
                })
        print(f"Current rides found: {len(rides)}")
        return jsonify({"currentRides": rides}), 200
    except Exception as e:
        print(f"Error fetching ride status: {e}")
        return jsonify({"message": f"Failed to fetch ride status: {str(e)}"}), 500

@app.route("/forgotPassword", methods=["POST"])
def forgot_password():
    data = request.get_json()
    user_email = data.get("emailaddress")
    if not user_email:
        return jsonify({"message": "Missing emailaddress"}), 400

    try:
        code = "{:06d}".format(random.randint(0, 999999))
        sender_email = "vkalpsm@gmail.com"
        receiver_email = user_email
        app_password = "wkmu kctm vpje coib"
        subject = "SeniorGo Password Reset Code"
        body = f"Your password reset code is: {code}"

        rider_table = dynamodb.Table('riderinfo')
        volunteer_table = dynamodb.Table('volunteerinfo')

        # Check in riderinfo
        rider_resp = rider_table.get_item(Key={"emailaddress": user_email})
        if "Item" in rider_resp and rider_resp["Item"]:
            rider_table.update_item(
                Key={"emailaddress": user_email},
                UpdateExpression="SET #pwd = :pwd, #reset = :reset",
                ExpressionAttributeNames={
                    "#pwd": "password",
                    "#reset": "resetPassword"
                },
                ExpressionAttributeValues={
                    ":pwd": code,
                    ":reset": True
                }
            )
            # Send email
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = receiver_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, app_password)
                server.send_message(msg)
                print(f"✅ Password reset code sent to {receiver_email}")
            return jsonify({"message": "Password reset code sent", "code": code}), 200

        # Check in volunteerinfo
        volunteer_resp = volunteer_table.get_item(Key={"emailaddress": user_email})
        if "Item" in volunteer_resp and volunteer_resp["Item"]:
            volunteer_table.update_item(
                Key={"emailaddress": user_email},
                UpdateExpression="SET #pwd = :pwd, #reset = :reset",
                ExpressionAttributeNames={
                    "#pwd": "password",
                    "#reset": "resetPassword"
                },
                ExpressionAttributeValues={
                    ":pwd": code,
                    ":reset": True
                }
            )
            # Send email
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = receiver_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, app_password)
                server.send_message(msg)
                print(f"✅ Password reset code sent to {receiver_email}")
            return jsonify({"message": "Password reset code sent", "code": code}), 200

        # Not found in either
        return jsonify({"message": "Email address not found"}), 404

    except Exception as e:
        print(f"Error in forgotPassword: {e}")
        return jsonify({"message": f"Error processing request: {str(e)}"}), 500

@app.route("/changePassword", methods=["POST"])
def change_password():
    data = request.get_json()
    print(data)
    email = data.get("emailaddress")
    old_password = data.get("oldpassword")
    new_password = data.get("newpassword")
    if not email or not old_password or not new_password:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        rider_table = dynamodb.Table('riderinfo')
        volunteer_table = dynamodb.Table('volunteerinfo')

        # Check in riderinfo
        rider_resp = rider_table.get_item(Key={"emailaddress": email})
        rider = rider_resp.get("Item")
        if rider:
            if rider.get("password") != old_password:
                return jsonify({"message": "Old password is incorrect"}), 401
            rider_table.update_item(
                Key={"emailaddress": email},
                UpdateExpression="SET #pwd = :pwd, #reset = :reset",
                ExpressionAttributeNames={
                    "#pwd": "password",
                    "#reset": "resetPassword"
                },
                ExpressionAttributeValues={
                    ":pwd": new_password,
                    ":reset": False
                }
            )
            return jsonify({"message": "Password changed successfully"}), 200

        # Check in volunteerinfo
        volunteer_resp = volunteer_table.get_item(Key={"emailaddress": email})
        volunteer = volunteer_resp.get("Item")
        if volunteer:
            if volunteer.get("password") != old_password:
                return jsonify({"message": "Old password is incorrect"}), 401
            volunteer_table.update_item(
                Key={"emailaddress": email},
                UpdateExpression="SET #pwd = :pwd, #reset = :reset",
                ExpressionAttributeNames={
                    "#pwd": "password",
                    "#reset": "resetPassword"
                },
                ExpressionAttributeValues={
                    ":pwd": new_password,
                    ":reset": False
                }
            )
            return jsonify({"message": "Password changed successfully"}), 200

        return jsonify({"message": "Email address not found"}), 404

    except Exception as e:
        print(f"Error in changePassword: {e}")
        return jsonify({"message": f"Error processing request: {str(e)}"}), 500

    
if __name__ == "__main__":
   app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

