from __future__ import print_function
import os
from time import strftime, sleep
import boto3
import requests
import time

def main():
    beanstalkclient = boto3.client('elasticbeanstalk')

    BLUE_ENV_NAME = os.getenv("BLUE_ENV_NAME")

    wait_until_env_be_ready(beanstalkclient, BLUE_ENV_NAME)

    blue_env_info = get_env_info(beanstalkclient, BLUE_ENV_NAME)
    blue_env_cname = blue_env_info["Environments"][0]["CNAME"]

    env_http_response = requests.get("http://"+blue_env_cname)
    env_reponse_status = env_http_response.status_code

    if env_reponse_status == 200 or env_reponse_status == 301:
        return "Ok"
    else:
        raise Exception("The environment isn't health")

def get_env_info(beanstalkclient, env_name):
  response = beanstalkclient.describe_environments(
  EnvironmentNames=[
      env_name
  ])
  print("Described the environment")
  return response

def wait_until_env_be_ready(beanstalkclient, ENV_NAME):
  env_info = get_env_info(beanstalkclient, ENV_NAME)
  while env_info["Environments"][0]["Status"] != "Ready":
    print("Waiting the blue environment be Ready!")
    time.sleep(10)
    env_info = get_env_info(beanstalkclient, ENV_NAME)
  return "Env is ready"