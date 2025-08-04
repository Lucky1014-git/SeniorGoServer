import boto3
import uuid
from datetime import datetime

def main():
    # Connect to DynamoDB (default region from environment or config)
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('adminuser')

    # Example admin user item
    admin_item = {
        "userid": "lucky123",
        "email": "vkalps@gmail.com",
        "name": "Lakshitha Vengadeswaran",
        "password": "password1",  # In production, use a hashed password!
        "phone": "737-757-6812",  # Optional field
        "createdat": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current date and time

    }

    # Insert the item
    try:
        table.put_item(Item=admin_item)
        print("Admin user inserted successfully:")
        print(admin_item)
    except Exception as e:
        print(f"Error inserting admin user: {e}")

if __name__ == "__main__":
    main()
