import boto3
import json
import traceback
import time
import sys
import logging
import os
import time



def main():
    beanstalkclient = boto3.client("elasticbeanstalk",region_name="ap-southeast-2")

    BLUE_CNAME_CONFIG_FILE = os.getenv("BLUE_CNAME_CONFIG_FILE")
    BLUE_ENV_NAME = os.getenv("BLUE_ENV_NAME")
    GREEN_ENV_NAME = os.getenv("GREEN_ENV_NAME")

    blue_env_url = get_blue_env_address(BLUE_CNAME_CONFIG_FILE)
    print("Blue env URL: " + str(blue_env_url))


    green_env_info = get_green_env_info(beanstalkclient, GREEN_ENV_NAME)
    green_env_cname = green_env_info["Environments"][0]["CNAME"]

    print("Green env CNAME: " + str(green_env_cname))

    if blue_env_url == green_env_cname:
        print("Nothing to swap")
    else:
        while green_env_info["Environments"][0]["Status"] != "Ready":
            time.sleep(10)
            green_env_info = get_green_env_info(beanstalkclient, GREEN_ENV_NAME)
        swap_response = swap_urls(beanstalkclient, BLUE_ENV_NAME, GREEN_ENV_NAME)
        if swap_response == "Successful":
            return "Ok"
        else:
            raise Exception("Failed to swap environments!")

    


def get_blue_env_address(BLUE_CNAME_CONFIG_FILE):
    # Opening JSON file
    file_name = BLUE_CNAME_CONFIG_FILE
    with open(file_name) as json_file:
        data = json.load(json_file)
    blue_env_url = data["BlueEnvUrl"]
    return blue_env_url

def get_green_env_info(beanstalkclient, EnvName):
  response = beanstalkclient.describe_environments(
  EnvironmentNames=[
      EnvName
  ])
  print("Described the environment")
  return response


def swap_urls(beanstalkclient, SourceEnv, DestEnv):
    green_env_data = (beanstalkclient.describe_environments(EnvironmentNames=[SourceEnv,DestEnv],IncludeDeleted=False))
    print(green_env_data)
    if (((green_env_data["Environments"][0]["Status"]) == "Ready") and ((green_env_data["Environments"][1]["Status"]) == "Ready")):
        beanstalkclient.swap_environment_cnames(SourceEnvironmentName=SourceEnv,DestinationEnvironmentName=DestEnv)
        return ("Successful")
    else:
        return ("Failure")