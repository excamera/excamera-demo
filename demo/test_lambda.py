import socket
import os
import threading
import sys
import base64
import json

print 'create socket'
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'start connection'
s.connect(('ec2-54-146-181-31.compute-1.amazonaws.com', 10000))
print 'send message'

s.sendall(json.dumps({'request_id' : sys.argv[1] }) + ':')            

s.close()
