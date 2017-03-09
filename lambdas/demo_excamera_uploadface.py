import subprocess as sub
import socket
import base64
import boto3
import uuid
import time
import gzip
import StringIO
import os
        
def lambda_handler(event, context):
    
    dynamodb = boto3.client('dynamodb')
    dynamodb.update_item(TableName='demo-excamera', 
        Key={ 'uuid4' : { 'S' : event['index'] }, },  
        ExpressionAttributeNames={ '#ST' : 'stage' },
        ExpressionAttributeValues={ ':s' : { 'S' : 'face_vector_retrieve_iamge' } },
        UpdateExpression='SET #ST = :s',
    )
    
    # get the base64 image
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket='demo-excamera', Key=event['image_key'])
    base64_image = response['Body'].read()
    
    dynamodb.update_item(TableName='demo-excamera', 
        Key={ 'uuid4' : { 'S' : event['index'] }, },  
        ExpressionAttributeNames={ '#ST' : 'stage' },
        ExpressionAttributeValues={ ':s' : { 'S' : 'face_vector_download_deps' } },
        UpdateExpression='SET #ST = :s',
    )
    
    # download the dependencies
    os.system("rm -rf /tmp/*")
    os.system("cd /tmp && curl https://s3.amazonaws.com/demo-excamera/root-495M-2017-02-06.tar.gz | tar xz")
    os.system("cd /tmp && curl -X GET https://codeload.github.com/excamera/excamera-demo/zip/master -o excamera-demo-master.zip && unzip excamera-demo-master.zip")

    dynamodb.update_item(TableName='demo-excamera', 
        Key={ 'uuid4' : { 'S' : event['index'] }, },  
        ExpressionAttributeNames={ '#ST' : 'stage' },
        ExpressionAttributeValues={ ':s' : { 'S' : 'start_face_vector_server' } },
        UpdateExpression='SET #ST = :s',
    )

    # run the face augmentation server
    p = sub.Popen(["/tmp/excamera-demo-master/demo/start_faceaugmentation_server"], stdout=sub.PIPE, stderr=sub.PIPE)
    time.sleep(5)

    SERVER_PORT = 10000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', SERVER_PORT))
    
    s.sendall('G' + base64_image + ':')
    
    dynamodb.update_item(TableName='demo-excamera', 
        Key={ 'uuid4' : { 'S' : event['index'] }, },  
        ExpressionAttributeNames={ '#ST' : 'stage' },
        ExpressionAttributeValues={ ':s' : { 'S' : 'wait_for_face_vector_server' } },
        UpdateExpression='SET #ST = :s',
    )
    
    data = ''
    while True:
        d = s.recv(4096)
        if(d == ''):
            break
        
        if(d[-1] == ':'):
            data += d[:-1]
            break
        
        data += d
    s.close()

    dynamodb.update_item(TableName='demo-excamera', 
        Key={ 'uuid4' : { 'S' : event['index'] }, },  
        ExpressionAttributeNames={ '#ST' : 'stage' },
        ExpressionAttributeValues={ ':s' : { 'S' : 'close_connection_face_vector_server' } },
        UpdateExpression='SET #ST = :s',
    )
    
    # close out the connection and process
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', SERVER_PORT))
    s.sendall('S:')
    s.close()
    
    time.sleep(5)
    p.kill()
    out, err = p.communicate()
    
    dynamodb.update_item(TableName='demo-excamera', 
        Key={ 'uuid4' : { 'S' : event['index'] }, },  
        ExpressionAttributeNames={ '#ST' : 'stage' },
        ExpressionAttributeValues={ ':s' : { 'S' : 'store_face_vectors' } },
        UpdateExpression='SET #ST = :s',
    )
    
    # put the face vector image
    sio = StringIO.StringIO()
    zipped_face_vector = gzip.GzipFile(fileobj=sio, mode='w')
    zipped_face_vector.write(data)
    zipped_face_vector.close()
    
    face_vector_key = 'uploaded-faces-vectors/' + event['request_id'] + '.csv.gz'
    s3 = boto3.client('s3')
    s3.put_object(Bucket='demo-excamera', Key=face_vector_key, Body=sio.getvalue())

    dynamodb.update_item(TableName='demo-excamera', 
        Key={ 'uuid4' : { 'S' : event['index'] }, },  
        ExpressionAttributeNames={ '#ST' : 'stage' },
        ExpressionAttributeValues={ ':s' : { 'S' : 'face_vectors_completed' } },
        UpdateExpression='SET #ST = :s',
    )

    return out