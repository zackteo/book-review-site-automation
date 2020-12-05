#!/bin/bash

#get Access ID and
read -p "aws_access_key_id : " aws_access_key_id
read -p "aws_secret_access_key : " aws_secret_access_key
read -p "aws_session_token (AWS Educate) : " aws_session_token
read -p "new key-pair name (not pre-existing) : " aws_key_pair
read -p "number of EC2 instances for spark cluster (min 2) : " no_of_instances

#cd ~
mkdir ~/.aws
echo "[default]
region = us-east-1" > ~/.aws/config

echo "[default]
aws_access_key_id=$aws_access_key_id
aws_secret_access_key=$aws_secret_access_key
aws_session_token=$aws_session_token" > ~/.aws/credentials

#FOR PROF start with ami-0f82752aa17ff8f5d
sudo apt-get update
sudo apt-get install -y unzip

#install aws-cli
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

#create key
aws ec2 create-key-pair --key-name $aws_key_pair > ~/.ssh/$aws_key_pair.json

sudo apt-get -y install jq

jq -r .KeyMaterial ~/.ssh/"$aws_key_pair.json" > ~/.ssh/"$aws_key_pair".pem

chmod 600 ~/.ssh/$aws_key_pair.pem

#install python stuff
sudo apt-get install -y python3
sudo apt-get install -y python3-venv

#Programmaticatically edit yml
cd python_scripts
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
python3 yml_append.py $no_of_instances


#REVIEW: t2.micro
aws cloudformation create-stack --template-body file://$(pwd)/hdfs-spark-ec2-cluster-new.yml   \
    --stack-name analytics-system --parameters ParameterKey=KeyName,ParameterValue=$aws_key_pair ParameterKey=InstanceType,ParameterValue=t2.large

sleep 2m

aws cloudformation describe-stacks --stack-name analytics-system > ~/test.json

python3 ~/book-review-site-automation/python_scripts/parse-json.py $no_of_instances $aws_key_pair ~/test.json
