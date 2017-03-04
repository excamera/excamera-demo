import tempfile
import os
import sys
#import boto3
import subprocess as sub

#s3_client = boto3.client('s3')

def lambda_handler(event, context):
    #os.environ['PATH'] += os.pathsep + os.path.dirname(__file__)

    res = sub.check_output(["rm", "-rf", "/tmp/*"])

    env_dir = tempfile.mkdtemp()
    os.chdir(env_dir)

    os.system("cd /tmp && curl https://s3.amazonaws.com/jemmons-test/root-495M-clean.tar.gz | tar xz")
    
    os.system("cd /tmp/root && cat env.sh test.sh > main.sh")
    os.system("cd /tmp/root && bash main.sh &> test.log")
    res = sub.check_output(["cat", "/tmp/root/test.log"])
    return res
