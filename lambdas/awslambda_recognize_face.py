import subprocess as sub
import socket
import base64
import gzip
import json
import StringIO
import os

def lambda_handler(event, context):
    try:
        if( 'base64_image' not in event.keys() ):
            raise Exception("'base64_image' must be set in the payload")
        if( 'query_facevectors' not in event.keys() ):
            raise Exception("'query_facevectors' must be set in the payload")
            
        base64_image = event['base64_image']
        query_facevectors = base64.b64decode( event['query_facevectors'] )
        
        # compress the facevectors
        sio = StringIO.StringIO()
        facevectors_gz = gzip.GzipFile(fileobj=sio, mode='w')
        facevectors_gz.write(query_facevectors)
        facevectors_gz.close()
        
        base64_face_vectors_gz = base64.b64encode( sio.getvalue() )
        
        # download the dependencies
        ROOT_URL = os.environ['FACE_ROOT']
        DEPS_URL = os.environ['FACE_DEPS']

        os.system("rm -rf /tmp/*")
        os.system("cd /tmp && curl {} | tar xz".format(ROOT_URL))
        os.system("cd /tmp && curl -X GET {} -o deps.zip && unzip deps.zip".format(DEPS_URL))

        # os.system("rm -rf /tmp/*")
        # os.system("cd /tmp && curl https://s3.amazonaws.com/serverless-face-recognition/root-495M-2017-02-06.tar.gz | tar xz")
        # os.system("cd /tmp && curl -X GET https://s3.amazonaws.com/serverless-face-recognition/deps.zip -o deps.zip && unzip deps.zip")
    
        # start the face augmentation server
        p = sub.Popen(["/tmp/deps/start_faceknn_server"], stdout=sub.PIPE, stderr=sub.PIPE)

        # wait for the server to come up
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socket.setdefaulttimeout(30) # time out 30 seconds
        sock.bind(('localhost', 10001))
        sock.listen(1)
        
        conn, addr = sock.accept() # block until server comes up
        conn.close()
        sock.close()
        
        # process image
        SERVER_PORT = 10000
        socket.setdefaulttimeout(300)

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
        
        # close the connection and end face recognition server process
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', SERVER_PORT))
        s.sendall('S:')
        s.close()
        
        p.kill()
        out, err = p.communicate()
        
        # record the result
        face_present = json.loads(data)['face_present']
        
        return {'face_present':str(face_present)}
        
    except Exception as e:
        return {'error' : str(e)}
    
    return {'error' : 'reached the end of the lambda without returning result...'}
