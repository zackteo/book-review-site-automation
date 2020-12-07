import boto3
import sys, os
from dotenv import load_dotenv
import teardown_environment_production
sys.path.append('../')
import credentials
import ast
import time

# AWS credentials needed for teardown
# Taken from archive - saved from setup
session = boto3.session.Session(
    aws_access_key_id=credentials.aws_access_key_id,
    aws_secret_access_key=credentials.aws_secret_access_key,
    aws_session_token=credentials.aws_session_token,
    region_name=credentials.region_name
    )


ec2_resource = session.resource('ec2')
ids = teardown_environment_production.ec2_ids
security_grps = teardown_environment_production.security_groups
key_pair = teardown_environment_production.key_pair

ec2 = boto3.client(
    'ec2',
    aws_access_key_id=credentials.aws_access_key_id,
    aws_secret_access_key=credentials.aws_secret_access_key,
    aws_session_token=credentials.aws_session_token,
    region_name=credentials.region_name
    )
    
waiter = ec2.get_waiter('instance_terminated')


# Terminate EC2 instances
ec2.terminate_instances(InstanceIds = ids)
print("AWS EC2 instances are terminating, please wait...")
waiter.wait(InstanceIds=ids)
print("---->AWS EC2 instances terminated")

time.sleep(60)

# Delete Key Pair
delete_key =  ec2.delete_key_pair(KeyName=key_pair)
print("---->AWS Key Pairs used are deleted")

time.sleep(60)

ec2 = boto3.client(
    'ec2',
    aws_access_key_id=credentials.aws_access_key_id,
    aws_secret_access_key=credentials.aws_secret_access_key,
    aws_session_token=credentials.aws_session_token,
    region_name=credentials.region_name
    )

# Delete AWS Security Groups used
print("Deleting AWS security groups...")
for sgid in security_grps:
    delete_sg = ec2.delete_security_group(GroupId=sgid)
    print("Deleted", sgid)
print("---->AWS Security Groups are deleted")


print('--------------------------------Done with tearing down the Production System fully----------------------------------')