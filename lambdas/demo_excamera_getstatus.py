from boto3.dynamodb.conditions import Key, Attr
import boto3
import json

def lambda_handler(event, context):
    try:
        request_id = event['request_id']
        
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('demo-excamera')
        r = table.query(
            IndexName='request_id',
            KeyConditionExpression=Key('request_id').eq(request_id)
        )
        
        # get the status entry
        response = None
        items = filter(lambda x: x['entry_type'] == 'summary', r['Items'])
        if( len(items) == 0 ):
            return { 'error' : 'request_id does not exist' }
        elif( len(items) == 1 ):
            response = dict.copy(items[0])
        else: 
            return { 'error' : 'mutliple copies of entry with queried request_id' }
            
        # get the frames with face of interest
        items = filter(lambda x: x['entry_type'] == 'recognition', r['Items'])
        non_empty_results = filter(lambda x: x['frames_with_face'], items)
        if( non_empty_results ):
            frames_with_face = reduce(lambda x,y: x + y, map(lambda x: x['frames_with_face'], non_empty_results))
            response['frames_with_face'] = sorted(frames_with_face)
            
    except Exception as e:
        return { 'error' : str(e) }
        
    return response
