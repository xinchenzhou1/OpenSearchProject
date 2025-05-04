
 #Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 #
 # Permission is hereby granted, free of charge, to any person obtaining a copy of this
 # software and associated documentation files (the "Software"), to deal in the Software
 # without restriction, including without limitation the rights to use, copy, modify,
 # merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
 # permit persons to whom the Software is furnished to do so.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 # INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
 # PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 # HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 # OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 # SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import logging
import boto3
import json
import requests
from requests_aws4auth import AWS4Auth
from requests.auth import HTTPBasicAuth

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3 = boto3.client('s3')
region = 'us-east-1' # For example, us-west-1
sts_client = boto3.client('sts', region_name=region, endpoint_url='https://sts.' + region + '.amazonaws.com')
service = 'es'
host = '<ElasticSearchEndpoint>' # The ES domain endpoint with https:// and a trailing slash
index = 'tenant-data' # This is the index name and should be same as provided in the permission of Kibana role
type = '_doc'
post_url = host + '/' + index + '/' + type
account_id = '<AWS-Account-Id>'

# Lambda execution starts here
def lambda_handler(event, context):

    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_key = event['Records'][0]['s3']['object']['key']
    logger.info('Reading {} from {}'.format(file_key, bucket_name))
    # get the object
    obj = s3.get_object(Bucket=bucket_name, Key=file_key)
    # get content from the body
    content = obj['Body']
    jsonObject = json.loads(content.read())

    tenantId = jsonObject['TenantId']
    rolename = tenantId + '-role'
    #constructing the tenant arn to assume the role
    rolearn = 'arn:aws:iam::' + account_id + ':role/' + rolename

    # we are assuming a tenant specific role
    assumed_role_object=sts_client.assume_role(
        RoleArn=rolearn,
        RoleSessionName="AssumeRoleSession"
    )
    credentials=assumed_role_object['Credentials']
    awsauth = AWS4Auth(credentials['AccessKeyId'], credentials['SecretAccessKey'], region, service, session_token=credentials['SessionToken'])

    req_data = jsonObject
    # ES 6.x requires an explicit Content-Type header
    headers = { "Content-Type": "application/json" }
    # Make the signed HTTP request
    r = requests.post(post_url, auth=awsauth, headers=headers, json=req_data)
    # Create the response
    response = {
        "statusCode": 200,
        "isBase64Encoded": False
    }
    # Add the search results to the response
    response['body'] = r.text
    return response
