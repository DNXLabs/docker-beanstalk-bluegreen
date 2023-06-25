IMAGE_NAME ?= dnxsolutions/beanstalk-bluegreen:latest

env-%: # Check for specific environment variables
	@ if [ "${${*}}" = "" ]; then echo "Environment variable $* not set"; exit 1;fi

.env:
	cp .env.template .env
	echo >> .env
	touch .env.auth
	touch .env.assume

.env.assume: .env .env.assume env-AWS_ACCOUNT_ID env-AWS_ROLE
	echo > .env.assume
	docker-compose pull aws
	docker-compose run --rm aws assume-role.sh > .env.assume
	cat .env.assume >> .env

build:
	docker build -t $(IMAGE_NAME) .

shell:
	docker run --rm -it --entrypoint=/bin/bash -v ~/.aws:/root/.aws -v $(PWD):/opt/app $(IMAGE_NAME)
