#!/bin/bash

REGION=eu-north-1
ACCOUNT_ID=572540381020
ROLE_ARN=arn:aws:iam::${ACCOUNT_ID}:role/breachloop-lambda-role

NAME=$1

cd lambdas/$NAME

zip handler.zip handler.py

aws lambda update-function-code \
  --function-name breachloop-$NAME \
  --zip-file fileb://handler.zip \
  --region $REGION

echo "Deployed breachloop-$NAME"

cd ../..