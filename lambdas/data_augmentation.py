import tempfile
import boto3
import os
import sys
import logging
import subprocess as sub
import json

def lambda_handler(event, context):
    res = sub.check_output(["rm", "-rf", "/tmp/*"])

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    file_location = event['Records'][0]['s3']['object']['key']
    logger.info('got event {}'.format(file_location))
    #logger.error('THIS IS A TEST THIS IS A TEST')
    
    url_prefix = 'https://s3.amazonaws.com/demo-excamera/'
    url_full = url_prefix + file_location

    os.system("cd /tmp && curl https://s3.amazonaws.com/demo-excamera/root-495M-2017-02-06.tar.gz | tar xz")
    sub.check_output(['curl', '-X', 'GET', url_full, '-o', '/tmp/photo.jpg'])

    # download the script for data augmentation...
    # run the script for data augmentation...
    out = sub.check_output(['ls', '/tmp'])
    return out
