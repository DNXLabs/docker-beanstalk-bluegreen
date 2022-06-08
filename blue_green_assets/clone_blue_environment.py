import json
import traceback
import sys
import logging
import os
import time
import aws_authentication

def main(BLUE_ENV_NAME, GREEN_ENV_NAME, BEANSTALK_APP_NAME, boto_authenticated_client):
  beanstalkclient = boto_authenticated_client.client('elasticbeanstalk',region_name='ap-southeast-2')
  blue_env_info=get_blue_env_info(beanstalkclient, BLUE_ENV_NAME)
  blue_env_id=(blue_env_info['Environments'][0]['EnvironmentId'])
  blue_version_label=(blue_env_info['Environments'][0]['VersionLabel'])
  
  #Calling CreateConfigTemplate API
  config_template=create_config_template(beanstalkclient, AppName=(BEANSTALK_APP_NAME),blue_env_id=blue_env_id,TempName="BlueEnvConfig")
  ReturnedTempName=config_template
  if not ReturnedTempName:
    #raise Exception if the Config file does not exist
    raise Exception("There were some issue while creating a Configuration Template from the Blue Environment")
  else:
    green_env_id=create_green_environment(beanstalkclient, env_name=(GREEN_ENV_NAME),config_template=ReturnedTempName,AppVersion=blue_version_label,AppName=(BEANSTALK_APP_NAME))
    
    # wait_green_be_ready(beanstalkclient, GREEN_ENV_NAME)

    print("Green environment ID: " + green_env_id)
    if green_env_id:
      #Create a CNAME Config file
      BlueEnvCname=(blue_env_info['Environments'][0]['CNAME'])
      BlueEnvCnameFile = {'BlueEnvUrl': BlueEnvCname}
      file_name = "blue_cname.json"
      with open(file_name, 'w') as fp:
        json.dump(BlueEnvCnameFile, fp)
      print ("Created a new CNAME file")

def create_config_template(beanstalkclient, AppName,blue_env_id,TempName):
  ListTemplates = beanstalkclient.describe_applications(ApplicationNames=[AppName])['Applications'][0]['ConfigurationTemplates']
  count = 0
  while count < len(ListTemplates):
    print (ListTemplates[count])
    if ListTemplates[count] == TempName:
      print ("ConfigTempAlreadyExists")
      return TempName
    count += 1
  response = beanstalkclient.create_configuration_template(
  ApplicationName=AppName,
  TemplateName=TempName,
  EnvironmentId=blue_env_id)
  return response['TemplateName']

def get_blue_env_info(beanstalkclient, env_name):
  response = beanstalkclient.describe_environments(
  EnvironmentNames=[
      env_name
  ])
  return response

def create_green_environment(beanstalkclient, env_name,config_template,AppVersion,AppName):
  GetEnvData = (beanstalkclient.describe_environments(EnvironmentNames=[env_name]))
  print(GetEnvData)
  InvalidStatus = ["Terminating","Terminated"]
  if not(GetEnvData['Environments']==[]):
    print("Environment Exists")
    if not(GetEnvData['Environments'][0]['Status']) in InvalidStatus:
      print("Existing Environment with the name %s not in Invalid Status" % env_name)
      return (GetEnvData['Environments'][0]['EnvironmentId'])
  print ("Creating a new Environment")
  response = beanstalkclient.create_environment(
  ApplicationName=AppName,
  EnvironmentName=env_name,
  TemplateName=config_template,
  VersionLabel=AppVersion)
  return response['EnvironmentId']

def wait_green_be_ready(beanstalkclient, GREEN_ENV_NAME):
  green_env_info = get_green_env_info(beanstalkclient, GREEN_ENV_NAME)
  while green_env_info["Environments"][0]["Status"] != "Ready":
    print("Waiting the blue environment be Ready!")
    time.sleep(10)
    green_env_info = get_green_env_info(beanstalkclient, GREEN_ENV_NAME)

def get_green_env_info(beanstalkclient, env_name):
  response = beanstalkclient.describe_environments(
  EnvironmentNames=[
      env_name
  ])
  return response

def timeout(event):
    logging.error('Execution is about to time out, sending failure response to CodePipeline')
