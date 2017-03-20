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
import time

DIRNAME = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(DIRNAME, 'python'))
from faceknn import *

LFW_ENDPOINT = 'https://s3-us-west-2.amazonaws.com/demo-excamera-s3/lfw_face_vectors.csv.gz'
SHAPE_PREDICTOR_PATH = '/tmp/root/openface-package/models/dlib/shape_predictor_68_face_landmarks.dat'
FACE_NN_PATH = '/tmp/root/openface-package/models/openface/nn4.small2.v1.t7'

face_model_path = sys.argv[1]
frame_path = sys.argv[2]

# get face dectection model
align = openface.AlignDlib(SHAPE_PREDICTOR_PATH)

# get face featurizer
net = openface.TorchNeuralNet(FACE_NN_PATH, imgDim=96, cuda=False)

lfw_fio = StringIO.StringIO(urllib2.urlopen(LFW_ENDPOINT).read())
lfw = np.asmatrix( map(lambda x: x.split(','), gzip.GzipFile(fileobj=lfw_fio).read().strip().split('\n')) )

face_vectors = np.asmatrix( map(lambda x: x.split(','), gzip.open(face_model_path, 'rb').read().strip().split('\n')) )

face_labels = np.zeros( (face_vectors.shape[0], 1) )
lfw_labels = np.ones( (lfw.shape[0], 1) )
        
combined = np.vstack( (face_vectors, lfw) )
combined_labels = np.vstack( (face_labels, lfw_labels) )
        
# train knn model to find the face of interest
knn = neighbors.KNeighborsClassifier(algorithm='kd_tree')
knn.fit(combined, combined_labels[:, 0])    

bgrImg = cv2.imread(frame_path)
rgbImg = cv2.cvtColor(bgrImg, cv2.COLOR_BGR2RGB)

result = is_face_present(rgbImg, align, net, knn)
print '----------'
print 'face present?:', result
