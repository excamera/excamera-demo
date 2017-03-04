import time
import cv2
import openface
import sys
import os 

DIRNAME = os.path.dirname(os.path.realpath(__file__))

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

        #start = time.time()
        rep = net.forward(alignedFace)
        #print("Neural network forward pass took {} seconds.".format(time.time() - start))

        reps.append((bb.center().x, rep))

    sreps = sorted(reps, key=lambda x: x[0])
    return sreps

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print sys.argv[0] + ": IMG_PATH [IMG_PATH ...]"

    else:
        align = openface.AlignDlib(os.path.join(DIRNAME, '/tmp/root/openface-package/models/dlib/shape_predictor_68_face_landmarks.dat'))
        net = openface.TorchNeuralNet(os.path.join(DIRNAME, '/tmp/root/openface-package/models/openface/nn4.small2.v1.t7'), imgDim=96, cuda=False)

        filenames = dict()
        for img in sys.argv[1:]:
            csvname = os.path.basename(img)
            if csvname in filenames.keys():
                raise('duplicate filename')
            else:
                face_weights = get_face_vectors(img, align, net)
                for i in range(len(face_weights)):
                    print ','.join(map(lambda x: str(x), face_weights[i][1]))
