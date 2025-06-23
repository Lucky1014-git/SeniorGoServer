from flask import Flask, request, jsonify
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


app = Flask(__name__)
excel_file = "senior_signups.xlsx"

@app.route("/")
def home():
    return "This is the home page of the SeniorGo server."

@app.route("/signUpSenior", methods=["POST"])
def sign_up_senior():
    data = request.get_json()
    print(data)
    # Basic validation
    required_fields = ["fullName", "phone", "email", "password", "confirmPassword", "address", "agree"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    # Create row to append
    row = {
        "Full Name": data["fullName"],
        "Phone": data["phone"],
        "Email": data["email"],
        "Password": data["password"],  # ⚠️ Only for testing – do NOT store plain passwords in production!
        "Confirm Password": data["confirmPassword"],
        "Address": data["address"],
        "Agreed To Terms": data["agree"]
    }

    try:
        # Load existing Excel or create new
        if os.path.exists(excel_file):
            df = pd.read_excel(excel_file)
        else:
            df = pd.DataFrame(columns=row.keys())

        # Append and save
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_excel(excel_file, index=False)
        sender_email = "vkalpsm@gmail.com"
        receiver_email = data["email"]
        app_password = "wkmu kctm vpje coib"  # Use App Password, NOT your Gmail login password

        # Email content
        subject = "Account Signup Confirmation"
        body = "Hi there,\n\nYou have successfully signed up for SeniorGo! Thank you for joining our community.\n\nBest regards,\nSeniorGo Team"

        # Set up MIME
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send via Gmail SMTP
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()  # Secure the connection
                server.login(sender_email, app_password)
                server.send_message(msg)
                print("✅ Email sent successfully!")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")


        return jsonify({"message": "Signup saved successfully!"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": f"Failed to save data: {str(e)}"}), 500
    

@app.route("/signUpVolunteer", methods=["POST"])
def sign_up_volunteer():
    data = request.get_json()
    print(data)

    # Required fields
    required_fields = [
        "fullName", "dob", "email", "phone", "address",
        "hasLicense", "licenseNumber", "hasVehicle", "vehicleType", "proof",
        "backgroundCheck", "volunteeredBefore", "firstAid", "mobilityHelp"
    ]

    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    # Create the row for Excel
    row = {
        "Full Name": data["fullName"],
        "Date of Birth": data["dob"],
        "Email": data["email"],
        "Phone": data["phone"],
        "Address": data["address"],
        "Has Driver's License": data["hasLicense"],
        "License Number": data["licenseNumber"],
        "Has Vehicle": data["hasVehicle"],
        "Vehicle Type": data["vehicleType"],
        "Proof of Insurance": data["proof"],
        "Background Check Consent": data["backgroundCheck"],
        "Volunteered Before": data["volunteeredBefore"],
        "First Aid/CPR Trained": data["firstAid"],
        "Comfortable with Mobility Assistance": data["mobilityHelp"]
    }

    try:
        excel_file = "volunteers.xlsx"

        # Load existing or create new Excel file
        if os.path.exists(excel_file):
            df = pd.read_excel(excel_file)
        else:
            df = pd.DataFrame(columns=row.keys())

        # Append new entry
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_excel(excel_file, index=False)
        sender_email = "vkalpsm@gmail.com"
        receiver_email = data["email"]
        app_password = "wkmu kctm vpje coib"  # Use App Password, NOT your Gmail login password

        # Email content
        subject = "Account Signup Confirmation"
        body = "Hi there,\n\nYou have successfully signed up for SeniorGo! We will get back to you shortly!\n\nBest regards,\nSeniorGo Team"

        # Set up MIME
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send via Gmail SMTP
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()  # Secure the connection
                server.login(sender_email, app_password)
                server.send_message(msg)
                print("✅ Email sent successfully!")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")

        return jsonify({"message": "Volunteer signup saved successfully!"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": f"Failed to save data: {str(e)}"}), 500

    # Email account credentials


    
if __name__ == "__main__":
   app.run(debug=True, host='10.0.0.24', port=5000)  # Change host and port as needed


