import time
import numpy as np
import cv2
import openface
import sys
import os 

DIRNAME = os.path.dirname(os.path.realpath(__file__))

def augment_image(img_path):
    bgrImg = cv2.imread(img_path)
    if bgrImg is None:
        raise Exception("Unable to load image: {}".format(img_path))
    rgbImg = cv2.cvtColor(bgrImg, cv2.COLOR_BGR2RGB)

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
    '''
    get_face_vectors: finds all faces in an image (from left to right) and featurizes them 
    using openface CNN featurizer.
    '''
    bbs = align.getAllFaceBoundingBoxes(rgbImg)

    if len(bbs) == 0:
        raise(Exception("Unable to find a face: {}".format(img_path)))
    elif len(bbs) > 1:
        raise(Exception("Found more than one face: {}".format(img_path)))
        
    alignedFace = align.align(
        96,
        rgbImg,
        bbs[0],
        landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)

    if alignedFace is None:
        raise("Unable to align image: {}".format(img_path))

    rep = net.forward(alignedFace)

    return rep

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print sys.argv[0] + ": IMG_PATH OUT_CSV"

    else:
        img_path = sys.argv[1]
        out_csv = sys.argv[2]
        
        align = openface.AlignDlib(os.path.join(DIRNAME, '/tmp/root/openface-package/models/dlib/shape_predictor_68_face_landmarks.dat'))
        net = openface.TorchNeuralNet(os.path.join(DIRNAME, '/tmp/root/openface-package/models/openface/nn4.small2.v1.t7'), imgDim=96, cuda=False)
        
        augmented_images = augment_image(img_path)

        face_feature_vectors = []
        for rgbImg in augmented_images:
            try:
                face_feature_vector = get_face_vector(rgbImg, align, net)
                face_feature_vectors.append( face_feature_vector )
            except Exception as e:
                sys.stderr.write( str(e) + '\n' )
                
        with open(out_csv, 'w') as f:
            for vector in face_feature_vectors:
                f.write(','.join(map(str, vector)) + '\n')
