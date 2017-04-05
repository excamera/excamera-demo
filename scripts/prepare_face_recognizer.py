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

base64_image = base64.b64encode( open(sys.argv[1], 'rb').read() )

conn = boto3.client('lambda')

response = conn.invoke(
    FunctionName=FunctionName,
    InvocationType='RequestResponse',
    LogType='Tail',
    Payload=json.dumps({'base64_image':base64_image})
)

facevectors =  eval(response['Payload'].read())['facevectors']
print facevectors
