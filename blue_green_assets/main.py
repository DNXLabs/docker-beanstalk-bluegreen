import os
import traceback
import sys
import clone_blue_environment
import swap_environment
import deploy_release
import release_health_check
import terminate_green_env
from termcolor import colored
import aws_authentication

def main():
    BLUE_ENV_NAME = os.getenv("BLUE_ENV_NAME")
    GREEN_ENV_NAME = os.getenv("GREEN_ENV_NAME")
    BEANSTALK_APP_NAME = os.getenv("BEANSTALK_APP_NAME")
    S3_ARTIFACTS_BUCKET = os.getenv("S3_ARTIFACTS_BUCKET")
    S3_ARTIFACTS_OBJECT = os.getenv("S3_ARTIFACTS_OBJECT")

    boto_authenticated_client = aws_authentication.get_boto_client()
  
    # print(colored('hello', 'red'), colored('world', 'green'))
    print(colored("Initiating blue green deployment process", "blue"))
    if str(sys.argv[1]) == 'deploy':
      ## Step 1: Cloning the blue env into green env.
      try:
        print(colored("Clonning the blue environment", "blue"))
        clone_blue_environment.main(BLUE_ENV_NAME, GREEN_ENV_NAME, BEANSTALK_APP_NAME, S3_ARTIFACTS_BUCKET, boto_authenticated_client)
      except Exception as err:
        print(colored("Clonning the blue environment environment has failed!", "red"))
        print(colored( ("Error: " + str(err)), "red"))
        e = sys.exc_info()[0]
        print(colored(e, "red"))
        traceback.print_exc()
        sys.exit(1)
      
      ## Step 2: Swapping blue and green envs URL's.
      try:
        print(colored("Swapping environment URL's", "blue"))
        swap_environment.main(BLUE_ENV_NAME, GREEN_ENV_NAME, S3_ARTIFACTS_BUCKET, boto_authenticated_client)
        print(colored("URL's swap task finished succesfully", "green"))
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
        deploy_release.main(S3_ARTIFACTS_OBJECT, S3_ARTIFACTS_BUCKET, BLUE_ENV_NAME, BEANSTALK_APP_NAME, boto_authenticated_client)
        print(colored("New release was deployed successfully.", "green"))
      except Exception as err:
        print(colored("New release deployment has failed.", "red"))
        print(colored(("Error: " + str(err)), "red"))
        e = sys.exc_info()[0]
        print(e)
        traceback.print_exc()
        sys.exit(1)

      # Step 4: Health checking new release deployment.
      try:
        print(colored("Health checking the new release.", "blue"))
        release_health_check.main(BLUE_ENV_NAME, boto_authenticated_client)
        print(colored("Environment is healthy!", "green"))
      except Exception as err:
        print(colored("Environment health check has failed!", "red"))
        print(colored(("Error: " + str(err)), "red"))
        e = sys.exc_info()[0]
        print(e)
        traceback.print_exc()
        sys.exit(1)

    ## Step 5: Re-swapping the URL's and terminating the green environment.
    if str(sys.argv[1]) == 'cutover':
      try:
        print(colored("Re-swapping the URL's and terminating the green environment.", "blue"))
        terminate_green_env.main(BLUE_ENV_NAME, GREEN_ENV_NAME, BEANSTALK_APP_NAME, boto_authenticated_client)
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
    if "AWS_DEFAULT_REGION" not in os.environ:
        raise Exception("The environment AWS_DEFAULT_REGION wasn't exposed to the container")
    if "AWS_ACCOUNT_ID" not in os.environ:
        raise Exception("The environment AWS_ACCOUNT_ID wasn't exposed to the container")
    if "AWS_ROLE" not in os.environ:
        raise Exception("The environment AWS_ROLE wasn't exposed to the container")
    if "BLUE_ENV_NAME" not in os.environ:
        raise Exception("The environment BLUE_ENV_NAME wasn't exposed to the container")
    if "GREEN_ENV_NAME" not in os.environ:
        raise Exception("The environment GREEN_ENV_NAME wasn't exposed to the container")
    if "BEANSTALK_APP_NAME" not in os.environ:
        raise Exception("The environment BEANSTALK_APP_NAME wasn't exposed to the container")
    if "S3_ARTIFACTS_BUCKET" not in os.environ:
        raise Exception("The environment S3_ARTIFACTS_BUCKET wasn't exposed to the container")
    if "S3_ARTIFACTS_OBJECT" not in os.environ:
        raise Exception("The environment S3_ARTIFACTS_OBJECT wasn't exposed to the container")
    print(colored("Successfully validated environment variables", "green"))
  except Exception as e:
    print("Failed to get environment variable")
    print(str(e))
    e = sys.exc_info()[0]
    traceback.print_exc()
    sys.exit(1)
  main()