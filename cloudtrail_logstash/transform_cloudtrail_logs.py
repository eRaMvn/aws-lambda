import json
import boto3
import gzip
import os
from io import BytesIO

def lambda_handler(event, context):
    
    s3 = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    gzip_key = event["Records"][0]["s3"]["object"]["key"]
    
    # Name of the uncompressed file
    uncompressed_key = "temp"
    
    s3.upload_fileobj(                      # upload a new obj to s3
    Fileobj=gzip.GzipFile(              # read in the output of gzip -d
        None,                           # just return output as BytesIO
        'rb',                           # read binary
        fileobj=BytesIO(s3.get_object(Bucket=bucket, Key=gzip_key)['Body'].read())),
    Bucket=bucket,                      # target bucket, writing to
    Key=uncompressed_key)               # target key, writing to
    
    # Get the temporary file that was uploaded
    response = s3.get_object(Bucket=bucket, Key=uncompressed_key)
    
    # Only obtain the data from the response, the content of the log file
    file_content = json.loads(response['Body'].read())
    
    # Write the events to file in the correct format
    with open(os.path.join('/tmp/','temp'), "w") as f:
        for item in file_content['Records']:
            f.write("%s\n" % json.dumps(item))
    
    #Format the output file name
    file_name = "CloudtrailTransformed/" + gzip_key.split('.')[0].split('/')[-1] + ".json"
    
    # Reupload the file to S3
    s3_resource.Bucket(bucket).upload_file("/tmp/temp", file_name)
    
    
    return "Done!"
