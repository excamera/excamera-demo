import time
import numpy as np
import cv2
import openface
import sys
import os 

DIRNAME = os.path.dirname(os.path.realpath(__file__))

def augment_image(img_path):
    img = cv2.imread(img_path)
    if img is None:
        raise Exception("Unable to load image: {}".format(img_path))

    augmented_images = []
    
    # original image
    augmented_images.append(img)

    # fliped x-axis
    rimg = img.copy()
    cv2.flip(rimg, 1, rimg)
    augmented_images.append(rimg)

    # add gaussian noise
    for _ in range(10):
        gaussian_noise = img.copy()
        cv2.randn(gaussian_noise, 0, 150)
        augmented_images.append(img + gaussian_noise)
        augmented_images.append(rimg + gaussian_noise)

    for _ in range(10):
        uniform_noise = img.copy()
        cv2.randu(uniform_noise, 0, 1)
        augmented_images.append(img + uniform_noise)
        augmented_images.append(rimg + uniform_noise)

    return augmented_images
    
def find_face(rgbImg, align):
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

    return alignedFace

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print sys.argv[0] + ": IMG_PATH"

    else:
        align = openface.AlignDlib(os.path.join(DIRNAME, '/tmp/root/openface-package/models/dlib/shape_predictor_68_face_landmarks.dat'))
        
        augmented_images = augment_image(sys.argv[1])

        for i in xrange(len(augmented_images)):
            face = find_face(augmented_images[i], align)
            cv2.imwrite('img'+str(i)+'.jpg', face)
        
