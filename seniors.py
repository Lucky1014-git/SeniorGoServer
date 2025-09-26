from flask import request, jsonify
from db_config import rider_table, volunteer_table, group_table,ride_info_table
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid
from botocore.exceptions import ClientError



# Function: sign_up_senior
# Description: Senior signup handler function that registers a new senior user. Validates groupcode, prevents duplicate emails, and sends a confirmation email upon successful signup.
# Called from main.py's /signUpSenior endpoint.
# Parameters: request_data - JSON data containing senior signup details
# Returns: JSON response with signup result
# Error: Returns 400 for missing fields or invalid groupcode, 500 for server/email errors, 400 for duplicate email.
def sign_up_senior(request_data):
    data = request_data
    print(data)
    required_fields = ["fullName", "phone", "email", "password", "confirmPassword", "address", "agree", "groupCode"]
    if not data or not all(field in data for field in required_fields):
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
        "fullname": data["fullName"],
        "phone": data["phone"],
        "password": data["password"],  # ⚠️ Hash in production
        "address": data["address"],
        "groupcode": groupcode_db
    }

    try:
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



# Function: request_ride
# Description: Request ride handler function that allows a senior to request a ride. Saves ride details, notifies all volunteers via email, and stores ride in rideinfo table.
# Called from main.py's /requestRide endpoint.
# Parameters: request_data - JSON data containing ride request details
# Returns: JSON response with request result
# Error: Returns 400 for missing fields, 500 for server/email errors, 400 if user/groupcode not found.
def request_ride(request_data):
    data = request_data
    try: 
        print(data)

        required_fields = ["currentLocation", "dropoffLocation", "pickupDateTime", "userEmailAddress"]
        if not data or not all(field in data for field in required_fields):
            print("Line 210")
            return jsonify({"message": "Missing required fields"}), 400

        pickup_datetime = data["pickupDateTime"]
        print("Pickup date and time:", pickup_datetime)

        # Get groupcode from riderinfo table
        rider_resp = rider_table.get_item(Key={"emailaddress": data["userEmailAddress"]})
        rider = rider_resp.get("Item")
        if not rider or "groupcode" not in rider:
            return jsonify({"message": "User not found or missing groupcode"}), 400
        groupcode = rider["groupcode"]

        ride_row = {
            "id": str(uuid.uuid4()),  # Unique ride id
            "currentlocation": data["currentLocation"],
            "dropofflocation": data["dropoffLocation"],
            "pickupDateTime": pickup_datetime,
            "userEmailAddress": data["userEmailAddress"],
            "acceptedby": "",
            "status": "requested",
            "groupcode": groupcode  # Store groupcode from riderinfo
        }
        print(ride_row)
        print("Ride row to be saved:", ride_row)
    
        ride_table = group_table.meta.client.Table('rideinfo') if hasattr(group_table.meta.client, 'Table') else None
        if not ride_table:
            import boto3
            ride_table = boto3.resource('dynamodb').Table('rideinfo')
        response = ride_table.put_item(Item=ride_row)
        print("DynamoDB put_item response:", response)

        # --- Notify all volunteers ---
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

# Function: current_rides
# Description: Current rides handler function that returns all current rides for a senior user, filtered by email and groupcode. Used to display ride status/history to the user.
# Called from main.py's /currentRides endpoint.
# Parameters: request_data - JSON data containing email address
# Returns: JSON response with current rides list
# Error: Returns 400 for missing emailaddress or user/groupcode not found, 500 for server errors.
def current_rides(request_data):
    data = request_data
    try:
        print("Fetching ride status for user:", data)
        user_email = data.get("emailaddress")
        print("User email address:", user_email)
        if not user_email:
            return jsonify({"message": "Missing emailaddress"}), 400

        rider_resp = rider_table.get_item(Key={"emailaddress": user_email})
        rider = rider_resp.get("Item")
        if not rider or "groupcode" not in rider:
            return jsonify({"message": "User not found or missing groupcode"}), 400
        groupcode = rider["groupcode"]

        response = ride_info_table.scan()
        items = response.get("Items", [])
        rides = []
        for item in items:
            if (
                item.get("userEmailAddress", "") == user_email
                and item.get("groupcode", "") == groupcode
                and item.get("status", "") != "canceled"
            ):
                pickup_datetime = item.get("pickupDateTime", "")
                
                # Extract day of the week from pickupDateTime
                day = ""
                if pickup_datetime:
                    try:
                        from datetime import datetime
                        # Parse the ISO format datetime string
                        dt = datetime.fromisoformat(pickup_datetime.replace('Z', '+00:00'))
                        day = dt.strftime("%A")  # Full day name (e.g., "Monday", "Tuesday")
                    except Exception as e:
                        print(f"Error parsing datetime {pickup_datetime}: {e}")
                        day = "Unknown"
                
                rides.append({
                    "id": item.get("id", ""),
                    "status": item.get("status", ""),
                    "currentlocation": item.get("currentlocation", ""),
                    "dropofflocation": item.get("dropofflocation", ""),
                    "acceptedby": item.get("acceptedby", ""),
                    "pickupDateTime": pickup_datetime,
                    "day": day
                })
        
        # Sort rides by pickupDateTime (earliest first)
        rides.sort(key=lambda ride: ride.get("pickupDateTime", ""))
        
        print(f"Current rides found: {len(rides)}")
        return jsonify({"currentRides": rides}), 200
    except Exception as e:
        print(f"Error fetching ride status: {e}")
        return jsonify({"message": f"Failed to fetch ride status: {str(e)}"}), 500

