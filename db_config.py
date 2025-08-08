# db_config.py
import boto3

# Initialize DynamoDB resource once
dynamodb = boto3.resource('dynamodb')  # Set your region

# Table references
rider_table = dynamodb.Table('riderinfo')
volunteer_table = dynamodb.Table('volunteerinfo')
group_table = dynamodb.Table('groupinfo')
admin_table = dynamodb.Table('adminuser')
