import os
from time import strftime, sleep
import boto3
from botocore.exceptions import ClientError



def main():
    VERSION_LABEL = strftime("%Y%m%d%H%M%S")
    BUCKET_KEY = os.getenv('S3_ARTIFACTS_OBJECT')
    S3_ARTIFACTS_BUCKET=os.getenv('S3_ARTIFACTS_BUCKET')
    BLUE_ENV_NAME = os.getenv("BLUE_ENV_NAME")
    BEANSTALK_APP_NAME = os.getenv("BEANSTALK_APP_NAME")

    try:
        beanstalkclient = boto3.client('elasticbeanstalk')
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False

    if not create_new_version(beanstalkclient, VERSION_LABEL, BUCKET_KEY, S3_ARTIFACTS_BUCKET, BEANSTALK_APP_NAME):
        raise Exception("Create new version.")
    
    wait_until_env_be_ready(beanstalkclient, BLUE_ENV_NAME)
    # Wait for the new version to be consistent before deploying
    if not deploy_new_version(beanstalkclient, BEANSTALK_APP_NAME, BLUE_ENV_NAME, VERSION_LABEL):
        raise Exception("Failed to deploy new version.")



def create_new_version(beanstalkclient, VERSION_LABEL, BUCKET_KEY, S3_ARTIFACTS_BUCKET, BEANSTALK_APP_NAME):
    """
    Creates a new application version in AWS Elastic Beanstalk
    """

    try:
        response = beanstalkclient.create_application_version(
            ApplicationName=BEANSTALK_APP_NAME,
            VersionLabel=VERSION_LABEL,
            Description='New release azure devops',
            SourceBundle={
                'S3Bucket': S3_ARTIFACTS_BUCKET,
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

def deploy_new_version(beanstalkclient, BEANSTALK_APP_NAME, BLUE_ENV_NAME, VERSION_LABEL):
    """
    Deploy a new version to AWS Elastic Beanstalk
    """
    try:
        response = beanstalkclient.update_environment(
            ApplicationName=BEANSTALK_APP_NAME,
            EnvironmentName=BLUE_ENV_NAME,
            VersionLabel=VERSION_LABEL,
        )
    except ClientError as err:
        print("Failed to update environment.\n" + str(err))
        return False

    print(response)
    return True

def wait_until_env_be_ready(beanstalkclient, ENV_NAME):
  env_info = get_env_info(beanstalkclient, ENV_NAME)
  while env_info["Environments"][0]["Status"] != "Ready":
    print("Waiting the blue environment be Ready!")
    sleep(5)
    env_info = get_env_info(beanstalkclient, ENV_NAME)
  return "Env is ready"


def get_env_info(beanstalkclient, env_name):
  response = beanstalkclient.describe_environments(
  EnvironmentNames=[
      env_name
  ])
  return response

if __name__ == "__main__":
    main()