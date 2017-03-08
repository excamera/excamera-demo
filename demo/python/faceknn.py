from sklearn import neighbors
import numpy as np
import openface
import cv2
import os
import sys
import gzip
import zlib
import timeit
import StringIO
import urllib2

DIRNAME = os.path.dirname(os.path.realpath(__file__))
LFW_ENDPOINT = 'https://s3.amazonaws.com/demo-excamera/lfw_face_vectors.csv.gz'
SHAPE_PREDICTOR_PATH = '/tmp/root/openface-package/models/dlib/shape_predictor_68_face_landmarks.dat'
FACE_NN_PATH = '/tmp/root/openface-package/models/openface/nn4.small2.v1.t7'

def parse_csvgz(filename):
    with gzip.open(filename, 'r') as f:
        data = map(lambda x: x.split(','), f.read().strip().split('\n'))
        np_data = np.asmatrix(data)

        return np_data 

def get_face_vectors(img_path, align, net):
    '''
    get_face_vectors: finds all faces in an image (from left to right) and featurizes them 
    using openface CNN featurizer.
    '''
    
    bgrImg = cv2.imread(img_path)
    if bgrImg is None:
        raise Exception("Unable to load image: {}".format(img_path))

    rgbImg = cv2.cvtColor(bgrImg, cv2.COLOR_BGR2RGB)

    bbs = align.getAllFaceBoundingBoxes(rgbImg)

    if len(bbs) == 0:
        sys.stderr.write("Unable to find a face: {}".format(img_path))
        return []

    reps = []
    for bb in bbs:
        alignedFace = align.align(
            96,
            rgbImg,
            bb,
            landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)
        if alignedFace is None:
            sys.stderr.write("Unable to align image: {}".format(img_path))
            return []

        rep = net.forward(alignedFace)
        reps.append((bb.center().x, rep))

    sreps = sorted(reps, key=lambda x: x[0])
    return sreps

if __name__ == "__main__":
    total_start = timeit.default_timer()
    if len(sys.argv) < 3:
        sys.stderr.write('Usage:\n\t' + sys.argv[0] + 
                         ' FACE.gz IMG_PATH [IMG_PATH ...]\n\n') 
        sys.stderr.write('Description:\n\tReturns "1" if ANY face in the image is from FACE.gz\n\tand "0" otherwise\n\n')
        sys.exit(-1)


    face_model_start = timeit.default_timer()
    face = parse_csvgz(sys.argv[1])
    face_model_end = timeit.default_timer()
    print "time to load target face model,", face_model_end - face_model_start
        
    model_download_start = timeit.default_timer()
    lfw_fio = StringIO.StringIO(urllib2.urlopen(LFW_ENDPOINT).read())
    lfw = np.asmatrix( map(lambda x: x.split(','), gzip.GzipFile(fileobj=lfw_fio).read().strip().split('\n')) )
    model_download_end = timeit.default_timer()
    print "time to load lfw model,", model_download_end - model_download_start
    
    aggregate_training_data_start = timeit.default_timer()
    face_labels = np.zeros( (face.shape[0], 1) )
    class1_labels = np.ones( (lfw.shape[0], 1) )
        
    combined = np.vstack( (face, lfw) )
    combined_labels = np.vstack( (face_labels, class1_labels) )
    aggregate_training_data_end = timeit.default_timer() 
    print "time to aggregate training data,", aggregate_training_data_end - aggregate_training_data_start

    # train knn model
    train_knn_start = timeit.default_timer()
    knn = neighbors.KNeighborsClassifier(algorithm='kd_tree')
    knn.fit(combined, combined_labels[:, 0])
    train_knn_end = timeit.default_timer()
    print "time to train knn,", train_knn_end - train_knn_start
    
    # get face dectection models
    face_aligner_start = timeit.default_timer()
    align = openface.AlignDlib(SHAPE_PREDICTOR_PATH)
    face_aligner_end = timeit.default_timer()
    print "time to load face predictor,", face_aligner_end - face_aligner_start

    face_featurizer_start = timeit.default_timer()
    net = openface.TorchNeuralNet(FACE_NN_PATH, imgDim=96, cuda=False)
    face_featurizer_end = timeit.default_timer()
    print "time to load face featurizer,", face_featurizer_end - face_featurizer_start
    
    # try to detect the person of interest in the images
    for img in sys.argv[2:]:
        face_vector_start = timeit.default_timer()
        face_vectors = map(lambda x: x[1], get_face_vectors(img, align, net))
        face_vector_end = timeit.default_timer()
        print "time to get face vectors,", face_vector_end - face_vector_start

        classify_face_start = timeit.default_timer()
        person_of_interest = False
        for face_vector in face_vectors:
            face_prediction = int(knn.predict(face_vector)[0])
            if( face_prediction == 0 ):
                person_of_interest = True
            
        if person_of_interest:
            sys.stdout.write( "1\n" )
        else:
            sys.stdout.write( "0\n" )
        classify_face_end = timeit.default_timer()
        print "time to classify face,", classify_face_end - classify_face_start

    total_end = timeit.default_timer()
    print "total time,", total_end - total_start
