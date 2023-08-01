terraform {
  backend "s3" {
    bucket  = "testing-terraform-dnx"
    key     = "platform"
    region  = "us-east-1"
    encrypt = true
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Environment = "dev"
    }
  }
}


module "eb_windows" {
  source                         = "git::https://github.com/DNXLabs/terraform-aws-eb-windows.git?ref=2.7.2"
  name                           = "testingApplication"
  security_group_name            = "testing_eb_app_sg"
  eb_platform                    = "dotnet"
  eb_solution_stack_name         = "64bit Windows Server 2019 v2.11.4 running IIS 10.0"
  environment                    = "dev"
  environment_type               = "LoadBalanced"
  loadbalancer_type              = "application"
  application_subnets            = data.aws_subnets.public.ids
  loadbalancer_subnets           = data.aws_subnets.public.ids
  loadbalancer_idle_timeout      = 60
  elb_scheme                     = "public"
  instance_type                  = "t3a.small"
  vpc_id                         = data.aws_vpc.selected.id
  create_security_group          = false
  application_port               = 80
  http_listener_enabled          = true
  ingress_rules                  = []
  enable_stream_logs             = true
  healthcheck_url                = "/"
  healthcheck_httpcodes_to_match = ["200"]
  deployment_timeout             = 600
  eb_wait_for_ready_timeout      = "10m"
  asg_min                        = 1
  asg_max                        = 1
  rolling_update_enabled         = false
  rolling_update_type            = "Time"
  updating_min_in_service        = 0
  associate_public_ip_address    = true
  root_volume_size               = 30
  iam_role_policy_attachment_to_instance = [
    {
      "name" : "SecretsManagerReadWrite",
      "policy_arn" : "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
    },
    {
      "name" : "AWSXRayDaemonWriteAccess",
      "policy_arn" : "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
    },
    {
      "name" : "AmazonS3ReadOnlyAccess",
      "policy_arn" : "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
    },
  ]
}

data "aws_subnets" "public" {

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected.id]
  }

  filter {
    name   = "tag:Scheme"
    values = ["public"]
  }
}

data "aws_vpc" "selected" {
  filter {
    name   = "tag:Name"
    values = ["dev-VPC"]
  }
}
