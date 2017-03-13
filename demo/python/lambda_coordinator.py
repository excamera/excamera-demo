import datetime
import boto3
import socket
import json 

FRAME_IDX_MIN = 1
FRAME_IDX_MAX = 14001
FRAMES_PER_LAMBDA = 60
PORT = 10000

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

def start_lambda_coordinator_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', PORT))
    sock.listen(1)
    print "server started"

    l = boto3.client('lambda')

    end = False
    while( not end ):
        conn, addr = sock.accept()

        # get the result
        data = ''
        while True:
            d = conn.recv(4096)
            if(d == ''):
                break
                
            if(d[-1] == ':'):
                data += d[:-1]
                break
                
            data += d
        conn.close()
        
        print data
        message = eval( data )
        request_id = message['request_id']
        index = message['index']
  
        dynamodb = boto3.client('dynamodb')
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
                            Key={ 'uuid4' : { 'S' : index } },  
                             ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
                             ExpressionAttributeValues={ ':s' : { 'S' : 'lambda_coordinator_starting_jobs' }, 
                                                         ':t' : { 'S' : t } },
                             UpdateExpression='SET #ST = :s, #T = :t',
        )

        for i in xrange(FRAME_IDX_MIN, FRAME_IDX_MAX, FRAMES_PER_LAMBDA):
            lower = i
            upper = min(i+FRAMES_PER_LAMBDA, FRAME_IDX_MAX)

            lambda_job_args = {
                "frame_start_idx": lower,
                "frame_stop_idx": upper,
                "face_model": request_id+".csv.gz",
                "request_id": request_id
            }
            
            response = l.invoke(
                FunctionName='arn:aws:lambda:us-west-2:387291866455:function:demo_excamera_recognizeface',
                InvocationType='Event',
                LogType='Tail',
                Payload=json.dumps(lambda_job_args)
            )

        end = True
        t = datetime.datetime.now().strftime(DATETIME_FORMAT)
        dynamodb.update_item(TableName='demo-excamera', 
                             Key={ 'uuid4' : { 'S' : index } },  
                             ExpressionAttributeNames={ '#ST' : 'stage', '#T' : 'time_current_op' },
                             ExpressionAttributeValues={ ':s' : { 'S' : 'lambda_coordinator_jobs_started' }, 
                                                         ':t' : { 'S' : t } },
                             UpdateExpression='SET #ST = :s, #T = :t',
        )

    conn.close()
    sock.close()

if __name__ == "__main__":
    start_lambda_coordinator_server()
