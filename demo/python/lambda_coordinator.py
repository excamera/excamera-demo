import boto3
import socket

FRAME_IDX_MIN = 1
FRAME_IDX_MAX = 360
PORT = 10000

def start_lambda_coordinator_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', PORT))
    sock.listen(1)
    print "server started"

    end = False
    while( not end ):
         conn, addr = sock.accept()
         break

    conn.close()
    sock.close()

if __name__ == "__main__":
    start_lambda_coordinator_server()
