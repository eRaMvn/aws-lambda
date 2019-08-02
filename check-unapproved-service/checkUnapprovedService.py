import json
import os
import boto3
import time
import functools

# Log error to console
def log_event_on_error(handler):
    @functools.wraps(handler)
    def wrapper(event, context):
        try:
            return handler(event, context)
        except Exception:
            print('event = %r' % event)
            raise

    return wrapper
    
client = boto3.client('logs')
sns = boto3.client('sns')

@log_event_on_error
def lambda_handler(event, context):
    
    current_time = int(round(time.time() * 1000))
    
    # Run every 15 minutes = 900000
    # Add your own whitelist: the syntax is similar to {$.eventSource!=apigateway*&&$.eventSource!=autoscaling*&&$.eventSource!=cloudf*}
    response = client.filter_log_events(
        logGroupName='CloudTrailPOC',
        filterPattern='{$.eventSource!=apigateway*&&$.eventSource!=autoscaling*&&$.eventSource!=cloudf*}',
        startTime= current_time - 900000
    )
 
    for each_event in response['events']:
        message = json.loads(each_event['message'])
        
        # If it is a console login event, skip this event
        if message["eventName"] == "ConsoleLogin":
            continue
        # If dome9 invoke the api, skip this event
        elif "guardduty" in message["userIdentity"]['sessionContext']['sessionIssuer']['userName'].lower():
            continue
        elif "dome9" in message["userIdentity"]['sessionContext']['sessionIssuer']['userName'].lower():
            continue
        
        # Publish a simple message to the specified SNS topic
        sns.publish(
            TopicArn='arn:aws:sns:us-west-2:12345678901:unapproved',    
            Message=f""" 
            User: 			{message["userIdentity"]["arn"].split(':')[5].split('/')[2]} 
            Assumed the role:   	{message["userIdentity"]['sessionContext']['sessionIssuer']['userName']}
            Used the service:     	{message["eventSource"]}
            Performed in account: 	{message["recipientAccountId"]}
            Region: 		 	{message["awsRegion"]}
            At: 			{message["eventTime"]}   
            """,
            Subject="ALERT: Unapproved service is being used!"
        )
    return "Done"