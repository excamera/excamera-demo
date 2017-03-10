from sklearn import neighbors
import numpy as np
import openface
import cv2
import os
import sys
import gzip
import zlib
import json
import timeit
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
        
        poison_symbol, video_gz, target_face_vectors_gz = data.split('!')

        print 'checking end condition'
        if( poison_symbol == 'S' ):
            end == True
            conn.close()
            sock.close()
            break
            
        # process image
        print 'decode image'
        video = io.BytesIO( base64.b64decode(video_gz) )
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
        
        # go through frames and look for face
        face_present = False
        face_frames = []
        for i in xrange(len()):
            # video decode here

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
    return
    
    # total_start = timeit.default_timer()
    # if len(sys.argv) < 3:
    #     sys.stderr.write('Usage:\n\t' + sys.argv[0] + 
    #                      ' FACE.gz IMG_PATH [IMG_PATH ...]\n\n') 
    #     sys.stderr.write('Description:\n\tReturns "1" if ANY face in the image is from FACE.gz\n\tand "0" otherwise\n\n')
    #     sys.exit(-1)

    # face_model_start = timeit.default_timer()
    # face = parse_csvgz(sys.argv[1])
    # face_model_end = timeit.default_timer()
    # print "time to load target face model,", face_model_end - face_model_start
        
    # model_download_start = timeit.default_timer()
    # lfw_fio = StringIO.StringIO(urllib2.urlopen(LFW_ENDPOINT).read())
    # lfw = np.asmatrix( map(lambda x: x.split(','), gzip.GzipFile(fileobj=lfw_fio).read().strip().split('\n')) )
    # model_download_end = timeit.default_timer()
    # print "time to load lfw model,", model_download_end - model_download_start
    
    # aggregate_training_data_start = timeit.default_timer()
    # face_labels = np.zeros( (face.shape[0], 1) )
    # class1_labels = np.ones( (lfw.shape[0], 1) )
        
    # combined = np.vstack( (face, lfw) )
    # combined_labels = np.vstack( (face_labels, class1_labels) )
    # aggregate_training_data_end = timeit.default_timer() 
    # print "time to aggregate training data,", aggregate_training_data_end - aggregate_training_data_start

    # # train knn model
    # train_knn_start = timeit.default_timer()
    # knn = neighbors.KNeighborsClassifier(algorithm='kd_tree')
    # knn.fit(combined, combined_labels[:, 0])
    # train_knn_end = timeit.default_timer()
    # print "time to train knn,", train_knn_end - train_knn_start
    
    # # get face dectection models
    # face_aligner_start = timeit.default_timer()
    # align = openface.AlignDlib(SHAPE_PREDICTOR_PATH)
    # face_aligner_end = timeit.default_timer()
    # print "time to load face predictor,", face_aligner_end - face_aligner_start

    # face_featurizer_start = timeit.default_timer()
    # net = openface.TorchNeuralNet(FACE_NN_PATH, imgDim=96, cuda=False)
    # face_featurizer_end = timeit.default_timer()
    # print "time to load face featurizer,", face_featurizer_end - face_featurizer_start
    
    # # try to detect the person of interest in the images
    # for img in sys.argv[2:]:
    #     face_vector_start = timeit.default_timer()
    #     face_vectors = map(lambda x: x[1], get_face_vectors(img, align, net))
    #     face_vector_end = timeit.default_timer()
    #     print "time to get face vectors,", face_vector_end - face_vector_start

    #     classify_face_start = timeit.default_timer()
    #     person_of_interest = False
    #     for face_vector in face_vectors:
    #         face_prediction = int(knn.predict(face_vector)[0])
    #         if( face_prediction == 0 ):
    #             person_of_interest = True
            
    #     if person_of_interest:
    #         sys.stdout.write( "1\n" )
    #     else:
    #         sys.stdout.write( "0\n" )
    #     classify_face_end = timeit.default_timer()
    #     print "time to classify face,", classify_face_end - classify_face_start

    # total_end = timeit.default_timer()
    # print "total time,", total_end - total_start
