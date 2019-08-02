from __future__ import print_function
import json
import boto3


def lambda_handler(event, context):

    # Dump event to cloudwatch log
    print('Event: ' + str(event))
    print('Received event: ' + json.dumps(event))

    # List of ids including ec2 instance, image, volume, snapshot, eni
    ids = []

    try:
        # Get some info from the event
        region = event['region']
        detail = event['detail']
        eventname = detail['eventName']
        principal = detail['userIdentity']['principalId']
        userType = detail['userIdentity']['type']

        client = boto3.client('iam')        

        # Check to see if this is an IAM user
        if userType == 'IAMUser':
            username = detail['userIdentity']['userName']
            # Get project tag       
            response = client.list_user_tags(UserName=username)
            tag = response['Tags'][0]['Value']
        elif userType == 'AssumedRole':
            username = detail['userIdentity']['sessionContext']["sessionIssuer"]['userName']
            response = client.list_role_tags(RoleName=username)
        tag = response['Tags'][0]['Value']        

        # Print out for troubleshooting    
        print('principalId: ' + str(principal))
        print('region: ' + str(region))
        print('eventName: ' + str(eventname))
        print('detail: ' + str(detail))

        # Code to check for error
        if not detail['responseElements']:
            print('Not responseElements found')
            if detail['errorCode']:
                print('errorCode: ' + detail['errorCode'])
            if detail['errorMessage']:
                print('errorMessage: ' + detail['errorMessage'])
            return False

        ec2 = boto3.resource('ec2')

        if eventname == 'CreateVolume':
            ids.append(detail['responseElements']['volumeId'])
            # print(ids)
        elif eventname == 'RunInstances':
            items = detail['responseElements']['instancesSet']['items']
            for item in items:
                ids.append(item['instanceId'])
            # print(ids)
            print('number of instances: ' + str(len(ids)))
            base = ec2.instances.filter(InstanceIds=ids)
            #loop through the instances to find volume id and eni id
            for instance in base:
                for vol in instance.volumes.all():
                    ids.append(vol.id)
                for eni in instance.network_interfaces:
                    ids.append(eni.id)
        elif eventname == 'CreateImage':
            ids.append(detail['responseElements']['imageId'])
            print(ids)
        elif eventname == 'CreateSnapshot':
            ids.append(detail['responseElements']['snapshotId'])
            print(ids)
        else:
            print('Not supported action')
        if ids:
            for resourceid in ids:
                print('Tagging resource ' + resourceid)
            ec2.create_tags(Resources=ids, Tags=[{'Key': 'project', 'Value': tag}])
        print('Done!')
        return True
    except Exception as e:
        print('Something went wrong: ' + str(e))
        return False