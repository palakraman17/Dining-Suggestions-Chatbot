import math
import logging
import os
import dateutil.parser
import datetime
import time
import random
import json
import re
import boto3
from botocore.vendored import requests

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def validate_dining_suggestion(location, cuisine, num_people, date, time, phonenum):

    locations = ['east village','west village','soho','chelsea','midtown manhattan','upper east side','upper west side', 'midtown', 'manhattan', 'brooklyn', 'queens', 'bronx', 'staten island', 'jersey']
    if location is not None and location.lower() not in locations:
        return build_validation_result(False, 'Location', 'Location not available. Please try another.')
    
    cuisines = ['thai', 'chinese', 'indian', 'american', 'mexican', 'japanese', 'italian']
    if cuisine is not None and cuisine.lower() not in cuisines:
        return build_validation_result(False, 'Cuisine', 'Cuisine not available. Please try another.')
                                       
    if num_people is not None:
        num_people = int(num_people)
        if num_people > 20 or num_people <= 0:
            return build_validation_result(False, 'NumberOfPeople', 'Maximum 20 people allowed. Please try again with a valid value.')
    
    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'Date', 'I did not understand that, what date would you like to book?')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'Date', 'Please give a future month and date for this year.')





    if time is not None:
        if len(time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'Time', None)

        hour, minute = time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'Time', 'Sorry, this is not a valid time.')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() == datetime.date.today():
            if hour < datetime.datetime.now().hour:
               return build_validation_result(False, 'Time', 'Please give a future time for today.') 


        #if hour < 10 or hour > 16:
            # Outside of business hours
         #   return build_validation_result(False, 'Time', 'Our business hours are from 10 am to 5 pm. Can you please specify a time during this range?')
    
    if phonenum is not None:
        logger.info(phonenum)
        rule = re.compile(r'/^[0-9]{10,14}$/')
        if rule.search(phonenum):
            logger.info('Inside rule.search')
            return build_validation_result(False, 'Phone', 'Enter a valid phone number')

    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """
def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True   
    except:
        return False
    """
    except ValueError:
        return False
    """    

def dining_suggestion_intent(intent_request):
    """
    Performs dialog management and fulfillment for food recommendation.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """
    
    location = get_slots(intent_request)["Location"]
    cuisine = get_slots(intent_request)["Cuisine"]
    num_people = get_slots(intent_request)["NumberOfPeople"]
    date = get_slots(intent_request)["Date"]
    time = get_slots(intent_request)["Time"]
    phonenum = get_slots(intent_request)["Phone"]
    source = intent_request["invocationSource"]

    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_dining_suggestion(location, cuisine, num_people, date, time, phonenum)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        output_session_attributes = intent_request['sessionAttributes']
        return delegate(output_session_attributes, get_slots(intent_request))
    
    logger.info(type(location))
    logger.info(type(cuisine))
    logger.info(type(num_people))
    logger.info(type(date))
    logger.info(type(time))
    logger.info(type(phonenum))
    
    requestData = {
        "location":location,
        "cuisine":cuisine,
        "peoplenum": num_people,
        "Date": date,
        "Time": time,
        "Phone": phonenum
    }

    messageId = restaurantSQSRequest(requestData)
    return close(intent_request['sessionAttributes'],"Fulfilled",{"contentType": "PlainText","content": "Thanks! We will get back to you with the suggestions shortly."})

def restaurantSQSRequest(requestData):

    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/665243609809/Q1'
    #queue_url = 'https://sqs.us-east-1.amazonaws.com/665243609809/tempQueue'
    delaySeconds = 0
    messageAttributes = {
        'Location': {
            'DataType': 'String',
            'StringValue': requestData['location']
        },
        'Cuisine': {
            'DataType': 'String',
            'StringValue': requestData['cuisine']
        },
        "DiningTime": {
            'DataType': "String",
            'StringValue': requestData['Time']
        },
        "DiningDate": {
            'DataType': "String",
            'StringValue': requestData['Date']
        },
        'PeopleNum': {
            'DataType': 'String',
            'StringValue': requestData['peoplenum']
        },
        'Phone': {
            'DataType': 'String',
            'StringValue': requestData['Phone']
        }
    }
    messageBody= "Recommendation for the food"

    logger.info("calling send_message()")
    response = sqs.send_message(QueueUrl = queue_url,DelaySeconds = delaySeconds,MessageAttributes = messageAttributes,MessageBody = messageBody)
    logger.info(response)
    logger.info('sending data to queue')
    logger.info(response['MessageId'])
    
    return response['MessageId']
    #logger.info(response['MessageId'])

def greeting_intent(intent_request):
    return {
        'dialogAction': {
            "type": "ElicitIntent",
            'message': {
                'contentType': 'PlainText', 
                'content': 'Hi there! How can I help?'
            }
        }
    }

def thank_you_intent(intent_request):
    return {
        'dialogAction': {
            "type": "ElicitIntent",
            'message': {
                'contentType': 'PlainText', 
                'content': 'You are welcome!'
            }
        }
    }
                
                
""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request['currentIntent']['name']
    
    if intent_name == 'GreetingIntent':
        return greeting_intent(intent_request)
    elif intent_name == 'DiningSuggestionsIntent':
        return dining_suggestion_intent(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thank_you_intent(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
# def main():
    logger.info(event)
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
