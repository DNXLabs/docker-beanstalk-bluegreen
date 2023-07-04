import traceback
import time
import os

def main(BLUE_ENV_NAME, GREEN_ENV_NAME, BEANSTALK_APP_NAME, boto_authenticated_client):
    CREATE_CONFIG_TEMPLATE_NAME = "BlueEnvConfig"

    beanstalkclient = boto_authenticated_client.client('elasticbeanstalk',region_name=os.environ['AWS_DEFAULT_REGION'])
    s3client = boto_authenticated_client.client('s3',region_name=os.environ['AWS_DEFAULT_REGION'])
    try:
        print("Starting the job")
        # Extract the Job Data
        #Calling DeleteConfigTemplate API
        DeleteConfigTemplate=delete_config_template_blue(beanstalkclient, AppName=(BEANSTALK_APP_NAME), TempName=(CREATE_CONFIG_TEMPLATE_NAME))
        print(DeleteConfigTemplate)
        #re-swapping the urls
        print("Swapping URL's")
        reswap = swap_green_blue(beanstalkclient, SourceEnv=(BLUE_ENV_NAME), DestEnv=(GREEN_ENV_NAME))
        if reswap == "Failure":
            print("Re-Swap did not happen")
            raise Exception("Re-Swap did not happen")
        print("URL's swap was completed succesfully")
        print("Deleting the GreenEnvironment")
        delete_green_environment(beanstalkclient, EnvName=(GREEN_ENV_NAME))
    except Exception as e:
        print('Function failed due to exception.')
        traceback.print_exc()
        raise Exception(e)

def delete_config_template_blue(beanstalkclient, AppName, TempName):
    #check if the config template exists
    ListTemplates = beanstalkclient.describe_applications(ApplicationNames=[AppName])['Applications'][0]['ConfigurationTemplates']
    if TempName not in ListTemplates:
        return ("Config Template does not exist")
    else:
        response = beanstalkclient.delete_configuration_template(ApplicationName=AppName,TemplateName=TempName)
        return ("Config Template Deleted")

def swap_green_blue(beanstalkclient, SourceEnv, DestEnv):
    GetEnvData = (beanstalkclient.describe_environments(EnvironmentNames=[SourceEnv,DestEnv],IncludeDeleted=False))
    if (((GetEnvData['Environments'][0]['Status']) == "Ready") and ((GetEnvData['Environments'][1]['Status']) == "Ready")):
        response = beanstalkclient.swap_environment_cnames(SourceEnvironmentName=SourceEnv,DestinationEnvironmentName=DestEnv)
        return ("Successful")
    else:
        return ("Failure")

def delete_green_environment(beanstalkclient, EnvName):
    GetEnvData = (beanstalkclient.describe_environments(EnvironmentNames=[EnvName]))
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
            print("Successfully Terminated Green Environment")
            return