import boto3
import json
import traceback
import time
import sys
import logging
import os

def main():
    BLUE_ENV_NAME = os.getenv("BLUE_ENV_NAME")
    GREEN_ENV_NAME = os.getenv("GREEN_ENV_NAME")
    BEANSTALK_APP_NAME = os.getenv("BEANSTALK_APP_NAME")
    CREATE_CONFIG_TEMPLATE_NAME = os.getenv("CREATE_CONFIG_TEMPLATE_NAME")

    beanstalkclient = boto3.client('elasticbeanstalk',region_name='ap-southeast-2')
    try:
        print("Starting the job")
        # Extract the Job Data
        #Calling DeleteConfigTemplate API
        DeleteConfigTemplate=DeleteConfigTemplateBlue(beanstalkclient, AppName=(BEANSTALK_APP_NAME),TempName=(CREATE_CONFIG_TEMPLATE_NAME))
        print(DeleteConfigTemplate)
        #re-swapping the urls
        print("Swapping the URL's")
        reswap = SwapGreenandBlue(beanstalkclient, SourceEnv=(BLUE_ENV_NAME),DestEnv=(GREEN_ENV_NAME))
        if reswap == "Failure":
            print("Re-Swap did not happen")
            raise Exception("Re-Swap did not happen")
        print("URL's swap was completed succesfully")
        print("Deleting the GreenEnvironment")
        DeleteGreenEnvironment(beanstalkclient, EnvName=(GREEN_ENV_NAME))
        
        #Set status
        Status="Success"
        Message="Successfully reswapped and terminated the Green Environment"

    except Exception as e:
        print('Function failed due to exception.')
        e = sys.exc_info()[0]
        print(e)
        traceback.print_exc()
        Status="Failure"
        Message=("Error occured while executing this. The error is %s" %e)

    finally:
        if (Status =="Success"):
            put_job_success(Message)
        else:
            put_job_failure(Message)

def DeleteConfigTemplateBlue(beanstalkclient, AppName,TempName):
    #check if the config template exists
    ListTemplates = beanstalkclient.describe_applications(ApplicationNames=[AppName])['Applications'][0]['ConfigurationTemplates']
    if TempName not in ListTemplates:
        return ("Config Template does not exist")
    else:
        response = beanstalkclient.delete_configuration_template(ApplicationName=AppName,TemplateName=TempName)
        return ("Config Template Deleted")

def SwapGreenandBlue(beanstalkclient, SourceEnv, DestEnv):
    GetEnvData = (beanstalkclient.describe_environments(EnvironmentNames=[SourceEnv,DestEnv],IncludeDeleted=False))
    print(GetEnvData)
    if (((GetEnvData['Environments'][0]['Status']) == "Ready") and ((GetEnvData['Environments'][1]['Status']) == "Ready")):
        response = beanstalkclient.swap_environment_cnames(SourceEnvironmentName=SourceEnv,DestinationEnvironmentName=DestEnv)
        return ("Successful")
    else:
        return ("Failure")

def DeleteGreenEnvironment(beanstalkclient, EnvName):
    GetEnvData = (beanstalkclient.describe_environments(EnvironmentNames=[EnvName]))
    print(GetEnvData)
    InvalidStatus = ["Terminating","Terminated"]
    if not(GetEnvData['Environments']==[]):
        if (GetEnvData['Environments'][0]['Status']) in InvalidStatus:
            return ("Already Terminated")
    while True:
        GreenEnvStatus = (beanstalkclient.describe_environments(EnvironmentNames=[EnvName]))['Environments'][0]['Status']
        print(GreenEnvStatus)
        time.sleep(10)
        if (GreenEnvStatus == 'Ready'):
            response = beanstalkclient.terminate_environment(EnvironmentName=EnvName)
            print(response)
            print("Successfully Terminated Green Environment")
            return
def timeout(event):
    logging.error('Execution is about to time out, sending failure response to CodePipeline')
    put_job_failure(event['event']['id'], "FunctionTimeOut")

def put_job_success( message):
    print('Putting job success')
    print(message)

def put_job_failure(message):
    print('Putting job failure')
    print(message)