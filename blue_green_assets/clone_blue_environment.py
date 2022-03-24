import boto3
import json
import traceback
import sys
import logging
import os
import time

def main():
  ENV = os.getenv('ENV')
  AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
  AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
  AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
  AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')
  AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')
  AWS_ROLE = os.getenv('AWS_ROLE')
  BLUE_ENV_NAME = os.getenv('BLUE_ENV_NAME')
  GREEN_ENV_NAME = os.getenv('GREEN_ENV_NAME')
  BEANSTALK_APP_NAME = os.getenv('BEANSTALK_APP_NAME')
  CREATE_CONFIG_TEMPLATE_NAME = os.getenv('CREATE_CONFIG_TEMPLATE_NAME')
  BLUE_CNAME_CONFIG_FILE = os.getenv('BLUE_CNAME_CONFIG_FILE')
  beanstalkclient = boto3.client('elasticbeanstalk',region_name='ap-southeast-2')
  try:
    BlueEnvInfo=GetBlueEnvInfo(beanstalkclient, BLUE_ENV_NAME)
    BlueEnvId=(BlueEnvInfo['Environments'][0]['EnvironmentId'])
    BlueVersionLabel=(BlueEnvInfo['Environments'][0]['VersionLabel'])
    
    #Calling CreateConfigTemplate API
    ConfigTemplate=CreateConfigTemplateBlue(beanstalkclient, AppName=(BEANSTALK_APP_NAME),BlueEnvId=BlueEnvId,TempName=CREATE_CONFIG_TEMPLATE_NAME)
    ReturnedTempName=ConfigTemplate
    if not ReturnedTempName:
      #raise Exception if the Config file does not exist
      raise Exception("There were some issue while creating a Configuration Template from the Blue Environment")
    else:
      GreenEnvId=CreateGreenEnvironment(beanstalkclient, EnvName=(GREEN_ENV_NAME),ConfigTemplate=ReturnedTempName,AppVersion=BlueVersionLabel,AppName=(BEANSTALK_APP_NAME))
      
      # wait_green_be_ready(beanstalkclient, GREEN_ENV_NAME)

      print("GreenEnvId: " + GreenEnvId)
      if GreenEnvId:
        #Create a CNAME Config file
        BlueEnvCname=(BlueEnvInfo['Environments'][0]['CNAME'])
        BlueEnvCnameFile = {'BlueEnvUrl': BlueEnvCname}
        file_name = BLUE_CNAME_CONFIG_FILE
        with open(file_name, 'w') as fp:
          json.dump(BlueEnvCnameFile, fp)
        print ("Created a new CNAME file")
  except Exception as e:
    print('Function failed due to exception.')
    e = sys.exc_info()[0]
    print(e)
    traceback.print_exc()

def CreateConfigTemplateBlue(beanstalkclient, AppName,BlueEnvId,TempName):
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
  EnvironmentId=BlueEnvId)
  return response['TemplateName']

def GetBlueEnvInfo(beanstalkclient, EnvName):
  response = beanstalkclient.describe_environments(
  EnvironmentNames=[
      EnvName
  ])
  print("Described the environment")
  return response

def CreateGreenEnvironment(beanstalkclient, EnvName,ConfigTemplate,AppVersion,AppName):
  GetEnvData = (beanstalkclient.describe_environments(EnvironmentNames=[EnvName]))
  print(GetEnvData)
  InvalidStatus = ["Terminating","Terminated"]
  if not(GetEnvData['Environments']==[]):
    print("Environment Exists")
    if not(GetEnvData['Environments'][0]['Status']) in InvalidStatus:
      print("Existing Environment with the name %s not in Invalid Status" % EnvName)
      return (GetEnvData['Environments'][0]['EnvironmentId'])
  print ("Creating a new Environment")
  response = beanstalkclient.create_environment(
  ApplicationName=AppName,
  EnvironmentName=EnvName,
  TemplateName=ConfigTemplate,
  VersionLabel=AppVersion)
  return response['EnvironmentId']

def wait_green_be_ready(beanstalkclient, GREEN_ENV_NAME):
  green_env_info = get_green_env_info(beanstalkclient, GREEN_ENV_NAME)
  while green_env_info["Environments"][0]["Status"] != "Ready":
    print("Waiting the blue environment be Ready!")
    time.sleep(10)
    green_env_info = get_green_env_info(beanstalkclient, GREEN_ENV_NAME)

def get_green_env_info(beanstalkclient, EnvName):
  response = beanstalkclient.describe_environments(
  EnvironmentNames=[
      EnvName
  ])
  print("Described the environment")
  return response

def timeout(event):
    logging.error('Execution is about to time out, sending failure response to CodePipeline')
