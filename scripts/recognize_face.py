#!/usr/bin/env python

import base64
import boto3
import json
import sys

################################################################################
# constants
################################################################################
FunctionName = 'arn:aws:lambda:us-west-2:387291866455:function:recognize_face'

################################################################################
# code
################################################################################
def main():
    if( len(sys.argv) != 3 ):
        print 'usage: ' + sys.argv[0] + ' FACEVECTORS.csv IMAGE.jpg'
        print 'description:'
        print '\treturns `true` or `false` if the face used to generate'
        print '\tFACEVECTORS.csv is present in IMAGE.csv'
        print
        sys.exit(0)

    query_facevectors = base64.b64encode( open(sys.argv[1], 'rb').read() )
    base64_image = base64.b64encode( open(sys.argv[2], 'rb').read() )

    conn = boto3.client('lambda')

    response = conn.invoke(
        FunctionName=FunctionName,
        InvocationType='RequestResponse',
        LogType='Tail',
        Payload=json.dumps({
            'query_facevectors':query_facevectors,
            'base64_image':base64_image
        })
    )

    res = eval(response['Payload'].read())
    try:
        facevectors =  res['face_present']
        print facevectors
    except:
        print res['error']

if(__name__ == '__main__'):
    main()
