from flask import request, jsonify
from db_config import rider_table, volunteer_table,group_table
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

# Function: update_status_bar
# Description: Update status bar handler function that returns the current status of a ride for a given rideId.
# Called from main.py's /updateStatusBar endpoint.
# Parameters: request_data - JSON data containing rideId
# Returns: JSON response with ride status
# Error: Returns 400 if rideId is missing, 500 if DynamoDB query fails.
def update_status_bar(request_data):
    import boto3
    data = request_data
    ride_id = data.get("rideId")
    if not ride_id:
        return jsonify({"message": "Missing ride id"}), 400
    try:
        dynamodb = boto3.resource('dynamodb')
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

# Function: update_status
# Description: Update status handler function that updates the status of a ride in the rideinfo table.
# Called from main.py's /updateStatus endpoint.
# Parameters: request_data - JSON data containing rideId
# Returns: JSON response with new status
# Error: Returns 400 if rideId is missing, 500 if DynamoDB update fails.
def update_status(request_data):
    from flask import current_app
    import boto3
    data = request_data
    print(f"Received data in updateStatus: {data}")
    ride_id = data.get("rideId")
    print(f"Extracted ride_id: '{ride_id}' (type: {type(ride_id)})")
    if not ride_id:
        ride_id = data.get("id")
        print(f"Fallback ride_id from 'id': '{ride_id}'")
    if not ride_id:
        print("No ride ID found in request data")
        return jsonify({"message": "Missing ride id"}), 400
    try:
        dynamodb = boto3.resource('dynamodb')
        ride_table = dynamodb.Table('rideinfo')
        ride_resp = ride_table.get_item(Key={"id": ride_id})
        current_status = ride_resp.get("Item", {}).get("status", "unknown")
        print(f"Current status for ride {ride_id}: {current_status}")
        if current_status == "Accepted":
            new_status = "volunteerstarted"
        elif current_status == "volunteerstarted":
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

# Function: change_password
# Description: Change password handler function that allows a user (senior or volunteer) to change their password. Checks old password for validation and updates to new password in the respective table.
# Called from main.py's /changePassword endpoint.
# Parameters: request_data - JSON data containing email and passwords
# Returns: JSON response with change result
# Error: Returns 400 for missing fields, 401 for incorrect old password, 404 if email not found, 500 for server errors.
def change_password(request_data):
    data = request_data
    print(data)
    email = data.get("emailaddress")
    old_password = data.get("oldpassword")
    new_password = data.get("newpassword")
    if not email or not old_password or not new_password:
        return jsonify({"message": "Missing required fields"}), 400

    try:
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

# Function: login_user
# Description: Login handler function that authenticates users (senior or volunteer) by email and password. 
# Called from main.py's /login endpoint. Returns account type and user info if successful. Also fetches group name from groupinfo table.
# Parameters: request_data - JSON data containing email and password
# Returns: JSON response with authentication result and user information
# Error: Returns 400 for missing fields, 401 for incorrect password, 404 if account does not exist.
def login_user(request_data):
    data = request_data
    if not data or "email" not in data or "password" not in data:
        return jsonify({"message": "Missing email or password"}), 400

    email = data["email"]
    password = data["password"]
    #rider_table = dynamodb.Table('riderinfo')
    #volunteer_table = dynamodb.Table('volunteerinfo')

    # Check in rider-info table (senior)
    try:
        response = rider_table.get_item(Key={"emailaddress": email})
        senior = response.get("Item")
        if senior:
            if senior.get("password") == password:
                # Get group name from groupinfo table
                groupcode = senior.get("groupcode")
                if groupcode:
                    #group_table = dynamodb.Table('groupinfo')
                    group_resp = group_table.scan(
                        FilterExpression="groupcode = :code",
                        ExpressionAttributeValues={":code": groupcode}
                    )
                    if group_resp.get("Items"):
                        senior["groupname"] = group_resp["Items"][0].get("groupname", "")
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
        response = volunteer_table.get_item(Key={"emailaddress": email})
        volunteer = response.get("Item")
        if volunteer:
            if volunteer.get("password") == password:
                # Get group name from groupinfo table
                groupcode = volunteer.get("groupcode")
                if groupcode:
                    #group_table = dynamodb.Table('groupinfo')
                    group_resp = group_table.scan(
                        FilterExpression="groupcode = :code",
                        ExpressionAttributeValues={":code": groupcode}
                    )
                    if group_resp.get("Items"):
                        volunteer["groupname"] = group_resp["Items"][0].get("groupname", "")
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


# Function: forgot_password
# Description: Forgot password handler function that initiates password reset for a user (senior or volunteer). Generates a 6-digit code, updates password to code, sets resetPassword flag, and sends code via email.
# Called from main.py's /forgotPassword endpoint.
# Parameters: request_data - JSON data containing email address
# Returns: JSON response with reset result and code
# Error: Returns 400 for missing email, 404 if email not found, 500 for email/DynamoDB errors.
def forgot_password(request_data):
    data = request_data
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


    