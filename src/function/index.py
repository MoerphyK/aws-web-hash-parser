import boto3
import json
import requests
import logging as logger
from hashlib import sha256

def lambda_handler(event, context):

    # URL of the real estate website to parse
    url = "https://portal.immobilienscout24.de/ergebnisliste/82359812"
    # Define the site name for the partition key
    site_name = 'immobilienscout24'
    default_hash = "9283ec05e6e603a41ae5abd832085436c9958209313a34ab71ba2145372900c4"
    
    # # URL of Google time
    # url = "https://www.google.com/search?q=aktuelle+uhrzeit&sca_esv=fc7c61e83823ecc2&rlz=1C1CHBF_deDE1081DE1081&ei=1GLeZZz0Eu6Bi-gP1euV6A8&oq=aktuelle+uhr&gs_lp=Egxnd3Mtd2l6LXNlcnAiDGFrdHVlbGxlIHVocioCCAAyEBAAGIAEGIoFGEMYsQMYyQMyCBAAGIAEGJIDMggQABiABBiSAzIQEAAYgAQYigUYQxixAxiDATIFEAAYgAQyBRAAGIAEMgUQABiABDIFEAAYgAQyBRAAGIAEMgUQABiABEjoEVAAWMQMcAB4AJABAJgBQqABmAWqAQIxMrgBA8gBAPgBAZgCDKACrQXCAhEQLhiABBixAxiDARjHARjRA8ICCxAAGIAEGLEDGIMBwgIIEAAYgAQYsQPCAiAQLhiABBixAxiDARjHARjRAxiXBRjcBBjeBBjgBNgBAcICChAAGIAEGIoFGEPCAgsQLhiABBixAxiDAcICDhAAGIAEGIoFGLEDGIMBwgIOEC4YgAQYsQMYxwEY0QPCAg0QABiABBiKBRhDGMkDwgILEAAYgAQYigUYkgPCAgoQLhiABBiKBRhDmAMAugYGCAEQARgUkgcCMTI&sclient=gws-wiz-serp"
    # site_name = "google_time"
    
    
    # Send a GET request to the website
    response = requests.get(url)
    new_hash = sha256(response.text.encode('utf-8')).hexdigest()
    print(f"New Hash {new_hash}")


    ## Retrieve old Hash value
    # Initialize a DynamoDB client
    dynamodb = boto3.client('dynamodb')
    # Attempt to get the current item for the site
    try:
        current_item_response = dynamodb.get_item(
            TableName='website_hashs',
            Key={
                'site': {'S': site_name}
            }
        )
        # Extract the current hash value in the table, if it exists
        old_hash = current_item_response.get('Item', {}).get('hash', {}).get('S', '')
        print(f"Old Hash {old_hash}")
    except Exception as e:
        logger.error(f"Failed to retrieve item from DynamoDB: {str(e)}")
        old_hash = ''


    ## Compare the old hash value with the new one
    if str(new_hash) != old_hash:
        print("Differenz found!")
        
        try:
            update_response = dynamodb.put_item(
                TableName='website_hashs',
                Item={
                    'site': {'S': site_name},
                    'hash': {'S': str(new_hash)}
                }
            )
            logger.info("DynamoDB update response: {}".format(update_response))
            
        except Exception as e:
            logger.error(f"Failed to update item in DynamoDB: {str(e)}")
            
        ### Mail Notification ###
        message = ""
        subject = ""
        # Is the new value the default value (no apartments)?
        print(f"Check: New Hash: {new_hash}; Default Hash: {default_hash}")
        if new_hash != default_hash:
            print("New hash is NOT equal to default hash.")
            subject = 'Alert: New Apartment Immoscout'
            message = f'A potential new apartment listing has been detected.\nVisit {url} for more details.'
        else:
            print("New hash is equal to default hash.")
            subject = 'No more Apartments in Immoscout'
            message = f'No more Apartments are offered under the URL.\nVisit {url} to verify yourself.'
        
        # Send a notification
        sns = boto3.client('sns')
        sns.publish(
            TopicArn='arn:aws:sns:eu-central-1:142338048689:website_hash',  # Update with your SNS topic ARN
            Message=message,
            Subject=subject
        )
    


    # Check if the request to the website was successful
    if response.status_code == 200:
        return {
            'statusCode': 200,
            'body': json.dumps('Website checked successfully.')
        }
    else:
        logger.error(f"Failed to retrieve the webpage: Status code {response.status_code}")
        return {
            'statusCode': response.status_code,
            'body': json.dumps('Error in retrieving the webpage.')
        }
