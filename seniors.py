# ...existing code...
from flask import request, jsonify
from db_config import rider_table, volunteer_table, group_table
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from botocore.exceptions import ClientError



def setup_signup_senior_routes(app):
    @app.route("/signUpSenior", methods=["POST"])
    def sign_up_senior():
        data = request.get_json()
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
