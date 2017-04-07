#!/usr/bin/env python

import base64
import boto3
import json
import sys
import os

################################################################################
# constants
################################################################################
DIRNAME = os.path.dirname(os.path.abspath(__file__))

FunctionName = json.load( open(DIRNAME+'/../.recognize_face.lambda.json', 'r') )['FunctionArn']

################################################################################
# code
################################################################################
def main():
    if( len(sys.argv) != 3 or sys.argv[1] == '--help' ):
        print 'usage: ' + sys.argv[0] + ' FACEVECTORS.csv IMAGE.jpg'
        print 'description:'
        print '\treturns `true` or `false` if the face used to generate'
        print '\tFACEVECTORS.csv is present in IMAGE.csv'
        print
        sys.exit(0)

    sys.stderr( 'reading input files' )
    query_facevectors = base64.b64encode( open(sys.argv[1], 'rb').read() )
    base64_image = base64.b64encode( open(sys.argv[2], 'rb').read() )

    sys.stderr( 'connecting to AWS lambda' )
    conn = boto3.client('lambda')

    sys.stderr( 'waiting for remote lambda worker to finish' )
    response = conn.invoke(
        FunctionName=FunctionName,
        InvocationType='RequestResponse',
        LogType='Tail',
        Payload=json.dumps({
            'query_facevectors':query_facevectors,
            'base64_image':base64_image
        })
    )

    sys.stderr( 'reading result from remote lambda worker' )
    res = eval(response['Payload'].read())
    try:
        face_present =  res['face_present']
        print face_present
    except:
        sys.stderr.write( str(res) ) 

if(__name__ == '__main__'):
    main()
