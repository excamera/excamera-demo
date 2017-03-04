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

    # get the openface dependencies
    os.system("cd /tmp && curl https://s3.amazonaws.com/demo-excamera/root-495M-2017-02-06.tar.gz | tar xz")
    
    # get the image
    os.system("mkdir /tmp/images")
    sub.check_output(['curl', '-X', 'GET', url_full, '-o', '/tmp/images/photo.jpg'])

    # perform feature augmentation
    os.system("cd /tmp && curl -X GET https://codeload.github.com/excamera/excamera-demo/zip/master -o excamera-demo-master.zip && unzip excamera-demo-master.zip")
    os.system("cd /tmp/images && /tmp/excamera-demo-master/demo/perform_faceaugmentation /tmp/images/photo.jpg &> /tmp/log.txt")
    os.system("cd /tmp && /tmp/excamera-demo-master/demo/get_facevectors images > /tmp/feature-vectors.csv")
    os.system("cd /tmp && gzip /tmp/feature-vectors.csv")
    
    s3 = boto3.resource('s3')
    data = open('/tmp/feature-vectors.csv.gz', 'rb')
    s3.Bucket('demo-excamera').put_object(Key='uploaded-faces-augmented/' + os.path.basename(file_location) + '.csv.gz', Body=data)
    
    #out = open('/tmp/feature-vectors.csv', 'r').read()
    #out = sub.check_output(['/tmp/excamera-demo-master/demo/perform_faceaugmentation', '/tmp/images/photo.jpg'])
    #out = sub.check_output(['ls', '-lh', '/tmp/images/photo.jpg'])
    
    return "DONE!"
