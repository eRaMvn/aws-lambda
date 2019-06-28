# Forwarding CloudTrail Logs to Elasticsearch

* Have you ever had issues with the logging format of Cloudtrail when it is sent to S3? 
* You have tried with logstash but the logging format is not right and you are using the filter something like this:
```
filter {
    if "cloudtrail" in [tags] {
        json {
            source => "message"
        }
        split {
            field => "Records
        }
    }
}
```
The problem with this approach is that Elasticsearch will stop ingesting cloudtrail logs after a certain number of records and there have been many posts on forums, but no answer
* You want to implement centralized logging solution on aws, but aws does not provide a way to send cloudwatch log group cross account
* You tried to use firehose to send logs cross account and cross region, but the problem with firehose is that even though firehose can send logs directly to elasticsearch, the output format of firehose is impossible to read, and require a lambda function to transform

# The Solution

* You can easily forward CloudTrail logs cross account to a centralized bucket
* Implement the lambda function in this repo
    
    * Make sure that you set out about 300 Mb of ram and change the timeout to 20 - 30 seconds

* Create an event that triggers the lambda function when there is a new object put in the S3 bucket
* Implement the logstash as follows:

```
input {
  s3 {
    "access_key_id" => "[your key]"
    "secret_access_key" => "[your key]"
    "bucket" => "[your bucket name]"
    "region" => "us-west-2"
    "prefix" => "CloudTrailTransformed"
    "tags"   => "cloudtrail"
    "interval" => "300"
    "temporary_directory" => "/your/directory"
    "codec" => "json"
  }
}

filter {
    if "cloudtrail" in [tags] {
        json {
            source => "message"
        }
    }
}
output {
    if "cloudtrail" in [tags] {
        amazon_es {
        hosts => ["your stack"]
        region => "us-west-2"
        aws_access_key_id => '[your key]'
        aws_secret_access_key => '[your key]'
        index => "cloudtrail-logs-%{+YYYY.MM.dd}"
        }
    }
}
```

### I have successfully deployed this solution myself after countless hours doing research. Hopefully, this would help someone :)