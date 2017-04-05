#!/usr/bin/env python

import base64
import boto3
import json
import sys

################################################################################
# constants
################################################################################
FunctionName = 'arn:aws:lambda:us-west-2:387291866455:function:prepare_face_recognizer'

################################################################################
# code
################################################################################
def main():
    if( len(sys.argv) != 2 ):
        print 'usage: ' + sys.argv[0] + ' IMAGE.jpg > FACEVECTORS.csv'
        print 'description:'
        print '\treturns the augmented feature vectors for the face in IMAGE.csv.'
        print '\tAssume exactly one face in the image'
        print
        sys.exit(0)

    base64_image = base64.b64encode( open(sys.argv[1], 'rb').read() )

    conn = boto3.client('lambda')
    
    response = conn.invoke(
    FunctionName=FunctionName,
        InvocationType='RequestResponse',
        LogType='Tail',
        Payload=json.dumps({'base64_image':base64_image})
    )
    
    res = eval(response['Payload'].read())
    try:
        facevectors =  res['facevectors']
        print facevectors
    except:
        print res['error']

if(__name__ == '__main__'):
    main()
