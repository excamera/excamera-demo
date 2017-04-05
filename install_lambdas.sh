#!/bin/bash -e

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

aws lambda create-function --timeout 300 --memory-size 1536 --function-name prepare-face-recognizer --runtime python2.7 --role $ROLE_ARN --handler awslambda_prepare_face_recognizer.lambda_handler --zip-file fileb://lambdas/awslambda_prepare_face_recognizer.py.zip > .prepare-face-recognizer.lambda.json

echo "adding 'recognize-face' lambda"
aws lambda create-function --timeout 300 --memory-size 1536 --function-name recognize_face --runtime python2.7 --role $ROLE_ARN --handler awslambda_recognize_face.lambda_handler --zip-file fileb://lambdas/awslambda_recognize_face.py.zip > .recognize_face.lambda.json

# finished!
echo "Done!"
