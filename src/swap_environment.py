import json
import time
import os


BLUE_CNAME_CONFIG_FILE = "blue_green_assets/blue_cname.json"


def main(BLUE_ENV_NAME, GREEN_ENV_NAME, S3_ARTIFACTS_BUCKET, BEANSTALK_APP_NAME, boto_authenticated_client):
    beanstalkclient = boto_authenticated_client.client(
        "elasticbeanstalk", region_name=os.environ['AWS_DEFAULT_REGION'])
    s3client = boto_authenticated_client.client(
        's3', region_name=os.environ['AWS_DEFAULT_REGION'])
    route53_client = boto_authenticated_client.client(
        'route53', region_name=os.environ['AWS_DEFAULT_REGION'])
    ssm_client = boto_authenticated_client.client(
        'ssm', region_name=os.environ['AWS_DEFAULT_REGION'])

    blue_env_url = get_env_address(
        BLUE_CNAME_CONFIG_FILE, S3_ARTIFACTS_BUCKET, s3client)
    print("Blue env URL: " + str(blue_env_url))

    green_env_info, beanstalkclient = get_environment_information(
        beanstalkclient, GREEN_ENV_NAME)
    green_env_cname = green_env_info["Environments"][0]["CNAME"]

    applications_response = get_ssm_parameter(ssm_client, BEANSTALK_APP_NAME)
    applications_list = applications_response['Parameter']['Value']

    hosted_zone_id_ssm_response = get_ssm_parameter(ssm_client, "HostedZoneId")
    hosted_zone_id = hosted_zone_id_ssm_response['Parameter']['Value']

    create_route53_records(route53_client, applications_list,
                           green_env_cname, hosted_zone_id)

    print("Green env CNAME: " + str(green_env_cname))

    if blue_env_url == green_env_cname:
        print("Nothing to swap")
    else:
        while green_env_info["Environments"][0]["Status"] != "Ready":
            time.sleep(10)
            green_env_info = get_environment_information(
                beanstalkclient, GREEN_ENV_NAME)
        swap_response = swap_urls(
            beanstalkclient, BLUE_ENV_NAME, GREEN_ENV_NAME)
        if swap_response == "Successful":
            return "Ok"
        else:
            raise Exception("Failed to swap environments!")


def get_env_address(BLUE_CNAME_CONFIG_FILE, S3_ARTIFACTS_BUCKET, s3client):
    ''' Get the domain of an beanstalk environment'''
    # Opening JSON file
    file_name = BLUE_CNAME_CONFIG_FILE
    data = json.loads(s3client.get_object(
        Bucket=S3_ARTIFACTS_BUCKET, Key=file_name)['Body'].read())
    blue_env_url = data["BlueEnvUrl"]
    return blue_env_url


def get_environment_information(beanstalkclient, EnvName):
    ''' Get informations about a beanstalk environment'''
    env_count = 0

    while True:
        response = beanstalkclient.describe_environments(
            EnvironmentNames=[
                EnvName
            ])
        if response["Environments"][0]["Status"] == "Ready":
            break
        time.sleep(60)

        if env_count == 3:
            print("Waiting for {EnvName} env to be ready.")
            env_count = 0
        else:
            env_count += 1

    return response, beanstalkclient


def swap_urls(beanstalkclient, SourceEnv, DestEnv):
    ''' Swap URLs between two beanstalk environment from the same application'''
    green_env_data = (beanstalkclient.describe_environments(
        EnvironmentNames=[SourceEnv, DestEnv], IncludeDeleted=False))
    print(green_env_data)
    if (((green_env_data["Environments"][0]["Status"]) == "Ready") and ((green_env_data["Environments"][1]["Status"]) == "Ready")):
        beanstalkclient.swap_environment_cnames(
            SourceEnvironmentName=SourceEnv, DestinationEnvironmentName=DestEnv)
        return ("Successful")
    else:
        return ("Failure")


def create_route53_records(route53_client, applications_list, green_env_url, hosted_zone_id):
    ''' Create a recordset in the route53'''
    for record in eval(applications_list):
        route53_client.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                "Changes": [
                    {
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Type": "CNAME",
                            "Name": record,
                            "Region": os.environ['AWS_DEFAULT_REGION'],
                            "SetIdentifier": f"{record} Identifier",
                            "TTL": 60,
                            "ResourceRecords": [
                                {
                                    "Value": green_env_url,
                                },
                            ],
                        }
                    },
                ]
            }
        )


def get_ssm_parameter(client, parameter_name):
    ''' Obtain an SSM parameter'''
    response = client.get_parameter(
        Name=parameter_name
    )

    return response


def re_swap_dns(boto_authenticated_client, S3_ARTIFACTS_BUCKET, GREEN_ENV_NAME, BLUE_ENV_NAME):
    '''Re-swap beanstalk environments Domains applying the rollback'''

    time.sleep(10)
    beanstalkclient = boto_authenticated_client.client(
        "elasticbeanstalk", region_name=os.environ['AWS_DEFAULT_REGION'])
    s3client = boto_authenticated_client.client(
        's3', region_name=os.environ['AWS_DEFAULT_REGION'])

    blue_env_url = get_env_address(
        BLUE_CNAME_CONFIG_FILE, S3_ARTIFACTS_BUCKET, s3client
    )

    green_env_info, client = get_environment_information(
        beanstalkclient, GREEN_ENV_NAME)
    green_env_cname = green_env_info["Environments"][0]["CNAME"]

    blue_env_info, client = get_environment_information(
        beanstalkclient, BLUE_ENV_NAME)

    if blue_env_url != green_env_cname:
        print("Nothing to re-swap")
        return "Nothing to Swap!"
    else:
        while green_env_info["Environments"][0]["Status"] != "Ready" and blue_env_info["Environments"][0]["Status"] != "Ready" :
            time.sleep(10)
            green_env_info, client = get_environment_information(
                beanstalkclient, GREEN_ENV_NAME)
            blue_env_info, client = get_environment_information(
                beanstalkclient, BLUE_ENV_NAME)
        swap_response = swap_urls(
            beanstalkclient, GREEN_ENV_NAME, BLUE_ENV_NAME)
        if swap_response == "Successful":
            return "Ok"
        else:
            raise Exception("Failed to re-swap environments!")