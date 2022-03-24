import os
import traceback
import sys
import clone_blue_environment
import swap_environment
import deploy_release
import release_health_check
import terminate_green_env
from termcolor import colored

print("name " + str(__name__))

def main():
    print(colored('hello', 'red'), colored('world', 'green'))
    print("Initiating blue green deployment process")

    ## Step 1: Cloning the blue env into green env.
    try:
      print("Clonning the blue environment into green environment")
      clone_blue_environment.main()
    except Exception as err:
      print("Clonning the blue environment into green environment has failed!")
      print("Error: " + str(err))
      e = sys.exc_info()[0]
      print(e)
      traceback.print_exc()
      sys.exit(1)
    
    ## Step 2: Swapping blue and green envs URL's.
    try:
      swap_environment.main()
    except Exception as err:
      print("Swap environment has failed.")
      print("Error: " + str(err))
      e = sys.exc_info()[0]
      print(e)
      traceback.print_exc()
      sys.exit(1)

    # ## Step 3: Deploying the new release into the blue env.
    try:
      deploy_release.main()
      print("New release deployed successfully.")
    except Exception as err:
      print("New release deployment has failed.")
      print("Error: " + str(err))
      e = sys.exc_info()[0]
      print(e)
      traceback.print_exc()
      sys.exit(1)

    ## Step 4: Health checking the new release deployment.
    try:
      release_health_check.main()
      print("The environment is health.")
    except Exception as err:
      print("Environment health check has failed.")
      print("Error: " + str(err))
      e = sys.exc_info()[0]
      print(e)
      traceback.print_exc()
      sys.exit(1)

    ## Step 5: Re-swapping the URL's and terminating the green environment.
    try:
      print("Re-swapping the URL's and terminating the green environment")
      terminate_green_env.main()
      print("The blue environment has terminated successfully.")
      print("The URL's has reswapped successfully.")
    except Exception as err:
      print("Re-swapping the URL's and terminating the green environment has failed!")
      print("Error: " + str(err))
      e = sys.exc_info()[0]
      print(e)
      traceback.print_exc()
      sys.exit(1)


if __name__ == "__main__":
  try:
    ENV = os.getenv("ENV")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
    AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")
    AWS_ROLE = os.getenv("AWS_ROLE")
    BLUE_ENV_NAME = os.getenv("BLUE_ENV_NAME")
    GREEN_ENV_NAME = os.getenv("GREEN_ENV_NAME")
    BEANSTALK_APP_NAME = os.getenv("BEANSTALK_APP_NAME")
    CREATE_CONFIG_TEMPLATE_NAME = os.getenv("CREATE_CONFIG_TEMPLATE_NAME")
    BLUE_CNAME_CONFIG_FILE = os.getenv("BLUE_CNAME_CONFIG_FILE")
    ARTIFACTS_S3_BUCKET=os.getenv('ARTIFACTS_S3_BUCKET')
    print("Successfully get envs")
  except Exception as e:
    print("Failed to get environment variable")
    print(str(e))
    e = sys.exc_info()[0]
    traceback.print_exc()
    sys.exit(1)
  main()