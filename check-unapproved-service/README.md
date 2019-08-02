# Check and notify if anyone is using unapproved service

This solution leverages the use of CloudWatch log group in which CloudTrail logs are sent to CloudWatch log group. You can also aggregate the CloudTrail logs in all of the member account in a centralized CloudWatch log group. More info can be found here:
Source: https://aws.amazon.com/blogs/architecture/stream-amazon-cloudwatch-logs-to-a-centralized-account-for-audit-and-analysis/ 

The function will check for any usage of unapproved service in AWS for the last 15 minutes and send out notification via sns
* Deploy the lambda function with Python3.7

* Change the white list according to the environment
Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html
Example rule to whitelist apigateway, cloudformattion and cloudfront:
```
{$.eventSource!=apigateway*&&$.eventSource!=autoscaling*&&$.eventSource!=cloudf*}
```

* Set up a cron job with CloudWatch Event to trigger the function every 15 mins
