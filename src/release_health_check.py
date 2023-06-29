from __future__ import print_function
import os
from time import strftime, sleep
import requests
import time


def main(BLUE_ENV_NAME, boto_authenticated_client):
    beanstalkclient = boto_authenticated_client.client('elasticbeanstalk')

    wait_until_env_be_ready(beanstalkclient, BLUE_ENV_NAME)

    if os.getenv("RELEASE_HEALTH_CHECKING_PATH"):
        blue_env_cname = os.getenv("RELEASE_HEALTH_CHECKING_PATH")
    else:
        blue_env_info = get_env_info(beanstalkclient, BLUE_ENV_NAME)
        blue_env_cname = "http://" + blue_env_info["Environments"][0]["CNAME"]

    print("blue_env_cname: " + blue_env_cname)
    env_http_response = requests.get(blue_env_cname, verify=False)
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
    return response


def wait_until_env_be_ready(beanstalkclient, ENV_NAME):
    env_info = get_env_info(beanstalkclient, ENV_NAME)
    while env_info["Environments"][0]["Status"] != "Ready":
        print("Waiting the blue environment be Ready!")
        time.sleep(10)
        env_info = get_env_info(beanstalkclient, ENV_NAME)
    return "Env is ready"
