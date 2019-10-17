import json
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
#from requests_aws4auth import AWS4Auth
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/665243609809/Q1'

    # Receive message from SQS queue
    response = sqs.receive_message(QueueUrl=queue_url,AttributeNames=['All'],MaxNumberOfMessages=1,MessageAttributeNames=['All'],VisibilityTimeout=0,WaitTimeSeconds=0)
    
    if (response and 'Messages' in response):
        
        host = 'search-restaurants-7grqg7diy6bkcp2u6vmuqniu3a.us-east-1.es.amazonaws.com' 
        region = 'us-east-1'
        service = 'es'
        
        es = Elasticsearch(
            hosts = [{'host': host, 'port': 443}],
            use_ssl = True,
            verify_certs = True,
            connection_class = RequestsHttpConnection
        )
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('yelp-restaurants')
        
        for message in response['Messages']:
            logger.info(message)
            receipt_handle = message['ReceiptHandle']
            req_attributes = message['MessageAttributes'] 
            res_cuisine = req_attributes['Cuisine']['StringValue']


            searchData = es.search(index="restaurants", body={
                                                "query": {
                                                    "match": {
                                                        "cuisine": res_cuisine
                                                    }}})
           
            logger.info("Total number of Hits: ")
            logger.info(searchData['hits']['total'])
            
            businessIds = []
            for hit in searchData['hits']['hits']:
                businessIds.append(hit['_source']['id'])
                logger.info(hit['_source']['id'])
            
            # Call the DynamoDB
            resultData = getDynamoDbData(table, req_attributes, businessIds)
            logger.info(resultData)
            logger.info(type(resultData))
            logger.info('req_attributes----')
            logger.info(req_attributes)
            
            # send the email
            sendMailToUser(req_attributes, resultData)
            
            # Delete received message from queue
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
    

def getDynamoDbData(table, requestData, businessIds):
    
    if len(businessIds) <= 0:
        return 'We can not find any restaurant under this description, please try again.'
    
    #textString = "Hello! Here are my " + requestData['Categories']['StringValue'] + " restaurant suggestions for " + requestData['PeopleNum']['StringValue'] +" people, for " + requestData['DiningDate']['StringValue'] + " at " + requestData['DiningTime']['StringValue'] + ". "
    count = 1
    textString=""
    logger.info("Inside getDynamoDbData")
    for business in businessIds:
        responseData = table.query(KeyConditionExpression=Key('id').eq(business))
        logger.info("responseData")
        logger.info(responseData)
        if (responseData and len(responseData['Items']) >= 1 and responseData['Items'][0]):
            responseData = responseData['Items'][0]
            display_address = ', '.join(responseData['address'])
            
            textString = textString + " " + str(count) + "." + responseData['name'] + ", located at " + display_address + " "
            count += 1
    
    textString = textString + " Enjoy your meal!"
    logger.info("textString")
    logger.info(textString)
    return textString

def sendMailToUser(requestData, resultData):
    logger.info("Inside sendMailToUser")
    RECIPIENT = requestData['Phone']['StringValue']
    logger.info(RECIPIENT)
    AWS_REGION = "us-east-1"      
    
    # Create a new SES resource and specify a region.
    client = boto3.client('sns',region_name=AWS_REGION)
    
    try:
        response = client.publish(
            PhoneNumber = RECIPIENT,
            Message="Hi User, Following are your restaurant suggestions" + resultData
        )
        logger.info(response)
    # Display an error if something goes wrong. 
    except ClientError as e:
        logger.info(e.response['Error']['Message'])
    else:
        logger.info("Text message sent! Message ID:"),
        logger.info(response['MessageId'])