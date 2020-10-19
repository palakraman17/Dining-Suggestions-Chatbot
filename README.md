# Dining-Suggestions-Chatbot

This is a serverless, micro service-driven web application created completely using AWS cloud services. The main application of this chatbot is to provide restaurant suggestions to its users based on the preferences provided to it through conversations. 

## Demo ##
Please visit [here](http://yelpbot.s3.amazonaws.com/home.html) for the Chatbot Link. 

This bot is designed to provide dining recommendations. The recommendation process can be invoked by sending messages like "Dinner in Manhattan", "Food in Brooklyn", etc.

## Services Used ##

* Amazon S3 - To host the frontend
* Amazon Lex - To create the bot and define the intents
API Gateway -  To setup the API
Amazon SQS - To push the
information collected from the user (location, cuisine, etc.) 
ElasticSearch - To fetch restaurant ids based on user preferences
DynamoDB - Store the restaurant data collected using Yelp API
Amazon SNS - Send restaurant suggestions to user through SMS
Lambda - To send data from the frontend to API and API to Lex, validation, collecting restaurant data, sending suggestions using SNS.


## Architecture Diagram ##
![Architecture Diagram](https://github.com/palakraman17/Dining-Suggestions-Chatbot/blob/master/DiningChatBot_Arch.png)


