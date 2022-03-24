ifdef DNX
	export GOOGLE_IDP_ID=C01501d06
	export GOOGLE_SP_ID=192607830114
endif

export AWS_DEFAULT_REGION=ap-southeast-2
export BLUE_ENV_NAME=DotNetFrameworkApp-API-env
export GREEN_ENV_NAME=DotNetFrameworkApp-API-env-green
export BEANSTALK_APP_NAME=DotNetFrameworkApp-API
export CREATE_CONFIG_TEMPLATE_NAME=BlueEnvConfig
export BLUE_CNAME_CONFIG_FILE=blue_cname.json
export ENV=Debug
export ARTIFACTS_S3_BUCKET=dnx-bluegreen-docker

env-%: # Check for specific environment variables
	@ if [ "${${*}}" = "" ]; then echo "Environment variable $* not set"; exit 1;fi

.env:
	cp .env.template .env
	echo >> .env
	touch .env.auth
	touch .env.assume

google-auth: .env env-GOOGLE_IDP_ID env-GOOGLE_SP_ID
	@echo "make .env.auth"
	docker-compose run --rm google-auth

.env.assume: .env .env.assume env-AWS_ACCOUNT_ID env-AWS_ROLE
	echo > .env.assume
	docker-compose pull aws
	docker-compose run --rm aws assume-role.sh > .env.assume
	cat .env.assume >> .env