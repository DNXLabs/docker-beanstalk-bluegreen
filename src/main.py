import os
import traceback
import sys

import clone_blue_environment
import swap_environment
import deploy_release
import release_health_check
import terminate_green_env
import aws_authentication
import time


def main():
    print("------------Initiating blue green deployment process------------\n\n\n")
    starting_time = time.time()

    BLUE_ENV_NAME = os.getenv("BLUE_ENV_NAME")
    GREEN_ENV_NAME = os.getenv("GREEN_ENV_NAME")
    BEANSTALK_APP_NAME = os.getenv("BEANSTALK_APP_NAME")
    S3_ARTIFACTS_BUCKET = os.getenv("S3_ARTIFACTS_BUCKET")
    VERSION_LABEL = os.environ['VERSION_LABEL']

    print("Environment variables: \n")
    print(f"BLUE_ENV_NAME = {BLUE_ENV_NAME}\n")
    print(f"GREEN_ENV_NAME = {GREEN_ENV_NAME}\n")
    print(f"BEANSTALK_APP_NAME = {BEANSTALK_APP_NAME}\n")
    print(f"VERSION_LABEL = {VERSION_LABEL}\n")
    print(f"S3_ARTIFACTS_BUCKET = {S3_ARTIFACTS_BUCKET}\n")

    available_execution_types = ["deploy", "cutover", "full", "rollback"]
    execution_type: str = str(sys.argv[1])

    if execution_type not in available_execution_types:
        print("Not valid execution type argument: " + execution_type)
        print(
            "Available execution types are: \n\
            -> deploy: Create a new environment, swap URL's and deploy the new release.\n\
            -> cutover: Apply health checks, reswap URL's and terminate environments.\n\
            -> full: Apply deploy and then cutover. \n\
            -> rollback: rollback tp specific application version label"
        )
        sys.exit(1)

    boto_authenticated_client = aws_authentication.get_boto_client()
    print(f"\n Execution Type: {execution_type}\n")

    if execution_type == "deploy" or execution_type == "full":
        print("\n\n\n ------------------ Stating Deployment Step 1 --------------------- \n")
        print("------------------ Creating Green Env --------------------- \n\n\n")

        # Step 1: Cloning the blue env into green env.
        try:
            print("Cloning the blue environment...")
            start_1 = time.time()
            clone_blue_environment.main(
                BLUE_ENV_NAME, GREEN_ENV_NAME, BEANSTALK_APP_NAME, S3_ARTIFACTS_BUCKET, boto_authenticated_client)
            print(f"Clonning the blue environment has finished successfully!\n\
                  \tIt took: {time.time() - start_1} seconds\n")
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
        print("\n\n\n ------------------ Stating Step 2 ---------------------\n")
        print("------------------ Swapping Domains --------------------- \n\n\n")

        # Step 2: Swapping blue and green envs URL's.
        try:
            print("Swapping environment Domains...")
            start_2 = time.time()
            swap_environment.main(BLUE_ENV_NAME, GREEN_ENV_NAME, S3_ARTIFACTS_BUCKET,
                                  BEANSTALK_APP_NAME, boto_authenticated_client)
            print(f"Swapping environment Domains has finished successfully!\n\
                    \tIt took: {time.time() - start_2} seconds\n")
        except Exception as err:
            print("Swap environment has failed.")
            print(("Error: " + str(err)))
            swap_environment.re_swap_dns(
                boto_authenticated_client, S3_ARTIFACTS_BUCKET, GREEN_ENV_NAME, BLUE_ENV_NAME)
            clone_blue_environment.rollback_created_env(
                boto_authenticated_client, GREEN_ENV_NAME)
            print("re-swap environment domain has done.")
            e = sys.exc_info()[0]
            print(e)
            traceback.print_exc()
            sys.exit(1)

        boto_authenticated_client = aws_authentication.get_boto_client()
        print("\n\n\n ------------------ Stating Step 3 --------------------- \n")
        print("----------------- New release Deployment --------------------- \n\n\n")

        ## Step 3: Deploying the new release into the blue env.
        try:
            print("New release deployment initiated on blue environment.")
            start_3 = time.time()
            deploy_release.release_deployment(BLUE_ENV_NAME, BEANSTALK_APP_NAME, VERSION_LABEL,
                                              boto_authenticated_client)
            print(f"New release deployment has finished successfully!\n\
                    \tIt took: {time.time() - start_3} seconds\n")
        except Exception as err:
            print("New release deployment has failed.")
            print(("Error: " + str(err)))
            e = sys.exc_info()[0]
            print(e)
            traceback.print_exc()
            sys.exit(1)

    # Start cutover phase
    if execution_type == "cutover" or execution_type == "full":
        # Step 4: Health checking new release deployment.
        try:
            print(f"Health checking the new release on {BLUE_ENV_NAME} env.")
            release_health_check.main(BLUE_ENV_NAME, boto_authenticated_client)
            print(f"{BLUE_ENV_NAME} Environment is healthy!")
        except Exception as err:
            print("Environment health check has failed!")
            print(("Error: " + str(err)))
            e = sys.exc_info()[0]
            print(e)
            traceback.print_exc()
            sys.exit(1)

        # Step 5: Re-swapping the URL's and terminating the green environment.
        print("\n\n\n ------------------ Stating Cutover --------------------- \n")
        boto_authenticated_client = aws_authentication.get_boto_client()
        try:
            print("Re-swapping the URL's and terminating the green environment.")
            time_4 = time.time()
            terminate_green_env.main(
                BLUE_ENV_NAME, GREEN_ENV_NAME, BEANSTALK_APP_NAME, boto_authenticated_client)
            print(f"Re-swapping the URL's and terminating the green environment has finished successfully!\n\
                    \tIt took: {time.time() - time_4} seconds\n")
        except Exception as err:
            print(
                "Re-swapping the URL's and terminating the green environment has failed!")
            print(("Error: " + str(err)))
            e = sys.exc_info()[0]
            print(e)
            traceback.print_exc()
            sys.exit(1)

    # Start rollback phase
    if execution_type == "rollback":
        try:
            print(f"Rolling back the blue environment to the specific version label {VERSION_LABEL}.")
            deploy_release.rollback_release(boto_authenticated_client, BEANSTALK_APP_NAME, BLUE_ENV_NAME, VERSION_LABEL)
            print("Rolling back the blue environment to the specific version label {VERSION_LABEL} successful.")
        except Exception as err:
            print("Rolling back the blue environment has failed!")
            print(("Error: " + str(err)))
            e = sys.exc_info()[0]
            print(e)
            traceback.print_exc()
            sys.exit(1)

        try:
            print("Re-swapping the URL's and terminating the green environment if applicable.")
            swap_environment.re_swap_dns(
                boto_authenticated_client, S3_ARTIFACTS_BUCKET, GREEN_ENV_NAME, BLUE_ENV_NAME)
        except Exception as err:
            print(
                "Re-swapping the URL's ...")
            print(("Error: " + str(err)))
            e = sys.exc_info()[0]
            print(e)
            traceback.print_exc()
            sys.exit(1)

        try:
            print("Terminated the Green environment if applicable.")
            clone_blue_environment.rollback_created_env(
                boto_authenticated_client, GREEN_ENV_NAME
            )
        except Exception as err:
            print("Rolling back the blue environment has failed!")
            print(("Error: " + str(err)))
            e = sys.exc_info()[0]
            print(e)
            traceback.print_exc()
            sys.exit(1)
        print("Rollback has finished successfully!")

    print("Deployment has finished successfully!")
    print(f"The process took: {round((time.time() - starting_time), 2)} seconds")


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
        if "VERSION_LABEL" not in os.environ:
            raise Exception(
                "The environment variable VERSION_LABEL wasn't exposed to the container")
    except Exception as e:
        print("Failed to get environment variable")
        print(str(e))
        e = sys.exc_info()[0]
        traceback.print_exc()
        sys.exit(1)
    main()