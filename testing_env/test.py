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


if __name__ == '__main__':
    client = get_boto_client()
    route53_client = client.client('route53', region_name='ap-southeast-2')
    create_route53_record(route53_client)