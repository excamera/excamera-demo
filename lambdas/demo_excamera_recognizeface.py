import subprocess as sub
import datetime
import socket
import base64
import boto3
import uuid
import time
import gzip
import json
import StringIO
import os

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
S3_FACE_VECTORS_PATH = 'uploaded-faces-vectors/'
S3_FRAME_PATH = 'video/gates_frames/'
FRAME_PREFIX = 'video_'

def lambda_handler(event, context):
    start_idx = event['frame_start_idx']
    stop_idx = event['frame_stop_idx'] # not inclusive
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
        os.system("cd /tmp && curl https://s3-us-west-2.amazonaws.com/demo-excamera-s3/root-495M-2017-02-06.tar.gz | tar xz")
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
        try:
            p = sub.Popen(["/tmp/excamera-demo-master/demo/start_faceknn_server"], stdout=sub.PIPE, stderr=sub.PIPE)
        except:
            raise Exception("couldn't start the faceknn server!")

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
        socket.setdefaulttimeout(300)

        # get the face model
        s3 = boto3.client('s3') 
        try:
            response = s3.get_object(Bucket='demo-excamera-s3', Key=S3_FACE_VECTORS_PATH+face_model_name)
            face_vectors_gz = response['Body'].read()
            base64_face_vectors_gz = base64.b64encode(face_vectors_gz)
        except:
            raise Exception("could not download: " + S3_FACE_VECTORS_PATH+face_model_name)

        # process the frames
        frames_with_face = []
        frames_with_face_indicator = []
        for i in xrange(start_idx, stop_idx):
            t = datetime.datetime.now().strftime(DATETIME_FORMAT)
            dynamodb.update_item(TableName='demo-excamera', 
                Key={ 'uuid4' : { 'S' : index } },  
                ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op', '#F' : 'frames_with_face' },
                ExpressionAttributeValues={ ':s' : { 'S' : 'frame' + str(i) + '_being_processed' }, 
                                            ':t' : { 'S' : t },
                                            ':f' : { 'L' : [ { 'N' : str(frame_num) } for frame_num in frames_with_face ] } 
                },
                UpdateExpression='SET #ST = :s, #T = :t, #F = :f',
            )

            # get frame from s3
            try:
                response = s3.get_object(Bucket='demo-excamera-s3', Key=S3_FRAME_PATH+FRAME_PREFIX+str(i).zfill(8)+'.jpg')
                binary_image = response['Body'].read()
                base64_image = base64.b64encode(binary_image)
            except:
                raise Exception("could not download: " + S3_FRAME_PATH+FRAME_PREFIX+str(i).zfill(8)+'.jpg')
        
            # make connection
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('localhost', SERVER_PORT))

            # send data
            s.sendall('G' + '!' + base64_image + '!' + base64_face_vectors_gz + ':')
            
            # get the result
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
            
            # record the result
            frames_with_face_indicator.append( json.loads(data)['face_present'] )
            
            frames_with_face = filter(lambda x: x[0], zip(frames_with_face_indicator, range(start_idx, stop_idx)))
            frames_with_face = map(lambda x: x[1], frames_with_face)
        
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
            ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op', '#F' : 'frames_with_face' },
            ExpressionAttributeValues={ ':s' : { 'S' : 'face_recognition_completed' }, 
                                        ':t' : { 'S' : t },
                                        ':f' : { 'L' : [ { 'N' : str(frame_num) } for frame_num in frames_with_face ] } 
            },
            UpdateExpression='SET #ST = :s, #T = :t, #F = :f',
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
