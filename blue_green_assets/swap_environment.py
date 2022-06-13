import json
import traceback
import time
import sys
import logging
import os
import time



def main(BLUE_ENV_NAME, GREEN_ENV_NAME, S3_ARTIFACTS_BUCKET, boto_authenticated_client):
    beanstalkclient = boto_authenticated_client.client("elasticbeanstalk",region_name="ap-southeast-2")
    s3client = boto_authenticated_client.client('s3',region_name='ap-southeast-2')

    BLUE_CNAME_CONFIG_FILE = "blue_green_assets/blue_cname.json"

    blue_env_url = get_blue_env_address(BLUE_CNAME_CONFIG_FILE, S3_ARTIFACTS_BUCKET, s3client)
    print("Blue env URL: " + str(blue_env_url))


    green_env_info = get_environment_information(beanstalkclient, GREEN_ENV_NAME)
    green_env_cname = green_env_info["Environments"][0]["CNAME"]

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

    


def get_blue_env_address(BLUE_CNAME_CONFIG_FILE, S3_ARTIFACTS_BUCKET, s3client):
    # Opening JSON file
    file_name = BLUE_CNAME_CONFIG_FILE
    data = json.loads(s3client.get_object(Bucket=S3_ARTIFACTS_BUCKET, Key=file_name)['Body'].read())
    blue_env_url = data["BlueEnvUrl"]
    return blue_env_url

def get_environment_information(beanstalkclient, EnvName):
  count = 0
  while True:
      response = beanstalkclient.describe_environments(
      EnvironmentNames=[
          EnvName
      ])
      if response["Environments"][0]["Status"] == "Ready":
        break
      time.sleep(5)

      if count == 3:
          print("Waiting the env be ready.")
          count = 0
      else:
          count+=1

  return response


def swap_urls(beanstalkclient, SourceEnv, DestEnv):
    green_env_data = (beanstalkclient.describe_environments(EnvironmentNames=[SourceEnv,DestEnv],IncludeDeleted=False))
    print(green_env_data)
    if (((green_env_data["Environments"][0]["Status"]) == "Ready") and ((green_env_data["Environments"][1]["Status"]) == "Ready")):
        beanstalkclient.swap_environment_cnames(SourceEnvironmentName=SourceEnv,DestinationEnvironmentName=DestEnv)
        return ("Successful")
    else:
        return ("Failure")
