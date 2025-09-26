from flask import request, jsonify
from db_config import volunteer_table, group_table
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from botocore.exceptions import ClientError

# Function: sign_up_volunteer
# Description: Volunteer signup handler function that registers a new volunteer user. Validates groupcode, prevents duplicate emails, and sends a confirmation email upon successful signup.
# Called from main.py's /signUpVolunteer endpoint.
# Parameters: request_data - JSON data containing volunteer signup details
# Returns: JSON response with signup result
# Error: Returns 400 for missing fields or invalid groupcode, 500 for server/email errors, 400 for duplicate email.
def sign_up_volunteer(request_data):
    data = request_data
    print("lucky")
    required_fields = [
        "fullName", "dob", "email", "password", "phone", "address",
        "hasLicense", "licenseNumber", "hasVehicle", "vehicleType", "proof",
        "backgroundCheck", "volunteeredBefore", "firstAid", "mobilityHelp", "groupCode"
    ]
    if not data or not all(field in data for field in required_fields):
        print("Missing required fields")
        return jsonify({"message": "Missing required fields"}), 400

    # Validate groupcode
    groupcode = data["groupCode"]
    group_resp = group_table.scan(
        FilterExpression="groupcode = :code",
        ExpressionAttributeValues={":code": groupcode}
    )
    if not group_resp.get("Items"):
        return jsonify({"message": "Invalid groupcode"}), 400

    # Get the actual groupcode from the groupinfo table (ensures correct casing/format)
    groupcode_db = group_resp["Items"][0]["groupcode"]

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
        "mobilityassistance": data["mobilityHelp"],
        "groupcode": groupcode_db  # Store the groupcode from the groupinfo table
    }
    print("shakthi")

    try:
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

# Function: active_requests
# Description: Active requests handler function that returns all active ride requests for a volunteer, filtered by groupcode. Only includes rides not yet accepted.
# Called from main.py's /activeRequests endpoint.
# Parameters: request_data - JSON data containing volunteer email
# Returns: JSON response with active requests list
# Error: Returns 400 for missing emailaddress or volunteer/groupcode not found, 500 for server errors.
def active_requests(request_data):
    data = request_data
    emailaddress = data.get("emailaddress")
    if not emailaddress:
        return jsonify({"message": "Missing emailaddress"}), 400

    try:
        print("Fetching active ride requests...")
        volunteer_resp = volunteer_table.get_item(Key={"emailaddress": emailaddress})
        volunteer = volunteer_resp.get("Item")
        if not volunteer or "groupcode" not in volunteer:
            return jsonify({"message": "Volunteer not found or missing groupcode"}), 400
        groupcode = volunteer["groupcode"]

        import boto3
        ride_table = boto3.resource('dynamodb').Table('rideinfo')
        response = ride_table.scan()
        items = response.get("Items", [])
        active_requests_list = []
        for item in items:
            # Only include rides that are not accepted and match volunteer's groupcode
            if item.get("status", "") != "Accepted" and item.get("groupcode", "") == groupcode:
                ride = {
                    "id": item.get("id", ""),
                    "currentlocation": item.get("currentlocation", ""),
                    "dropofflocation": item.get("dropofflocation", ""),
                    "pickupDateTime": item.get("pickupDateTime", ""),
                    "userEmailAddress": item.get("userEmailAddress", ""),
                    "acceptedby": item.get("acceptedby", ""),
                    "status": item.get("status", "")
                }
                active_requests_list.append(ride)
        print(f"Active requests found: {len(active_requests_list)}")
        return jsonify({"activeRequests": active_requests_list}), 200
    except Exception as e:
        print(f"Error fetching active ride requests: {e}")
        return jsonify({"message": f"Failed to fetch active ride requests: {str(e)}"}), 500

# Function: accept_requests
# Description: Accept requests handler function that allows a volunteer to accept a ride request. Updates ride status and records volunteer email in rideinfo table.
# Called from main.py's /acceptRequests endpoint.
# Parameters: request_data - JSON data containing ride id and volunteer email
# Returns: JSON response with accept result
# Error: Returns 400 for missing ride id or volunteer email, 500 for server errors.
def accept_requests(request_data):
    data = request_data
    try:
        print("Received data for acceptRequests:", data)  # Add this line
        ride_id = data.get("id")
        volunteer_email = data.get("emailaddress")
        if not ride_id or not volunteer_email:
            return jsonify({"message": "Missing ride id or volunteer email"}), 400

        import boto3
        ride_table = boto3.resource('dynamodb').Table('rideinfo')
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

# Function: accepted_requests
# Description: Accepted requests handler function that returns all rides accepted by a volunteer, filtered by groupcode and volunteer email.
# Called from main.py's /acceptedRequests endpoint.
# Parameters: request_data - JSON data containing volunteer email
# Returns: JSON response with accepted requests list
# Error: Returns 400 for missing emailaddress or volunteer/groupcode not found, 500 for server errors.
def accepted_requests(request_data):
    data = request_data
    try:
        print("Fetching accepted ride requests...")
        emailaddress = data.get("emailaddress")
        print("The email address is:", emailaddress)
        
        volunteer_resp = volunteer_table.get_item(Key={"emailaddress": emailaddress})
        volunteer = volunteer_resp.get("Item")
        if not volunteer or "groupcode" not in volunteer:
            return jsonify({"message": "Volunteer not found or missing groupcode"}), 400
        groupcode = volunteer["groupcode"]

        import boto3
        ride_table = boto3.resource('dynamodb').Table('rideinfo')
        response = ride_table.scan()
        items = response.get("Items", [])
        accepted_requests_list = []
        for item in items:
            # Only include rides that are accepted by this volunteer and match groupcode
            if (
                item.get("status", "") == "Accepted"
                and item.get("acceptedby", "") == emailaddress
                and item.get("groupcode", "") == groupcode
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
                accepted_requests_list.append(ride)
        print(f"Accepted requests found: {len(accepted_requests_list)}")
        return jsonify({"acceptedRequests": accepted_requests_list}), 200
    except Exception as e:
        print(f"Error fetching accepted ride requests: {e}")
        return jsonify({"message": f"Failed to fetch accepted ride requests: {str(e)}"}), 500
