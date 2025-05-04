
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
region = 'us-east-1' # For example, us-west-1
sts_client = boto3.client('sts', region_name=region, endpoint_url='https://sts.' + region + '.amazonaws.com')
service = 'es'
host = '<Elastic Search Endpoint>' # The ES domain endpoint with https:// and a trailing slash
index = '<Index Name>' # In our example is 'tenant-data' .This is the index name and should be same as provided in the permission of Kibana role.
type = '_doc'
url = host + '/' + index + '/_search'
account_id = '<AWS-Account-Id>'

# Lambda execution starts here
def lambda_handler(event, context):
    tenantId = event["queryStringParameters"]['TenantId']
    rolename = tenantId + '-role' # this is a sample guid, you should use the actual tenant Id or Guid here
    rolearn = 'arn:aws:iam::' + account_id + ':role/' + rolename

    # we are assuming a tenant specific role to ensure tenant specific permission applies in ES
    assumed_role_object=sts_client.assume_role(
        RoleArn=rolearn,
        RoleSessionName="AssumeRoleSession"
    )
    credentials=assumed_role_object['Credentials']
    awsauth = AWS4Auth(credentials['AccessKeyId'], credentials['SecretAccessKey'], region, service, session_token=credentials['SessionToken'])

    # sample query to fetch all documents, limiting to hits to returned to 1000
    query = {
        "size": 1000,
        "query": {
                    "match_all": {
                            }
            }
        }
    # ES 6.x requires an explicit Content-Type header
    headers = { "Content-Type": "application/json" }
    # Make the signed HTTP request
    logger.info('Sending the query to elastic search')
    r = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))

    # Create the response
    response = {
        "statusCode": 200,
        "isBase64Encoded": False
    }
    # Add the search results to the response
    response['body'] = r.text
    return response