# Function: request_recurring_ride
# Description: Request recurring ride handler function that creates multiple ride records based on weekly schedule between start and end dates.
# Called from main.py's /requestRecurringRide endpoint.
# Parameters: request_data - JSON data containing recurring ride request details
# Returns: JSON response with creation result and count of rides created
# Error: Returns 400 for missing fields or invalid user/groupcode, 500 for server errors.
def request_recurring_ride(request_data):
    from datetime import datetime, timedelta
    import boto3
    
    data = request_data
    try:
        print("Recurring ride request data:", data)

        required_fields = ["currentLocation", "dropoffLocation", "startDate", "endDate", "weeklySchedule", "userEmailAddress"]
        if not data or not all(field in data for field in required_fields):
            return jsonify({"message": "Missing required fields"}), 400

        # Get groupcode from riderinfo table
        rider_resp = rider_table.get_item(Key={"emailaddress": data["userEmailAddress"]})
        rider = rider_resp.get("Item")
        if not rider or "groupcode" not in rider:
            return jsonify({"message": "User not found or missing groupcode"}), 400
        groupcode = rider["groupcode"]

        # Parse dates
        start_date = datetime.fromisoformat(data["startDate"].replace('Z', '+00:00')).date()
        end_date = datetime.fromisoformat(data["endDate"].replace('Z', '+00:00')).date()
        
        # Day name to weekday mapping
        day_mapping = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        
        # Build array of ride records
        rides_to_create = []
        current_date = start_date
        
        while current_date <= end_date:
            current_weekday = current_date.weekday()
            
            # Check each day in weeklySchedule
            for day_name, schedule_info in data["weeklySchedule"].items():
                if schedule_info.get("enabled", False) and day_mapping.get(day_name) == current_weekday:
                    # Create pickup datetime by combining date and time
                    pickup_time = schedule_info.get("time", "09:00")
                    pickup_datetime = f"{current_date}T{pickup_time}:00.000Z"
                    
                    ride_record = {
                        "id": str(uuid.uuid4()),
                        "acceptedby": None,
                        "currentlocation": data["currentLocation"],
                        "dropofflocation": data["dropoffLocation"],
                        "groupcode": groupcode,
                        "pickupDateTime": pickup_datetime,
                        "status": "requested",
                        "userEmailAddress": data["userEmailAddress"]
                    }
                    rides_to_create.append(ride_record)
            
            current_date += timedelta(days=1)
        
        # Insert all rides into rideinfo table
        ride_table = boto3.resource('dynamodb').Table('rideinfo')
        
        for ride in rides_to_create:
            ride_table.put_item(Item=ride)
            print(f"Created ride for {ride['pickupDateTime']}")
        
        return jsonify({
            "message": f"Recurring rides created successfully!",
            "ridesCreated": len(rides_to_create),
            "rides": rides_to_create
        }), 200
        
    except Exception as e:
        print(f"Error creating recurring rides: {e}")
        return jsonify({"message": f"Failed to create recurring rides: {str(e)}"}), 500

# Function: cancel_ride
# Description: Cancel ride handler function that updates a ride's status to "canceled" based on ride ID and user verification.
# Called from main.py's /cancelRide endpoint.
# Parameters: request_data - JSON data containing rideId and emailaddress
# Returns: JSON response with cancellation result
# Error: Returns 400 for missing fields, 404 if ride not found or unauthorized, 500 for server errors.
def cancel_ride(request_data):
    data = request_data
    try:
        print("Cancel ride request data:", data)

        required_fields = ["rideId", "emailaddress"]
        if not data or not all(field in data for field in required_fields):
            return jsonify({"message": "Missing required fields"}), 400

        ride_id = data["rideId"]
        user_email = data["emailaddress"]

        # Get the ride from rideinfo table
        ride_resp = ride_info_table.get_item(Key={"id": ride_id})
        ride = ride_resp.get("Item")
        
        if not ride:
            return jsonify({"message": "Ride not found"}), 404

        # Verify that the user requesting cancellation is the owner of the ride
        if ride.get("userEmailAddress", "") != user_email:
            return jsonify({"message": "Unauthorized: You can only cancel your own rides"}), 404

        # Update the ride status to "canceled"
        ride_info_table.update_item(
            Key={"id": ride_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": "canceled"}
        )

        print(f"Ride {ride_id} has been canceled by {user_email}")
        return jsonify({"message": "Ride canceled successfully"}), 200
        
    except Exception as e:
        print(f"Error canceling ride: {e}")
        return jsonify({"message": f"Failed to cancel ride: {str(e)}"}), 500
