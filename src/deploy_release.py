from time import strftime, sleep
from botocore.exceptions import ClientError
import os
import swap_environment

def main(BUCKET_KEY, S3_ARTIFACTS_BUCKET, BLUE_ENV_NAME, BEANSTALK_APP_NAME, boto_authenticated_client):
    VERSION_LABEL = strftime("%Y%m%d%H%M%S")

    if "VERSION_LABEL" in os.environ:
        VERSION_LABEL = os.environ['VERSION_LABEL']

    try:
        beanstalkclient = boto_authenticated_client.client('elasticbeanstalk')
    except ClientError as err:
        print("Failed to create boto3 beanstalk client.\n" + str(err))
        return False

    if not create_new_version(beanstalkclient, VERSION_LABEL, BUCKET_KEY, S3_ARTIFACTS_BUCKET, BEANSTALK_APP_NAME):
        raise Exception("Failed to create beanstalk release.")

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

    print("The new version was deployed successfully!")
    print(
        f"New version environment URL: http://{response['EnvironmentName']}.elasticbeanstalk.com")
    return True


def wait_until_env_be_ready(beanstalkclient, ENV_NAME):
    env_info = get_env_info(beanstalkclient, ENV_NAME)
    while env_info["Environments"][0]["Status"] != "Ready":
        print("Waiting the blue environment be Ready!")
        sleep(50)
        env_info = get_env_info(beanstalkclient, ENV_NAME)
    return "Env is ready"


def get_env_info(beanstalkclient, env_name):
    response = beanstalkclient.describe_environments(
        EnvironmentNames=[
            env_name
        ])
    return response

def rollback_release(client, application_name, environment_name):
    try:
        beanstalkclient = client.client('elasticbeanstalk')
    except ClientError as err:
        print("Failed to create boto3 beanstalk client.\n" + str(err))
        return False
    environment_info, client = swap_environment.get_environment_information(
        beanstalkclient, environment_name)

    while environment_info["Environments"][0]["Status"] != "Ready":
        sleep(10)
        environment_info, client = swap_environment.get_environment_information(
            beanstalkclient, environment_name)

    response = beanstalkclient.describe_application_versions(
        ApplicationName=application_name,
        MaxRecords=2
    )
    VERSION_LABEL = response['ApplicationVersions'][-1]['VersionLabel']

    if not deploy_new_version(beanstalkclient, application_name, environment_name, VERSION_LABEL):
        raise Exception("Failed to deploy new version.")