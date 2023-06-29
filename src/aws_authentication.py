import boto3
import os


def get_boto_client():
    print("AUTH_METHOD: ")
    if os.getenv('AUTH_METHOD') == 'SSO':
        boto3.setup_default_session(profile_name=os.getenv('SSO_PROFILE'))
        print("\t -> SSO Authentication\n")
    else:
        print("\t -> AWS KEYS authentication\n")
    return boto3
