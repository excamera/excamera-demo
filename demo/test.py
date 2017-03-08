import socket
import base64
import cv2

# img = cv2.imread('/home/ec2-user/excamera-demo/john_emmons_headshot.jpg')
# img_base64 = base64.b64encode(img)
# print len(img_base64)

img_base64 = base64.b64encode(open('/home/ec2-user/excamera-demo/john_emmons_headshot.jpg', 'rb').read())
print len(img_base64)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 10000))
s.sendall('G' + img_base64 + ':')

data = ''
while True:
    data += s.recv(1024)

    if(data[-1] == ':'):
        break

s.close()

with open('out.csv', 'w') as f:
    f.write(data[:-1])

print 'Received', repr(data)
