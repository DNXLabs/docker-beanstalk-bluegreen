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

build:
	docker build -t $(IMAGE_NAME) .