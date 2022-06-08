import boto3
import os

def get_boto_client():
        print("AUTH_METHOD: " +  str(os.getenv('AUTH_METHOD')))
        if os.getenv('AUTH_METHOD') == 'SSO':
            boto3.setup_default_session(profile_name=os.getenv('SSO_PROFILE'))
            print("SSO Authentication") 
        else:
            print("AWS KEYS authentication")
        return boto3