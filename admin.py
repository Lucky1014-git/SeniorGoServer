from flask import request, jsonify
from db_config import rider_table, volunteer_table,group_table, admin_table
import boto3
import random

# Function: admin_login
# Description: Admin login handler function that authenticates an admin user by userid and password.
# Called from main.py's /adminLogin endpoint.
# Parameters: request_data - JSON data containing userid and password
# Returns: JSON response with success/error message
# Error: Returns 400 for missing fields, 401 for invalid credentials, 500 for server errors.
def admin_login(request_data):
    print("Admin login endpoint called")
    data = request_data
    userid = data.get("userId")
    password = data.get("password")
    if not userid or not password:
        return jsonify({"message": "Missing userid or password"}), 400

    try:
        print(f"Attempting admin login for user: {userid}")
        resp = admin_table.get_item(Key={"userid": userid})
        admin = resp.get("Item")
        if admin and admin.get("password") == password:
            return jsonify({"message": "success"}), 200
        else:
            return jsonify({"message": "Invalid userid or password"}), 401
    except Exception as e:
        print(f"Error in adminLogin: {e}")
        return jsonify({"message": f"Error processing request: {str(e)}"}), 500


# Function: create_group
# Description: Create group handler function that allows an admin to create a new group.
# Called from main.py's /createGroup endpoint.
# Parameters: request_data - JSON data containing group details
# Returns: JSON response with success message and group details
# Error: Returns 400 for missing fields, 500 for groupcode generation or database errors.
def create_group(request_data):
    data = request_data
    print("Received data for createGroup:", data)
    required_fields = ["emailaddress", "phonenumber", "groupname", "location", "grouptype"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    # Generate 6-digit random unique id (numeric)
    groupid = "{:06d}".format(random.randint(0, 999999))

    # Generate unique 6-character alphabetical groupcode (unique for each group)
    max_attempts = 10
    for _ in range(max_attempts):
        groupcode = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=6))
        # Check uniqueness for groupcode only
        response = group_table.scan(
            FilterExpression="groupcode = :code",
            ExpressionAttributeValues={
                ":code": groupcode
            }
        )
        if not response.get("Items"):
            break
    else:
        return jsonify({"message": "Failed to generate unique groupcode"}), 500

    group_row = {
        "groupid": groupid,
        "groupcode": groupcode,
        "emailaddress": data["emailaddress"],
        "phonenumber": data["phonenumber"],
        "groupname": data["groupname"],
        "location": data["location"],
        "grouptype": data["grouptype"]
    }

    try:
        group_table.put_item(Item=group_row)
        return jsonify({
            "message": "Group created successfully",
            "groupid": groupid,
            "groupcode": groupcode
        }), 200
    except Exception as e:
        print(f"Error creating group: {e}")
        return jsonify({"message": f"Failed to create group: {str(e)}"}), 500
