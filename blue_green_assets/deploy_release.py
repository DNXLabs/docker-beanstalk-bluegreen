import os
from time import strftime, sleep
import boto3
from botocore.exceptions import ClientError



def main():
    VERSION_LABEL = strftime("%Y%m%d%H%M%S")
    BUCKET_KEY = os.getenv('ENV') + '/deployment/DeploymentPackage.zip'
    ARTIFACTS_S3_BUCKET=os.getenv('ARTIFACTS_S3_BUCKET')
    BLUE_ENV_NAME = os.getenv("BLUE_ENV_NAME")
    BEANSTALK_APP_NAME = os.getenv("BEANSTALK_APP_NAME")

    if not create_new_version(VERSION_LABEL, BUCKET_KEY, ARTIFACTS_S3_BUCKET, BEANSTALK_APP_NAME):
        raise Exception("Create new version.")
    # Wait for the new version to be consistent before deploying
    sleep(5)
    if not deploy_new_version(BEANSTALK_APP_NAME, BLUE_ENV_NAME, VERSION_LABEL):
        raise Exception("Failed to deploy new version.")



def create_new_version(VERSION_LABEL, BUCKET_KEY, ARTIFACTS_S3_BUCKET, BEANSTALK_APP_NAME):
    """
    Creates a new application version in AWS Elastic Beanstalk
    """
    try:
        client = boto3.client('elasticbeanstalk')
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False

    try:
        response = client.create_application_version(
            ApplicationName=BEANSTALK_APP_NAME,
            VersionLabel=VERSION_LABEL,
            Description='New release azure devops',
            SourceBundle={
                'S3Bucket': ARTIFACTS_S3_BUCKET,
                'S3Key': BUCKET_KEY
            },
            Process=True
        )
    except ClientError as err:
        print("Failed to create application version.\n" + str(err))
        return False

    try:
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            print(response)
            return False
    except (KeyError, TypeError) as err:
        print(str(err))
        return False

def deploy_new_version(BEANSTALK_APP_NAME, BLUE_ENV_NAME, VERSION_LABEL):
    """
    Deploy a new version to AWS Elastic Beanstalk
    """
    try:
        client = boto3.client('elasticbeanstalk')
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False

    try:
        response = client.update_environment(
            ApplicationName=BEANSTALK_APP_NAME,
            EnvironmentName=BLUE_ENV_NAME,
            VersionLabel=VERSION_LABEL,
        )
    except ClientError as err:
        print("Failed to update environment.\n" + str(err))
        return False

    print(response)
    return True

if __name__ == "__main__":
    main()