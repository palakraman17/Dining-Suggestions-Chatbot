import json

from botocore.vendored import requests
from urllib.parse import urljoin
import boto3
from decimal import *
import datetime
from time import sleep
import logging 
logger = logging.getLogger() 
logger.setLevel(logging.INFO)
#from elasticsearch import putRequests

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('yelp-restaurants')

API_KEY= 'ckm-FCRJQYGwT6ZLxDfiWpR5Mdk5JH753A5EiSbjOi1k2DD7N6j8X017WoDfbtiv7RfLdKJvC_cp5ciZO8stb_0ZChNsBs-rXA6Qpa7rDe69dpv120HXuIFPT-icXXYx'


API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
TOKEN_PATH = '/oauth2/token'
GRANT_TYPE = 'client_credentials'

# Defaults for our simple example.
DEFAULT_TERM = 'dinner'
DEFAULT_LOCATION = 'Manhattan'
restaurants = {}


def search(cuisine,offset):
    url_params = {
        'location': DEFAULT_LOCATION,
        'offset' : offset,
        'limit': 50,
        'term': cuisine + " restaurants",
        'sort_by' : 'rating'
    }
    return request(API_HOST, SEARCH_PATH, url_params=url_params)


def request(host, path, url_params=None):
    url_params = url_params or {}
    url = urljoin(host, path)
    headers = {
        'Authorization': 'Bearer tF6dH2ARAq0NXInqL5zd_0pocA2QPbrqNzgwLebeizgiJ07I5kY38HpV25HEpAV-JmxwmG9B1S4VjPYc4yzlzQlUbV40qOvzoTbyQPIoRIVDt7B-1Z4RoJIPhJ-bXXYx',
    }

    response = requests.request('GET', url, headers=headers, params=url_params)
    rjson = response.json()
    #business_list = rjson['businesses']
    return rjson

def addItems(data, cuisine):
    global restaurants
    global logger
    with table.batch_writer() as batch:
        for rec in data:
            try:
                #logger.info(rec)
                if rec["alias"] in restaurants:
                    continue;
                rec["id"] = rec["id"]
                rec["name"] = rec["name"]
                rec["review_count"] = rec["review_count"]
                rec["zip_code"] = rec["location"]["zip_code"]
                rec["rating"] = Decimal(str(rec["rating"]))
                restaurants[rec["alias"]] = 0
                rec['cuisine'] = cuisine
                rec['insertedAtTimestamp'] = str(datetime.datetime.now())
                rec["coordinates"]["latitude"] = Decimal(str(rec["coordinates"]["latitude"]))
                rec["coordinates"]["longitude"] = Decimal(str(rec["coordinates"]["longitude"]))
                rec['address'] = rec['location']['display_address']
                rec.pop("distance", None)
                rec.pop("location", None)
                rec.pop("transactions", None)
                rec.pop("display_phone", None)
                rec.pop("categories", None)
                if rec["phone"] == "":
                    rec.pop("phone", None)
                if rec["image_url"] == "":
                    rec.pop("image_url", None)
    
                logger.info(rec)
                batch.put_item(Item=rec)
                sleep(0.001)
            except Exception as e:
                print(e)
                logger.info(type(rec["zip_code"]))
                #print(rec)


def scrape():
    cuisines = ['italian', 'chinese', 'indian', 'american', 'mexican', 'spanish','greek','latin','Persian']
    for cuisine in cuisines:
        offset = 0
        while offset<1000:
            js = search(cuisine,offset)
            addItems(js["businesses"], cuisine)
            offset+=50
           
def lambda_handler(event, context):
    # TODO implement
    #putRequests()
    scrape()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
'''

def main():
    #putRequests()
    scrape()
    addItems(data, cuisine)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
''' 