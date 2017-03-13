import boto3
import json
import uuid
import datetime

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

def lambda_handler(event, context):
    index = str( uuid.uuid4() )
    request_id = str( uuid.uuid4() )
    image_key = 'uploaded-faces/'+request_id+'.b64'
    
    t = datetime.datetime.now().strftime(DATETIME_FORMAT)
    dynamodb = boto3.client('dynamodb')
    dynamodb.put_item(TableName='demo-excamera', Item={
        'uuid4' : { 'S' : index },
        'request_id': { 'S' : request_id },
        'entry_type' : { 'S' : 'summary' },
        'stage' : { 'S' : 'received_request' },
        'error' : { 'S' : 'None' },
        'time_start' : { 'S' : t },
        'time_current_op' : { 'S' : t }, 
    })
    
    try:
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : index }, },  
            ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
            ExpressionAttributeValues={ ':s' : { 'S' : 'upload_image' }, 
                                        ':t' : { 'S' : t } },
            UpdateExpression='SET #ST = :s, #T = :t',
        )
        
        s3 = boto3.client('s3')
        s3.put_object(Bucket='demo-excamera-s3', Key=image_key, Body=event['image'])
    
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : index }, },  
            ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
            ExpressionAttributeValues={ ':s' : { 'S' : 'invoke_face_augmentation' }, 
                                        ':t' : { 'S' : t } },
            UpdateExpression='SET #ST = :s, #T = :t',
        )
        
        l = boto3.client('lambda')
        response = l.invoke(
            FunctionName='arn:aws:lambda:us-west-2:387291866455:function:demo_excamera_uploadface',
            InvocationType='Event',
            LogType='Tail',
            Payload=json.dumps({
                'request_id' : request_id,
                'image_key' : image_key,
                'index' : index
            }),
        )
        
    except Exception as e:
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : index }, },  
            ExpressionAttributeNames={ '#ST' : 'error' },
            ExpressionAttributeValues={ ':s' : { 'S' : str(e) } },
            UpdateExpression='SET #ST = :s',
        )

    return { 'request_id' : request_id }
