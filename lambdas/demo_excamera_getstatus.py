from boto3.dynamodb.conditions import Key, Attr
import boto3
import json

def lambda_handler(event, context):
    request_id = event['request_id']
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('demo-excamera')
    response = table.query(
        IndexName='request_id',
        KeyConditionExpression=Key('request_id').eq(request_id),
        FilterExpression=Attr('entry_type').eq('summary')
    )
    
    items = response['Items']
    if( len(items) == 0 ):
        return { 'error' : 'request_id does not exist' }
    elif( len(items) == 1 ):
        return items[0]
    else: 
        return { 'error' : 'mutliple copies of entry with queried request_id' }
