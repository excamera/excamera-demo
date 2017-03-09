import boto3
import json
import uuid

def lambda_handler(event, context):
    index = str( uuid.uuid4() )
    request_id = str( uuid.uuid4() )
    image_key = 'uploaded-faces/'+request_id+'.b64'
    
    dynamodb = boto3.client('dynamodb')
    dynamodb.put_item(TableName='demo-excamera', Item={
        'uuid4' : { 'S' : index },
        'request_id': { 'S' : request_id } ,
        'entry_type' : { 'S' : 'summary' },
        'stage': { 'S' : 'received_request' }
    })
    
    dynamodb.update_item(TableName='demo-excamera', 
        Key={ 'uuid4' : { 'S' : index }, },  
        ExpressionAttributeNames={ '#ST' : 'stage' },
        ExpressionAttributeValues={ ':s' : { 'S' : 'upload_image' } },
        UpdateExpression='SET #ST = :s',
    )
    
    s3 = boto3.client('s3')
    s3.put_object(Bucket='demo-excamera', Key=image_key, Body=event['image'])

    dynamodb.update_item(TableName='demo-excamera', 
        Key={ 'uuid4' : { 'S' : index }, },  
        ExpressionAttributeNames={ '#ST' : 'stage' },
        ExpressionAttributeValues={ ':s' : { 'S' : 'invoke_face_augmentation' } },
        UpdateExpression='SET #ST = :s',
    )
    
    l = boto3.client('lambda')
    response = l.invoke(
        FunctionName='demo_excamera_uploadface',
        InvocationType='Event',
        LogType='Tail',
        Payload=json.dumps({
            'request_id' : request_id,
            'image_key' : image_key,
            'index' : index
        }),
    )
   
    return { 'request_id' : request_id }
