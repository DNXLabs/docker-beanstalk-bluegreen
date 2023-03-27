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

    available_execution_types = ["deploy", "cutover", "full"]
    execution_type = str(sys.argv[1])

    if execution_type not in available_execution_types:
      print("Not valid execution type argument: " + execution_type)
      print(
            "Available execution types are: \n\
              -> deploy: Create a new environment, swap URL's and deploy the new release.\n\
              -> cutover: Apply health checks, reswap URL's and terminate environments.\n\
              -> full: Apply deploy and then cutover"
              )
      
      sys.exit(1)

    boto_authenticated_client = aws_authentication.get_boto_client()
    print("Execution Type: " + execution_type)
    print(colored("Initiating blue green deployment process", "blue"))
    if execution_type == "deploy" or execution_type == "full":
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
      boto_authenticated_client = aws_authentication.get_boto_client()
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
      boto_authenticated_client = aws_authentication.get_boto_client()
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

    boto_authenticated_client = aws_authentication.get_boto_client()
    ## Start cutover phase
    if execution_type == "cutover" or execution_type == "full":
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
      boto_authenticated_client = aws_authentication.get_boto_client()
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
        raise Exception("The environment variable AWS_DEFAULT_REGION wasn't exposed to the container")
    if "AWS_ACCOUNT_ID" not in os.environ:
        raise Exception("The environment variable AWS_ACCOUNT_ID wasn't exposed to the container")
    if "AWS_ROLE" not in os.environ:
        raise Exception("The environment variable AWS_ROLE wasn't exposed to the container")
    if "BLUE_ENV_NAME" not in os.environ:
        raise Exception("The environment variable BLUE_ENV_NAME wasn't exposed to the container")
    if "GREEN_ENV_NAME" not in os.environ:
        raise Exception("The environment variable GREEN_ENV_NAME wasn't exposed to the container")
    if "BEANSTALK_APP_NAME" not in os.environ:
        raise Exception("The environment variable BEANSTALK_APP_NAME wasn't exposed to the container")
    if "S3_ARTIFACTS_BUCKET" not in os.environ:
        raise Exception("The environment variable S3_ARTIFACTS_BUCKET wasn't exposed to the container")
    if "S3_ARTIFACTS_OBJECT" not in os.environ:
        raise Exception("The environment variable S3_ARTIFACTS_OBJECT wasn't exposed to the container")
    print(colored("Successfully validated environment variables", "green"))
  except Exception as e:
    print("Failed to get environment variable")
    print(str(e))
    e = sys.exc_info()[0]
    traceback.print_exc()
    sys.exit(1)
  main()