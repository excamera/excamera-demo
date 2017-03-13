import socket
import os
import threading
import sys
import base64

# def manage_fifo():
    
#     print 'start'
#     fifo = os.open('00000000.mp4.fifo.webm', os.O_WRONLY)
#     print 'open fifo'
#     with open('00000000.mp4.webm', 'rb') as f:
#         print 'write fifo'
#         os.write(fifo, f.read())

#     print 'close fifo'

# os.mkfifo('/home/ec2-user/excamera-demo/demo/00000000.mp4.fifo.webm', 0777)
# t = threading.Thread(target=manage_fifo)
# t.start()

# fifo = os.open('00000000.mp4.fifo.webm', os.O_RDONLY)
# while True:
#     #print 'read',
#     os.read(fifo, 1)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('localhost', 10001))
sock.listen(1)
conn, addr = sock.accept()

conn.close()
sock.close()

vectors = None
with open(sys.argv[1], 'rb') as f:
    vectors = base64.b64encode( f.read() )

for path in sys.argv[2:]:
    print 'create socket'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print 'start connection'
    s.connect(('localhost', 10000))
    print 'send message'

    img = None
    with open(path, 'rb') as f:
        img = base64.b64encode( f.read() )

    s.sendall('G' + '!' + img  + '!' + vectors + ':')

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
            
    print data
    if( data == '' ):
        raise Exception("could not process image")

print 'create socket'
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'start connection'
s.connect(('localhost', 10000))
print 'send message'
s.sendall('S!!:')

# t.join()
s.close()
