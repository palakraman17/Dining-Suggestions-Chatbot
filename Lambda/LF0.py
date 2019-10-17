import json
import boto3


client = boto3.client('lex-runtime', region_name='us-east-1')

def lambda_handler(event, context):
    lastUserMessage=event['message']
    botMessage = "Please try again.";
    print(context)


   
    if lastUserMessage is None or len(lastUserMessage) < 1:
        return {
            'statusCode': 200,
            'body': json.dumps(botMessage)
        }
        
    response = client.post_text(botName='FoodBot',
        botAlias='bot',
        userId = 'testUser',
        inputText=lastUserMessage)
    
    if response['message'] is not None or len(response['message']) > 0:
        lastUserMessage = response['message']
    
    
    return {
        'statusCode': 200,
        'body': json.dumps(lastUserMessage)
    }
