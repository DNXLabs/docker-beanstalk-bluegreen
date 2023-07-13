import json
import time
import os

# noqa: E502

def main(BLUE_ENV_NAME, GREEN_ENV_NAME, BEANSTALK_APP_NAME, S3_ARTIFACTS_BUCKET, boto_authenticated_client):

    beanstalkclient = boto_authenticated_client.client(
        'elasticbeanstalk', region_name=os.environ['AWS_DEFAULT_REGION'])
    s3client = boto_authenticated_client.client(
        's3', region_name=os.environ['AWS_DEFAULT_REGION'])


    blue_env_info = get_env_info(beanstalkclient, BLUE_ENV_NAME)
    blue_env_id = blue_env_info['Environments'][0]['EnvironmentId']
    blue_version_label = blue_env_info['Environments'][0]['VersionLabel']

    # Calling CreateConfigTemplate API
    config_template = create_config_template(beanstalkclient, AppName=(
        BEANSTALK_APP_NAME), blue_env_id=blue_env_id, TempName="BlueEnvConfig")
    ReturnedTempName = config_template
    if not ReturnedTempName:
        # raise Exception if the Config file does not exist
        raise Exception(
            "There were some issue while creating a Configuration Template from the Blue Environment")
    else:
        green_env_id, did_new_env_was_created = create_green_environment(
            beanstalkclient, GREEN_ENV_NAME,
            ReturnedTempName, blue_version_label,
            BEANSTALK_APP_NAME
        )

        print("Green environment ID: " + green_env_id)
        if green_env_id and did_new_env_was_created:
            # Create a CNAME Config file
            blue_env_cname = blue_env_info['Environments'][0]['CNAME']
            blue_env_cname_file = {'BlueEnvUrl': blue_env_cname}
            file_name = "blue_green_assets/blue_cname.json"
            response = s3client.put_object(
                Bucket=S3_ARTIFACTS_BUCKET, Key=file_name, Body=json.dumps(blue_env_cname_file))

            print("Created a new CNAME file at S3")

            current_release_bucket, current_release_key = get_current_release_package(
                beanstalkclient, BEANSTALK_APP_NAME)
            return current_release_bucket, current_release_key


def create_config_template(beanstalkclient, AppName, blue_env_id, TempName):
    '''Creates a ElasticBeanstalk deployment template and return the Template Name'''
    ListTemplates = beanstalkclient.describe_applications(
        ApplicationNames=[AppName])['Applications'][0]['ConfigurationTemplates']
    count = 0
    while count < len(ListTemplates):
        if ListTemplates[count] == TempName:
            print("Configuration template already exists")
            return TempName
        count += 1
    response = beanstalkclient.create_configuration_template(
        ApplicationName=AppName,
        TemplateName=TempName,
        EnvironmentId=blue_env_id)
    return response['TemplateName']


def get_env_info(beanstalkclient, env_name):
    ''' Get an beanstalk environment description by its name '''
    response = beanstalkclient.describe_environments(
        EnvironmentNames=[
            env_name
        ])
    return response


def create_green_environment(beanstalkclient, env_name, config_template, app_version, app_name):
    ''' Create a new elastic beansatalk environment based on a Environment Template'''
    did_new_env_was_created = True
    response = (beanstalkclient.describe_environments(
        EnvironmentNames=[env_name]))
    InvalidStatus = ["Terminating", "Terminated"]
    GetEnvData = [item for item in response['Environments']
                  if item['Status'] not in InvalidStatus]
    if not (GetEnvData == []):
        did_new_env_was_created = False
        if not (GetEnvData[0]['Status']) in InvalidStatus:
            print("Environment already exists")
            print(
                f"Existing Environment - {env_name} - it is in a Valid Status: {GetEnvData[0]['Status']}")
            return (GetEnvData[0]['EnvironmentId']), did_new_env_was_created
    print("Creating a new Environment")
    response = beanstalkclient.create_environment(
        ApplicationName=app_name,
        EnvironmentName=env_name,
        TemplateName=config_template,
        VersionLabel=app_version)
    return response['EnvironmentId'], did_new_env_was_created


def wait_green_be_ready(beanstalkclient, GREEN_ENV_NAME):
    ''' Stop code execution until an Beanstalk Environment gets in the Ready status'''
    green_env_info = get_env_info(beanstalkclient, GREEN_ENV_NAME)
    while green_env_info["Environments"][0]["Status"] != "Ready":
        print("Waiting the blue environment be Ready!")
        time.sleep(60)
        green_env_info = get_env_info(beanstalkclient, GREEN_ENV_NAME)


def rollback_created_env(boto_authenticated_client, environment_name):
    ''' Terminate a beanstalk environment'''

    time.sleep(10)
    beanstalkclient = boto_authenticated_client.client(
        'elasticbeanstalk', region_name=os.environ['AWS_DEFAULT_REGION'])

    green_env_info = get_env_info(beanstalkclient, environment_name)
    if len(green_env_info["Environments"]) == 0:
        return "Environment terminated successfully!"
    beanstalkclient.terminate_environment(
        EnvironmentName=environment_name,
        EnvironmentId=green_env_info["Environments"][0]["EnvironmentId"]
    )
    return "Environment terminaated successfully!!"

def get_current_release_package(client, application_name):
    response = client.describe_application_versions(
        ApplicationName=application_name,
        MaxRecords=1
    )

    return response['ApplicationVersions'][0]['SourceBundle']['S3Bucket'], response['ApplicationVersions'][0]['SourceBundle']['S3Key']
