#!/bin/bash -e

# remove the s3 bucket
echo "removing s3 bucket"
readonly BUCKET=$(python -c "
import json
print( json.load( open('.bucket.s3.json', 'r') )['Location'][1:] )
")
aws s3 rm s3://$BUCKET --recursive
aws s3api delete-bucket --bucket $BUCKET

# remove lambda executor role
echo "removing 'lambda-executor' role"
aws iam detach-role-policy --role-name lambda-executor --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name lambda-executor

# create the lambdas
echo "removing 'prepare-face-recognizer' lambda"
aws lambda delete-function --function-name prepare-face-recognizer

echo "removing 'recognize-face' lambda"
aws lambda delete-function --function-name recognize_face

# finished!
echo "Done!"
