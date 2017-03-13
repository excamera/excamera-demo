from sklearn import neighbors
import numpy as np
import openface
import cv2
import os
import io
import sys
import gzip
import zlib
import json
import base64
import timeit
import socket
import StringIO
import urllib2

HOST = 'localhost'
PORT = 10000
MAX_BUFFER_SIZE = 2**12

DIRNAME = os.path.dirname(os.path.realpath(__file__))
LFW_ENDPOINT = 'https://s3.amazonaws.com/demo-excamera/lfw_face_vectors.csv.gz'
SHAPE_PREDICTOR_PATH = '/tmp/root/openface-package/models/dlib/shape_predictor_68_face_landmarks.dat'
FACE_NN_PATH = '/tmp/root/openface-package/models/openface/nn4.small2.v1.t7'

def is_face_present(rgbImg, align, net, knn):

    # get face vectors
    bbs = align.getAllFaceBoundingBoxes(rgbImg)
    face_vectors = []
    for bb in bbs:
        alignedFace = align.align(
            96,
            rgbImg,
            bb,
            landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)

        if alignedFace is None:
            raise("Unable to align image")

        rep = net.forward(alignedFace)
        face_vectors.append(rep)

    # classify the faces in the image
    for face_vector in face_vectors:
        face_prediction = int(knn.predict(face_vector)[0])
        if( face_prediction == 0 ):
            return True

    return False

def face_knn_server():

    # labeled faces in the wild (lfw) vectors
    lfw_fio = StringIO.StringIO(urllib2.urlopen(LFW_ENDPOINT).read())
    lfw = np.asmatrix( map(lambda x: x.split(','), gzip.GzipFile(fileobj=lfw_fio).read().strip().split('\n')) )
    
    # get face dectection model
    align = openface.AlignDlib(SHAPE_PREDICTOR_PATH)
    face_aligner_end = timeit.default_timer()

    # get face featurizer
    net = openface.TorchNeuralNet(FACE_NN_PATH, imgDim=96, cuda=False)

    # start the server 
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(1)
    print "server started"

    # signal to the lambda that the server is ready
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    count = 0
    not_connected = True
    while( not_connected ):
        try:
            s.connect(('localhost', 10001))
            not_connected = False
        except:
            print 'waiting for host to come up', count
            if( count >= 30 ):
                print 'waited too long'
                sys.exit(-1)

            time.sleep(1)
            count += 1

    s.close()

    end = False
    while( not end ):
        conn, addr = sock.accept()
        print 'connection made'

        print 'getting data'
        data = ''
        while True:
            d = conn.recv(MAX_BUFFER_SIZE)
            if( d[-1] == ':'):
                data += d[:-1]
                break

            data += d
        
        poison_symbol, video_path, target_face_vectors_gz = data.split('!')
        print poison_symbol, frame_path, target_face_vectors_gz

        print 'checking end condition'
        if( poison_symbol == 'S' ):
            end == True
            conn.close()
            sock.close()
            break
            
        # process image
        '''
        print 'get face vectors as np amtrix'
        target_face_vectors = io.BytesIO( base64.b64decode(target_face_vectors_gz) )

        # train model for the face of interest
        face = np.asmatrix( map(lambda x: x.split(','), gzip.GzipFile(fileobj=target_face_vectors).read().strip().split('\n')) )

        face_labels = np.zeros( (face.shape[0], 1) )
        lfw_labels = np.ones( (lfw.shape[0], 1) )
        
        combined = np.vstack( (face, lfw) )
        combined_labels = np.vstack( (face_labels, class1_labels) )
        
        # train knn model to find the face of interest
        knn = neighbors.KNeighborsClassifier(algorithm='kd_tree')
        knn.fit(combined, combined_labels[:, 0])    
        '''

        # go through frames and look for face
        face_present = False
        face_frames = []
        for i in xrange(1):
            # video decode here
            print 'open file'
            fd = os.open(video_path, os.O_RDONLY)
            print 'video capture'
            cap = cv2.VideoCapture(video_path)
            print 'read video'
            i = 0
            while(True):
                print i
                i += 1
                ret, frame = cap.read()
                print 'ret:', ret
                if( not ret ):
                    break

            continue
            if ( is_face_present(rgbImg, align, net, knn) ):
                face_present = True
                face_frames.append(i)
        
        # send back resulting face feature vectors
        print 'sending back result'
        result = dict()
        result['face_present'] = int(face_present)
        result['face_frames'] = face_frames
        
        conn.sendall(json.dumps(result) + ':')

        # close connection
        print 'closing connection'
        conn.close()

    print 'done'

if __name__ == "__main__":
    face_knn_server()
