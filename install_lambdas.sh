#!/bin/bash -e

# create bucket
echo "creating bucket"
readonly UUID=$(uuidgen)
aws s3api create-bucket --bucket $UUID > .bucket.s3.json

# copy the dependencies to s3
echo "uploading dependencies to s3"
aws s3 cp --acl public-read blobs/deps.zip s3://$UUID/deps.zip
aws s3 cp --acl public-read blobs/root-495M-2017-02-06.tar.gz s3://$UUID/root-495M-2017-02-06.tar.gz
aws s3 cp --acl public-read blobs/lfw_face_vectors.csv.gz s3://$UUID/lfw_face_vectors.csv.gz

# create lambda executor role
echo "adding 'lambda-executor' role"
aws iam create-role --role-name lambda-executor --assume-role-policy-document file://lambdas/AWSLambdaRole.json > .lambda-executor.role.json

aws iam attach-role-policy --role-name lambda-executor --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

readonly ROLE_ARN=$(python -c "
import json
print json.load( open('.lambda-executor.role.json', 'r') )['Role']['Arn']
")

# create the lambdas
echo "adding 'prepare-face-recognizer' lambda"
sleep 7 # give AWS some time to propagate the role

aws lambda create-function --timeout 300 --memory-size 1536 --function-name prepare-face-recognizer --runtime python2.7 --role $ROLE_ARN --handler awslambda_prepare_face_recognizer.lambda_handler --zip-file fileb://lambdas/awslambda_prepare_face_recognizer.py.zip --environment Variables="{FACE_ROOT=https://s3.amazonaws.com/$UUID/root-495M-2017-02-06.tar.gz,FACE_DEPS=https://s3.amazonaws.com/$UUID/deps.zip,LFS_VECTORS=https://s3.amazonaws.com/$UUID/lfw_face_vectors.csv.gz}" > .prepare-face-recognizer.lambda.json

echo "adding 'recognize-face' lambda"
aws lambda create-function --timeout 300 --memory-size 1536 --function-name recognize_face --runtime python2.7 --role $ROLE_ARN --handler awslambda_recognize_face.lambda_handler --zip-file fileb://lambdas/awslambda_recognize_face.py.zip --environment Variables="{FACE_ROOT=https://s3.amazonaws.com/$UUID/root-495M-2017-02-06.tar.gz,FACE_DEPS=https://s3.amazonaws.com/$UUID/deps.zip,LFS_VECTORS=https://s3.amazonaws.com/$UUID/lfw_face_vectors.csv.gz}" > .recognize_face.lambda.json

# finished!
echo "Done!"
