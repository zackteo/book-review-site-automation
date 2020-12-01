#!/bin/bash

#get Access ID and
read -p "aws_access_key_id : " aws_access_key_id
read -p "aws_secret_access_key : " aws_secret_access_key
read -p "aws_session_token (AWS Educate) : " aws_session_token
read -p "new key-pair name (not pre-existing) : " aws_key_pair

#cd ~
mkdir .aws
echo "[default]
region = us-east-1" > .aws/config

echo "[default]
aws_access_key_id=$aws_access_key_id
aws_secret_access_key=$aws_secret_access_key
aws_session_token=$aws_session_token" > .aws/credentials

#FOR PROF start with ami-0f82752aa17ff8f5d
sudo apt-get update
sudo apt-get install -y unzip

#install aws-cli
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

#create key
aws ec2 create-key-pair --key-name $aws_key_pair > ~/.ssh/$aws_key_pair.pem

curl https://gist.githubusercontent.com/zackteo/cc5f3d718f4ada748c1d56805cc97a37/raw/625b1711adecb3fadef55966cc4a305fe5177f0e/hdfs-spark-ec2.yaml \
    > single-instance.yml 

#Programmaticatically edit yml?


#REVIEW: t2.micro
aws cloudformation create-stack --template-body file://$(pwd)/cloudformation_templates/production-setup.yml  \
    --stack-name single-instance --parameters ParameterKey=KeyName,ParameterValue=$aws_key_pair ParameterKey=InstanceType,ParameterValue=t2.micro
