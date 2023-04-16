import json
import time
import aws_authentication



def main(BLUE_ENV_NAME, GREEN_ENV_NAME, S3_ARTIFACTS_BUCKET, BEANSTALK_APP_NAME, boto_authenticated_client):
    beanstalkclient = boto_authenticated_client.client("elasticbeanstalk", region_name="ap-southeast-2")
    s3client = boto_authenticated_client.client('s3', region_name='ap-southeast-2')
    route53_client = boto_authenticated_client.client('route53', region_name='ap-southeast-2')
    ssm_client = boto_authenticated_client.client('ssm', region_name='ap-southeast-2')

    BLUE_CNAME_CONFIG_FILE = "blue_green_assets/blue_cname.json"

    blue_env_url = get_env_address(BLUE_CNAME_CONFIG_FILE, S3_ARTIFACTS_BUCKET, s3client)
    print("Blue env URL: " + str(blue_env_url))


    green_env_info, beanstalkclient = get_environment_information(beanstalkclient, GREEN_ENV_NAME)
    green_env_cname = green_env_info["Environments"][0]["CNAME"]

    applications_response = get_ssm_parameter(ssm_client, BEANSTALK_APP_NAME)
    applications_list = applications_response['Parameter']['Value']

    hosted_zone_id_ssm_response = get_ssm_parameter(ssm_client, "HostedZoneId")
    hosted_zone_id = hosted_zone_id_ssm_response['Parameter']['Value']


    create_route53_records(route53_client, applications_list, green_env_cname, hosted_zone_id)



    print("Green env CNAME: " + str(green_env_cname))

    if blue_env_url == green_env_cname:
        print("Nothing to swap")
    else:
        while green_env_info["Environments"][0]["Status"] != "Ready":
            time.sleep(10)
            green_env_info = get_environment_information(beanstalkclient, GREEN_ENV_NAME)
        swap_response = swap_urls(beanstalkclient, BLUE_ENV_NAME, GREEN_ENV_NAME)
        if swap_response == "Successful":
            return "Ok"
        else:
            raise Exception("Failed to swap environments!")
    


def get_env_address(BLUE_CNAME_CONFIG_FILE, S3_ARTIFACTS_BUCKET, s3client):
    # Opening JSON file
    file_name = BLUE_CNAME_CONFIG_FILE
    data = json.loads(s3client.get_object(Bucket=S3_ARTIFACTS_BUCKET, Key=file_name)['Body'].read())
    blue_env_url = data["BlueEnvUrl"]
    return blue_env_url

def get_environment_information(beanstalkclient, EnvName):
  env_count = 0
  env_count_for_credentials = 0

  while True:
      response = beanstalkclient.describe_environments(
      EnvironmentNames=[
          EnvName
      ])
      if response["Environments"][0]["Status"] == "Ready":
        break
      time.sleep(5)

      if env_count == 3:
          print("Waiting the env be ready.")
          env_count = 0
      else:
          env_count+=1
      if env_count_for_credentials == 12:
            print("Renewing security token...")
            boto_client = aws_authentication.get_boto_client()
            beanstalkclient = boto_client.client("elasticbeanstalk", region_name="ap-southeast-2")
            env_count_for_credentials=0
      else:
            env_count_for_credentials+=1

  return response, beanstalkclient


def swap_urls(beanstalkclient, SourceEnv, DestEnv):
    green_env_data = (beanstalkclient.describe_environments(EnvironmentNames=[SourceEnv,DestEnv],IncludeDeleted=False))
    print(green_env_data)
    if (((green_env_data["Environments"][0]["Status"]) == "Ready") and ((green_env_data["Environments"][1]["Status"]) == "Ready")):
        beanstalkclient.swap_environment_cnames(SourceEnvironmentName=SourceEnv,DestinationEnvironmentName=DestEnv)
        return ("Successful")
    else:
        return ("Failure")

def create_route53_records(route53_client, applications_list, green_env_url, hosted_zone_id):
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
                            "Region": "ap-southeast-2",
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
    response = client.get_parameter(
        Name=parameter_name
    )

    return response