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
    start_idx = event['frame_start_idx']
    stop_idx = event['frame_stop_idx']
    face_model_name = event['face_model']
    request_id = event['request_id']
    index = str( uuid.uuid4() )

    t = datetime.datetime.now().strftime(DATETIME_FORMAT)
    dynamodb = boto3.client('dynamodb')
    dynamodb.put_item(TableName='demo-excamera', Item={
        'uuid4' : { 'S' : index },
        'request_id' : { 'S' : request_id },
        'frames': { 'L' : [ {'N' : str(i) } for i in xrange(start_idx, stop_idx) ] },
        'frames_with_face': { 'L' : [] },
        'entry_type' : { 'S' : 'recognition' },
        'stage' : { 'S' : 'received_request' },
        'error' : { 'S' : 'None' },
        'time_start' : { 'S' : t },
        'time_current_op' : { 'S' : t }, 
    })
    
    try:
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : index } },  
            ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
            ExpressionAttributeValues={ ':s' : { 'S' : 'faceknn_download_deps' }, 
                                        ':t' : { 'S' : t } },
            UpdateExpression='SET #ST = :s, #T = :t',
        )
        
        # download the dependencies
        os.system("rm -rf /tmp/*")
        os.system("cd /tmp && curl https://s3.amazonaws.com/demo-excamera/root-495M-2017-02-06.tar.gz | tar xz")
        os.system("cd /tmp && curl -X GET https://codeload.github.com/excamera/excamera-demo/zip/master -o excamera-demo-master.zip && unzip excamera-demo-master.zip")

        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : index } },  
            ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
            ExpressionAttributeValues={ ':s' : { 'S' : 'start_faceknn_server' }, 
                                        ':t' : { 'S' : t } },
            UpdateExpression='SET #ST = :s, #T = :t',
        )
    
        # run the face augmentation server
        p = sub.Popen(["/tmp/excamera-demo-master/demo/start_faceaugmentation_server"], stdout=sub.PIPE, stderr=sub.PIPE)

        # wait for the server to come up
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socket.setdefaulttimeout(30) # time out 30 seconds
        sock.bind(('localhost', 10001))
        sock.listen(1)
            
        conn, addr = sock.accept() # block until server comes up
        conn.close()
        sock.close()
        
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : index } },  
            ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
            ExpressionAttributeValues={ ':s' : { 'S' : 'connect_to_faceknn_server' }, 
                                        ':t' : { 'S' : t } },
            UpdateExpression='SET #ST = :s, #T = :t',
        )
        
        # begin communication
        SERVER_PORT = 10000
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', SERVER_PORT))
        
        # TODO send over data...
        
        # end communication
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : index } },  
            ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
            ExpressionAttributeValues={ ':s' : { 'S' : 'shutdown_faceknn_server' }, 
                                        ':t' : { 'S' : t } },
            UpdateExpression='SET #ST = :s, #T = :t',
        )
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', SERVER_PORT))
        s.sendall('S:')
        s.close()
        
        time.sleep(5)
        p.kill()
        out, err = p.communicate()
        
        # persist results to db
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
            Key={ 'uuid4' : { 'S' : index } },  
            ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
            ExpressionAttributeValues={ ':s' : { 'S' : 'face_recognition_completed' }, 
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
        return str(e)
    
    return 'DONE'
