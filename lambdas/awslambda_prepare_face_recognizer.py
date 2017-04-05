import base64
import os
import socket
import subprocess as sub

def lambda_handler(event, context):
    try:
        # get the base64 image
        if( 'base64_image' not in event.keys() ):
            raise Exception("'base64_image' must be set in the payload")
            
        base64_image = event['base64_image']
        
        # download the dependencies
        os.system("rm -rf /tmp/*")
        os.system("cd /tmp && curl https://s3.amazonaws.com/serverless-face-recognition/root-495M-2017-02-06.tar.gz | tar xz")
        os.system("cd /tmp && curl -X GET https://s3.amazonaws.com/serverless-face-recognition/deps.zip -o deps.zip && unzip deps.zip")
    
        # run the face augmentation server
        p = sub.Popen(["/tmp/deps/start_faceaugmentation_server"], stdout=sub.PIPE, stderr=sub.PIPE)

        # wait for the server to come up
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socket.setdefaulttimeout(30) # time out 30 seconds
        sock.bind(('localhost', 10001))
        sock.listen(1)
            
        conn, addr = sock.accept() # block until server comes up
        conn.close()
        sock.close()
      
        # send image to face augmentation server and receive augmented face vectors
        socket.setdefaulttimeout(300)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', 10000))
        
        s.sendall('G' + base64_image + ':')
        
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
        
        if( data == '' ):
            raise Exception("could not process face image!")
    
        # close the connection and end face augmentation server process
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', 10000))
        s.sendall('S:')
        s.close()
        
        p.kill()
        out, err = p.communicate()
        
        # compress the face vectors
        return {'facevectors' : data}
    
    except Exception as e:
        return {'error' : str(e)}
    
    return {'error' : 'reached the end of the lambda without returning result...'}
