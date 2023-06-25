import os
import traceback
import sys
import clone_blue_environment
import swap_environment
import deploy_release
import release_health_check
import terminate_green_env
import aws_authentication


def main():
    BLUE_ENV_NAME = os.getenv("BLUE_ENV_NAME")
    GREEN_ENV_NAME = os.getenv("GREEN_ENV_NAME")
    BEANSTALK_APP_NAME = os.getenv("BEANSTALK_APP_NAME")
    S3_ARTIFACTS_BUCKET = os.getenv("S3_ARTIFACTS_BUCKET")
    S3_ARTIFACTS_OBJECT = os.getenv("S3_ARTIFACTS_OBJECT")

    print(f"BLUE_ENV_NAME = {BLUE_ENV_NAME}\n")
    print(f"GREEN_ENV_NAME = {GREEN_ENV_NAME}\n")
    print(f"BEANSTALK_APP_NAME = {BEANSTALK_APP_NAME}\n")
    print(f"S3_ARTIFACTS_BUCKET = {S3_ARTIFACTS_BUCKET}\n")
    print(f"S3_ARTIFACTS_OBJECT {S3_ARTIFACTS_OBJECT}\n")

    available_execution_types = ["deploy", "cutover", "full", "rollback"]
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
    print("Initiating blue green deployment process")
    print("\n\n\n ------------------ Initiating Step 1 --------------------- \n\n\n")
    print("\n\n\n ------------------ Creating Green Env --------------------- \n\n\n")
    if execution_type == "deploy" or execution_type == "full":
        # Step 1: Cloning the blue env into green env.
        try:
            print("Clonning the blue environment")
            clone_blue_environment.main(
                BLUE_ENV_NAME, GREEN_ENV_NAME, BEANSTALK_APP_NAME, S3_ARTIFACTS_BUCKET, boto_authenticated_client)
        except Exception as err:
            clone_blue_environment.rollback_created_env(
                boto_authenticated_client, GREEN_ENV_NAME
            )
            print("Clonning the blue environment environment has failed!")
            print(("Error: " + str(err)))
            e = sys.exc_info()[0]
            print(str(e))
            traceback.print_exc()
            sys.exit(1)
        boto_authenticated_client = aws_authentication.get_boto_client()
        # Step 2: Swapping blue and green envs URL's.
        try:
            print("Swapping environment URL's")
            swap_environment.main(BLUE_ENV_NAME, GREEN_ENV_NAME, S3_ARTIFACTS_BUCKET,
                                  BEANSTALK_APP_NAME, boto_authenticated_client)
            print("URL's swap task finished succesfully")
        except Exception as err:
            print("Swap environment has failed.")
            print(("Error: " + str(err)))
            swap_environment.re_swap_dns(
                boto_authenticated_client, S3_ARTIFACTS_BUCKET, GREEN_ENV_NAME, BLUE_ENV_NAME)
            clone_blue_environment.rollback_created_env(
                boto_authenticated_client, GREEN_ENV_NAME)

            e = sys.exc_info()[0]
            print(e)
            traceback.print_exc()
            sys.exit(1)
        boto_authenticated_client = aws_authentication.get_boto_client()
        # ## Step 3: Deploying the new release into the blue env.
        try:
            print("New release deployment initiated.")
            deploy_release.main(S3_ARTIFACTS_OBJECT, S3_ARTIFACTS_BUCKET,
                                BLUE_ENV_NAME, BEANSTALK_APP_NAME, boto_authenticated_client)
            print("New release was deployed successfully.")
        except Exception as err:
            print("New release deployment has failed.")
            print(("Error: " + str(err)))
            e = sys.exc_info()[0]
            print(e)
            traceback.print_exc()
            sys.exit(1)

    boto_authenticated_client = aws_authentication.get_boto_client()
    # Start cutover phase
    if execution_type == "cutover" or execution_type == "full":
        # Step 4: Health checking new release deployment.
        try:
            print("Health checking the new release.")
            release_health_check.main(BLUE_ENV_NAME, boto_authenticated_client)
            print("Environment is healthy!")
        except Exception as err:
            print("Environment health check has failed!")
            print(("Error: " + str(err)))
            e = sys.exc_info()[0]
            print(e)
            traceback.print_exc()
            sys.exit(1)

        # Step 5: Re-swapping the URL's and terminating the green environment.
        boto_authenticated_client = aws_authentication.get_boto_client()
        try:
            print("Re-swapping the URL's and terminating the green environment.")
            terminate_green_env.main(
                BLUE_ENV_NAME, GREEN_ENV_NAME, BEANSTALK_APP_NAME, boto_authenticated_client)
            print("The green environment has terminated successfully.")
            print("The URL's has reswapped successfully.")
        except Exception as err:
            print(
                "Re-swapping the URL's and terminating the green environment has failed!")
            print(("Error: " + str(err)))
            e = sys.exc_info()[0]
            print(e)
            traceback.print_exc()
            sys.exit(1)
    if execution_type == "rollback":
        try:
            print("Re-swapping the URL's and terminating the green environment.")
            swap_environment.re_swap_dns(
                boto_authenticated_client, S3_ARTIFACTS_BUCKET, GREEN_ENV_NAME, BLUE_ENV_NAME)
        except Exception as err:
            print(
                "Re-swapping the URL's and terminating the green environment has failed!")
            print(("Error: " + str(err)))
            e = sys.exc_info()[0]
            print(e)
            traceback.print_exc()
            sys.exit(1)
        try:
            print("Rolling back the blue environment.")
            clone_blue_environment.rollback_created_env(
                boto_authenticated_client, GREEN_ENV_NAME
            )
            print("The blue environment has rolled back successfully.")
        except Exception as err:
            print("Rolling back the blue environment has failed!")
            print(("Error: " + str(err)))
            e = sys.exc_info()[0]
            print(e)
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    try:
        if "AWS_DEFAULT_REGION" not in os.environ:
            raise Exception(
                "The environment variable AWS_DEFAULT_REGION wasn't exposed to the container")
        if "AWS_ACCOUNT_ID" not in os.environ:
            raise Exception(
                "The environment variable AWS_ACCOUNT_ID wasn't exposed to the container")
        if "AWS_ROLE" not in os.environ:
            raise Exception(
                "The environment variable AWS_ROLE wasn't exposed to the container")
        if "BLUE_ENV_NAME" not in os.environ:
            raise Exception(
                "The environment variable BLUE_ENV_NAME wasn't exposed to the container")
        if "GREEN_ENV_NAME" not in os.environ:
            raise Exception(
                "The environment variable GREEN_ENV_NAME wasn't exposed to the container")
        if "BEANSTALK_APP_NAME" not in os.environ:
            raise Exception(
                "The environment variable BEANSTALK_APP_NAME wasn't exposed to the container")
        if "S3_ARTIFACTS_BUCKET" not in os.environ:
            raise Exception(
                "The environment variable S3_ARTIFACTS_BUCKET wasn't exposed to the container")
        if "S3_ARTIFACTS_OBJECT" not in os.environ:
            raise Exception(
                "The environment variable S3_ARTIFACTS_OBJECT wasn't exposed to the container")
        print("Successfully validated environment variables")
    except Exception as e:
        print("Failed to get environment variable")
        print(str(e))
        e = sys.exc_info()[0]
        traceback.print_exc()
        sys.exit(1)
    main()

