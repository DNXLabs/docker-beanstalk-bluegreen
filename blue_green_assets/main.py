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
    # print(colored('hello', 'red'), colored('world', 'green'))
    print(colored("Initiating blue green deployment process", "blue"))

    ## Step 1: Cloning the blue env into green env.
    try:
      print(colored("Clonning the blue environment into green environment", "blue"))
      clone_blue_environment.main()
    except Exception as err:
      print(colored("Clonning the blue environment into green environment has failed!", "red"))
      print(colored( ("Error: " + str(err)), "red"))
      e = sys.exc_info()[0]
      print(colored(e, "red"))
      traceback.print_exc()
      sys.exit(1)
    
    ## Step 2: Swapping blue and green envs URL's.
    try:
      print(colored("Swapping environment URL's", "blue"))
      swap_environment.main()
      print(colored("URL's swapped successfully", "green"))
    except Exception as err:
      print(colored("Swap environment has failed.", "red"))
      print(colored(("Error: " + str(err)), "red"))
      e = sys.exc_info()[0]
      print(colored(e, "red"))
      traceback.print_exc()
      sys.exit(1)

    # ## Step 3: Deploying the new release into the blue env.
    try:
      print(colored("New release deployment initiated.", "blue"))
      deploy_release.main()
      print(colored("New release was deployed successfully.", "green"))
    except Exception as err:
      print(colored("New release deployment has failed.", "red"))
      print(colored(("Error: " + str(err)), "red"))
      e = sys.exc_info()[0]
      print(e)
      traceback.print_exc()
      sys.exit(1)

    ## Step 4: Health checking the new release deployment.
    try:
      print(colored("Health checking the new release.", "blue"))
      release_health_check.main()
      print(colored("The environment is health.", "green"))
    except Exception as err:
      print(colored("Environment health check has failed.", "red"))
      print(colored(("Error: " + str(err)), "red"))
      e = sys.exc_info()[0]
      print(e)
      traceback.print_exc()
      sys.exit(1)

    ## Step 5: Re-swapping the URL's and terminating the green environment.
    try:
      print(colored("Re-swapping the URL's and terminating the green environment.", "blue"))
      terminate_green_env.main()
      print(colored("The blue environment has terminated successfully.", "green"))
      print(colored("The URL's has reswapped successfully.", "green"))
    except Exception as err:
      print(colored("Re-swapping the URL's and terminating the green environment has failed!", "red"))
      print(colored(("Error: " + str(err)), "red"))
      e = sys.exc_info()[0]
      print(e)
      traceback.print_exc()
      sys.exit(1)


if __name__ == "__main__":
  try:
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
    AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")
    AWS_ROLE = os.getenv("AWS_ROLE")
    BLUE_ENV_NAME = os.getenv("BLUE_ENV_NAME")
    GREEN_ENV_NAME = os.getenv("GREEN_ENV_NAME")
    BEANSTALK_APP_NAME = os.getenv("BEANSTALK_APP_NAME")
    S3_ARTIFACTS_BUCKET=os.getenv('S3_ARTIFACTS_BUCKET')
    print(colored("Successfully get envs", "green"))
  except Exception as e:
    print("Failed to get environment variable")
    print(str(e))
    e = sys.exc_info()[0]
    traceback.print_exc()
    sys.exit(1)
  main()