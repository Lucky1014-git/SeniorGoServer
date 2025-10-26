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
            # Get group name from groupinfo table
            groupcode = admin.get("groupcode")
            if groupcode:
                group_resp = group_table.scan(
                    FilterExpression="groupcode = :code",
                    ExpressionAttributeValues={":code": groupcode}
                )
                if group_resp.get("Items"):
                    admin["groupname"] = group_resp["Items"][0].get("groupname", "")
            
            response_data = {
                "message": "success",
                "accountType": "admin",
                "userInfo": admin
            }
            print("Admin login response:", response_data)
            return jsonify(response_data), 200
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
    required_fields = ["emailaddress", "groupname", "grouptype", "location", "phonenumber"]
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

# Function: get_all_groups
# Description: Get all groups handler function that fetches all group information from the group info table.
# Called from main.py's /getAllGroups endpoint.
# Parameters: request_data - JSON data (no specific parameters required)
# Returns: JSON response with all groups information
# Error: Returns 500 for server errors.
def get_all_groups(request_data):
    try:
        print("Fetching all groups information...")
        
        # Scan the group table to get all groups
        response = group_table.scan()
        items = response.get("Items", [])
        
        groups_list = []
        for item in items:
            group_info = {
                "groupid": item.get("groupid", ""),
                "groupcode": item.get("groupcode", ""),
                "emailaddress": item.get("emailaddress", ""),
                "phonenumber": item.get("phonenumber", ""),
                "groupname": item.get("groupname", ""),
                "location": item.get("location", ""),
                "grouptype": item.get("grouptype", "")
            }
            groups_list.append(group_info)
        
        print(f"Total groups found: {len(groups_list)}")
        return jsonify({"groups": groups_list}), 200
        
    except Exception as e:
        print(f"Error fetching groups information: {e}")
        return jsonify({"message": f"Failed to fetch groups information: {str(e)}"}), 500

# Function: get_all_group_admin_users
# Description: Get all group admin users handler function that fetches all admin records where role is GROUP_ADMIN.
# Called from main.py's /getAllGroupAdminUsers endpoint.
# Parameters: request_data - JSON data (no specific parameters required)
# Returns: JSON response with all group admin users information
# Error: Returns 500 for server errors.
def get_all_group_admin_users(request_data):
    try:
        print("Fetching all group admin users...")
        
        # Scan the admin table and filter by role = GROUP_ADMIN
        response = admin_table.scan(
            FilterExpression="#role = :role",
            ExpressionAttributeNames={"#role": "role"},
            ExpressionAttributeValues={":role": "GROUP_ADMIN"}
        )
        items = response.get("Items", [])
        
        admin_users_list = []
        for item in items:
            # Get group name from groupinfo table using groupcode
            groupcode = item.get("groupcode", "")
            groupname = ""
            if groupcode:
                try:
                    group_resp = group_table.scan(
                        FilterExpression="groupcode = :code",
                        ExpressionAttributeValues={":code": groupcode}
                    )
                    if group_resp.get("Items"):
                        groupname = group_resp["Items"][0].get("groupname", "")
                except Exception as e:
                    print(f"Error fetching group name for groupcode {groupcode}: {e}")
                    groupname = "Unknown"
            
            admin_user_info = {
                "userid": item.get("userid", ""),
                "createddate": item.get("createddate", ""),
                "email": item.get("email", ""),
                "groupcode": groupcode,
                "groupname": groupname,
                "name": item.get("name", ""),
                "password": item.get("password", ""),
                "phone": item.get("phone", ""),
                "role": item.get("role", "")
            }
            admin_users_list.append(admin_user_info)
        
        print(f"Total group admin users found: {len(admin_users_list)}")
        return jsonify({"groupAdminUsers": admin_users_list}), 200
        
    except Exception as e:
        print(f"Error fetching group admin users: {e}")
        return jsonify({"message": f"Failed to fetch group admin users: {str(e)}"}), 500
