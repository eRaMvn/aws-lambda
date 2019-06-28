from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

AWS_EMAIL_REGION='us-east-1'
EMAIL_FROM = "[source email]"
EMAIL_TO = "[destination email]"
MAX_AGE = 9

iam = boto3.client('iam')
ses = boto3.client('ses', region_name=AWS_EMAIL_REGION)

def lambda_handler(event, context):
    paginator = iam.get_paginator('list_users')

    for response in paginator.paginate():
        for user in response['Users']:
            username = user['UserName']
            res = iam.list_access_keys(UserName=username)

            for access_key in res['AccessKeyMetadata']:
                access_key_id = access_key['AccessKeyId']
                create_date = access_key['CreateDate']
                print(f'User: {username} {access_key_id} {create_date}')

                age = days_old(create_date)
                if age < MAX_AGE:
                    continue

                # Expire the key
                print(f'Key {access_key_id} for user {username} is expired {age} days.')

                iam.update_access_key(
                    UserName=username,
                    AccessKeyId=access_key_id,
                    Status='Inactive'
                )

                # Create new credentials
                new_credentials = iam.create_access_key(UserName=username)
                send_email_report(EMAIL_TO, username, age, access_key_id, new_credentials)

def days_old(create_date):
    now = datetime.now(timezone.utc)
    age = now - create_date
    return age.days

def send_email_report(email_to, username, age, access_key_id, new_credentials):
    new_access_key_id = new_credentials['AccessKey']['AccessKeyId']
    new_secret_key_id = new_credentials['AccessKey']['SecretAccessKey']
    data = f"""
    Hi,

    Access key {access_key_id} belonging to user {username} has been automatically deactivated due to it being {age} days old.
    Your new access key is {new_access_key_id}
    Your new secret key is {new_secret_key_id}

    Thanks,

    """

    try:
        response = ses.send_email(
            Source = EMAIL_FROM,
            Destination={
                'ToAddresses':[EMAIL_TO]
            },
            Message={
                'Subject':{
                    'Data':(f'AWS IAM Access Key Rotation - Deactivation of Access Keys: {access_key_id}')
                },
                'Body': {
                    'Text': {
                        'Data': data
                    }
                }
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:" + response['MessageId'])
