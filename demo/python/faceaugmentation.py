import numpy as np
import openface
import base64
import socket
import time
import cv2
import sys
import os 
import io

HOST = 'localhost'
PORT = 10000
MAX_BUFFER_SIZE = 2**12

DIRNAME = os.path.dirname(os.path.realpath(__file__))
SHAPE_PREDICTOR_PATH = '/tmp/root/openface-package/models/dlib/shape_predictor_68_face_landmarks.dat'
FACE_NN_PATH = '/tmp/root/openface-package/models/openface/nn4.small2.v1.t7'

def augment_image(rgbImg):
    augmented_images = []
    
    # original image
    augmented_images.append(rgbImg)

    # fliped x-axis
    rimg = rgbImg.copy()
    cv2.flip(rimg, 1, rimg)
    augmented_images.append(rimg)

    # add gaussian noise
    for _ in range(10):
        gaussian_noise = rgbImg.copy()
        cv2.randn(gaussian_noise, 0, 150)
        augmented_images.append(rgbImg + gaussian_noise)
        augmented_images.append(rimg + gaussian_noise)

    for _ in range(10):
        uniform_noise = rgbImg.copy()
        cv2.randu(uniform_noise, 0, 1)
        augmented_images.append(rgbImg + uniform_noise)
        augmented_images.append(rimg + uniform_noise)

    return augmented_images
    
def get_face_vector(rgbImg, align, net):
    bbs = align.getAllFaceBoundingBoxes(rgbImg)

    if len(bbs) == 0:
        raise(Exception("Unable to find a face"))
    elif len(bbs) > 1:
        raise(Exception("Found more than one face"))
        
    alignedFace = align.align(
        96,
        rgbImg,
        bbs[0],
        landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)

    if alignedFace is None:
        raise("Unable to align image")

    rep = net.forward(alignedFace)

    return rep

def face_augmentation_server():
    print 'starting up!'

    align = openface.AlignDlib(SHAPE_PREDICTOR_PATH)
    net = openface.TorchNeuralNet(FACE_NN_PATH)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(1)
    print "server started"

    end = False
    while( not end ):
        conn, addr = sock.accept()
        print 'connection made'

        print 'getting data'
        img_base64 = ''
        while True:
            data = conn.recv(MAX_BUFFER_SIZE)
            if( data[-1] == ':'):
                img_base64 += data[:-1]
                break

            img_base64 += data

        print 'checking end condition'
        poison_symbol = img_base64[0]
        img_base64 = img_base64[1:]
        if( poison_symbol == 'S' ):
            end == True
            conn.close()
            sock.close()
            break
            
        # process image
        print 'decode image'
        bio = io.BytesIO( base64.b64decode(img_base64) )
        compressed_img = np.fromstring( bio.read(), dtype=np.uint8 )
        bgrImg = cv2.imdecode(compressed_img, cv2.IMREAD_COLOR)
        rgbImg = cv2.cvtColor(bgrImg, cv2.COLOR_BGR2RGB)

        print 'augmenting image'
        augmented_images = augment_image(rgbImg)

        print 'getting face vectors'
        face_feature_vectors = []
        for rgbImg in augmented_images:
            try:
                face_feature_vector = get_face_vector(rgbImg, align, net)
                face_feature_vectors.append( face_feature_vector )
            except Exception as e:
                sys.stderr.write( str(e) + '\n' )

        # send back resulting face feature vectors
        print 'sending back face vectors'
        output_csv = ''
        for vector in face_feature_vectors:
            output_csv += ','.join(map(str, vector)) + '\n'
        
        conn.sendall(output_csv + ':')

        # close connection
        print 'closing connection'
        conn.close()

    print 'done'

if __name__ == "__main__":
    face_augmentation_server()
