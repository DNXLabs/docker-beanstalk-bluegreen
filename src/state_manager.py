import json
import os
global state
state = {}


def initialize_state(boto_authenticated_client):
    """
    Initialize the state file
    :param boto_authenticated_client:
    """
    # Implement a code that will initialize the state file
    # and save it to S3

    if len(state) > 0:
        print("State file already exists")
        return

    s3client = boto_authenticated_client.client(
        's3', region_name=os.environ['AWS_DEFAULT_REGION'])

    response = s3client.list_objects(
        Bucket=os.environ['S3_ARTIFACTS_BUCKET'],
        Prefix=f"deployment_state/{os.environ['VERSION_LABEL']}.json"
    )

    if 'Contents' in response:
        print("Remote state file exists, updating local state")
        get_state(boto_authenticated_client)
    else:
        print("Remote state file doesn't exist, creating a new one")
        update_local_state({})

def get_state(boto_authenticated_client):
    """
    Get the state file from S3 and return it as a dictionary
    :param boto_authenticated_client:
    """

    # Implement a code that will download the state file from S3
    # and return it as a dictionary
    s3client = boto_authenticated_client.client(
        's3', region_name=os.environ['AWS_DEFAULT_REGION'])
    remote_state = s3client.get_object(
        Bucket=os.environ['S3_ARTIFACTS_BUCKET'],
        Key=f"deployment_state/{os.environ['VERSION_LABEL']}.json"
    )
    remote_state = json.loads(remote_state['Body'].read().decode('utf-8'))
    update_local_state(remote_state)

def save_state(boto_authenticated_client):
    """
    Save the state file to S3
    :param boto_authenticated_client:
    """
    s3client = boto_authenticated_client.client(
        's3', region_name=os.environ['AWS_DEFAULT_REGION'])
    s3client.put_object(
        Bucket=os.environ['S3_ARTIFACTS_BUCKET'],
        Key=f"deployment_state/{os.environ['VERSION_LABEL']}.json",
        Body=json.dumps(state)
    )

def print_state():
    """
    Print the state dictionary
    """
    print(json.dumps(state, indent=4, sort_keys=True))

def update_local_state(remote_state):
    """
    Update the local state dictionary with the remote state
    :param remote_state:
    """
    state["current_version_label"] = remote_state["current_version_label"]\
        if "current_version_label" in remote_state.keys()\
        else os.environ["VERSION_LABEL"]
    state["beanstalk_app_name"] = remote_state["beanstalk_app_name"]\
        if "beanstalk_app_name" in remote_state.keys()\
        else os.environ["BEANSTALK_APP_NAME"]
    state["s3_artifacts_bucket"] = remote_state["s3_artifacts_bucket"]\
        if "s3_artifacts_bucket" in remote_state.keys()\
        else os.environ["S3_ARTIFACTS_BUCKET"]
    state["s3_artifact_object"] = remote_state["s3_artifact_object"]\
        if "s3_artifact_object" in remote_state.keys()\
        else os.environ["S3_ARTIFACTS_OBJECT"]
    state["blue_env_id"] = remote_state["blue_env_id"]\
        if "blue_env_id" in remote_state.keys()\
        else ""
    state["green_env_id"] = remote_state["green_env_id"]\
        if "green_env_id" in remote_state.keys()\
        else ""
    state["blue_env_name"] = remote_state["blue_env_name"]\
        if "blue_env_name" in remote_state.keys()\
        else os.environ["BLUE_ENV_NAME"]
    state["green_env_name"] = remote_state["green_env_name"]\
        if "green_env_name" in remote_state.keys()\
        else os.environ["GREEN_ENV_NAME"]
    state["blue_env_version"] = remote_state["blue_env_version"]\
        if "blue_env_version" in remote_state.keys()\
        else ""
    state["green_env_version"] = remote_state["green_env_version"]\
        if "green_env_version" in remote_state.keys()\
        else ""
    state["blue_env_config_template"] = remote_state["blue_env_config_template"]\
        if "blue_env_config_template" in remote_state.keys()\
        else ""
    state["green_env_config_template"] = remote_state["green_env_config_template"]\
        if "green_env_config_template" in remote_state.keys()\
        else ""
    state["blue_env_url"] = remote_state["blue_env_url"]\
        if "blue_env_url" in remote_state.keys()\
        else ""
    state["green_env_url"] = remote_state["green_env_url"]\
        if "green_env_url" in remote_state.keys()\
        else ""
    state["blue_env_status"] = remote_state["blue_env_status"]\
        if "blue_env_status" in remote_state.keys()\
        else ""
    state["green_env_status"] = remote_state["green_env_status"]\
        if "green_env_status" in remote_state.keys()\
        else ""
    state["blue_version_label"] = remote_state["blue_version_label"]\
        if "blue_version_label" in remote_state.keys()\
        else ""
