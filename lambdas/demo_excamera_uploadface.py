import subprocess as sub
import datetime
import socket
import base64
import boto3
import uuid
import time
import gzip
import StringIO
import os
        
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
        
def lambda_handler(event, context):
    try:
        dynamodb = boto3.client('dynamodb')
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : event['index'] }, },  
            ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
            ExpressionAttributeValues={ ':s' : { 'S' : 'face_vector_retrieve_iamge' }, 
                                        ':t' : { 'S' : t } },
            UpdateExpression='SET #ST = :s, #T = :t',
        )
        
        # get the base64 image
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket='demo-excamera', Key=event['image_key'])
        base64_image = response['Body'].read()
        
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : event['index'] } },  
            ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
            ExpressionAttributeValues={ ':s' : { 'S' : 'face_vector_download_deps' }, 
                                        ':t' : { 'S' : t } },
            UpdateExpression='SET #ST = :s, #T = :t',
        )
        
        # download the dependencies
        os.system("rm -rf /tmp/*")
        os.system("cd /tmp && curl https://s3.amazonaws.com/demo-excamera/root-495M-2017-02-06.tar.gz | tar xz")
        os.system("cd /tmp && curl -X GET https://codeload.github.com/excamera/excamera-demo/zip/master -o excamera-demo-master.zip && unzip excamera-demo-master.zip")
    
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : event['index'] } },  
            ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
            ExpressionAttributeValues={ ':s' : { 'S' : 'start_face_vector_server' }, 
                                        ':t' : { 'S' : t } },
            UpdateExpression='SET #ST = :s, #T = :t',
        )
    
        # run the face augmentation server
        p = sub.Popen(["/tmp/excamera-demo-master/demo/start_faceaugmentation_server"], stdout=sub.PIPE, stderr=sub.PIPE)
        time.sleep(5)
    
        SERVER_PORT = 10000
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', SERVER_PORT))
        
        s.sendall('G' + base64_image + ':')
        
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : event['index'] }, },  
            ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
            ExpressionAttributeValues={ ':s' : { 'S' : 'wait_for_face_vector_server' }, 
                                        ':t' : { 'S' : t } },
            UpdateExpression='SET #ST = :s, #T = :t',
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
    
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : event['index'] }, },  
            ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
            ExpressionAttributeValues={ ':s' : { 'S' : 'close_connection_face_vector_server' }, 
                                        ':t' : { 'S' : t } },
            UpdateExpression='SET #ST = :s, #T = :t',
        )
        
        # close out the connection and process
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', SERVER_PORT))
        s.sendall('S:')
        s.close()
        
        time.sleep(5)
        p.kill()
        out, err = p.communicate()
        
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : event['index'] }, },  
            ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
            ExpressionAttributeValues={ ':s' : { 'S' : 'store_face_vectors' }, 
                                        ':t' : { 'S' : t } },
            UpdateExpression='SET #ST = :s, #T = :t',
        )
        
        # put the face vector image
        sio = StringIO.StringIO()
        zipped_face_vector = gzip.GzipFile(fileobj=sio, mode='w')
        zipped_face_vector.write(data)
        zipped_face_vector.close()
        
        face_vector_key = 'uploaded-faces-vectors/' + event['request_id'] + '.csv.gz'
        s3 = boto3.client('s3')
        s3.put_object(Bucket='demo-excamera', Key=face_vector_key, Body=sio.getvalue())
    
    
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : event['index'] }, },  
            ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
            ExpressionAttributeValues={ ':s' : { 'S' : 'face_vectors_completed' }, 
                                        ':t' : { 'S' : t } },
            UpdateExpression='SET #ST = :s, #T = :t',
        )
        
    except Exception as e:
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : index }, },  
            ExpressionAttributeNames={ '#ST' : 'error' },
            ExpressionAttributeValues={ ':s' : { 'S' : str(e) } },
            UpdateExpression='SET #ST = :s',
        )
    
    return 'DONE'
