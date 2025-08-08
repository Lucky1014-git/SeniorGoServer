from flask import request, jsonify
from db_config import rider_table, volunteer_table,group_table


def setup_login_routes(app):
    @app.route("/login", methods=["POST"])
    def login():
        data = request.get_json()
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