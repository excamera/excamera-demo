import socket
import os
import threading
import sys
import base64

print 'create socket'
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'start connection'
s.connect(('localhost', 10000))
print 'send message'

#s.sendall('G' + fio  + ':')            

s.close()
