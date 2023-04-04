import boto3
import os



def create_route53_record(route53_client):
    response = route53_client.get_hosted_zone(
        Id='Z01998683H70F4Z45TM26',
    )
    print(response)
    zone_id = response['HostedZone']['Id']
    response = route53_client.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch={
            "Comment": "Automatic DNS update",
            "Changes": [
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Type": "CNAME",
                        "Name": "route53test.prod2.mydeal.com.au",
                        "Region": "ap-southeast-2",
                        "SetIdentifier": "Testing route53",
                        "TTL": 60,
                        "ResourceRecords": [
                            {
                                "Value": "www.google.com",
                            },
                        ],
                    }
                },
            ]
        }
    )

def get_boto_client():
    print("AUTH_METHOD: " + str(os.getenv('AUTH_METHOD')))
    if os.getenv('AUTH_METHOD') == 'SSO':
        boto3.setup_default_session(profile_name=os.getenv('SSO_PROFILE'))
        print("SSO Authentication")
    else:
        print("AWS KEYS authentication")
    return boto3


def get_beanstalk_environtment(beanstalk_client, application_name, template_name, environment_name):
    response = beanstalk_client.describe_configuration_settings(
        ApplicationName=application_name,
        EnvironmentName=environment_name
    )

    test = response["ConfigurationSettings"][0]["OptionSettings"][36]

    print(response)
    print()
    print(test)


def get_ssm_parameter(client, parameter_name):
    response = client.get_parameter(
        Name=parameter_name
    )
    print(response)
    print(eval(response['Parameter']['Value']))
    print(eval(response['Parameter']['Value'])[0])
    print(eval(response['Parameter']['Value'])[1])
    print(len(eval(response['Parameter']['Value'])))
    return response




if __name__ == '__main__':
    client = get_boto_client()
    # route53_client = client.client('route53', region_name='ap-southeast-2')
    # beanstalk_client = client.client('elasticbeanstalk', region_name='ap-southeast-2')
    ssm_client = client.client('ssm', region_name='ap-southeast-2')
    # create_route53_record(route53_client)
    # get_beanstalk_environtment(beanstalk_client, "MydealWeb", "template_name", "MyDealWeb-prod-green")
    get_ssm_parameter(ssm_client, "MyDealWeb")