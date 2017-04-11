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

FunctionName = json.load( open(DIRNAME+'/../.prepare-face-recognizer.lambda.json', 'r') )['FunctionArn']

################################################################################
# code
################################################################################
def main():
    if( len(sys.argv) != 2  or sys.argv[1] == '--help' ):
        print( 'usage: ' + sys.argv[0] + ' IMAGE.jpg > FACEVECTORS.csv' )
        print( 'description:' )
        print( '\treturns the augmented feature vectors for the face in IMAGE.csv.' )
        print( '\tAssume exactly one face in the image.' )
        print()
        sys.exit(0)

    sys.stderr.write( 'reading input file\n' )
    base64_image = base64.b64encode( open(sys.argv[1], 'rb').read() ).decode('utf-8')

    sys.stderr.write( 'connecting to AWS lambda\n' )
    conn = boto3.client('lambda')
    
    sys.stderr.write( 'waiting for remote lambda worker to finish\n' )
    response = conn.invoke(
    FunctionName=FunctionName,
        InvocationType='RequestResponse',
        LogType='Tail',
        Payload=json.dumps({'base64_image':base64_image})
    )
    
    sys.stderr.write( 'reading result from remote lambda worker\n' )
    res = eval(response['Payload'].read())
    try:
        facevectors =  res['facevectors']
        print( facevectors )

        sys.stderr.write( "\nDone!\n" )
    except:
        sys.stderr.write( str(res) )

if(__name__ == '__main__'):
    main()
