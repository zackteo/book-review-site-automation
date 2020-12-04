#!/usr/bin/env python3

import json
import sys
import os

n = int(sys.argv[1])  # var1
ssh_key = sys.argv[2]

if n < 2:
    print("Error: Number of Instances must be 2 or more")
    exit(1)


with open("test.json") as f:
    data = json.load(f)

outputs = dict()

for i in data["Stacks"][0]["Outputs"]:
    outputs[i["OutputKey"]] = i["OutputValue"]

dns = outputs["Instance1PublicIP"]

# send aws-key to namenode
os.system(
    "scp -i ~/.ssh/"
    + ssh_key
    + "~/.ssh/"
    + ssh_key
    + "ubuntu@"
    + dns
    + ":requirements.txt/.ssh/id_rsa"
)

# create /etc/hosts for all


host_file = """
# /etc/hosts
172.31.23.4 hadoop-master
172.31.23.5 hadoop-worker-1
172.31.23.6 hadoop-worker-2
172.31.23.7 hadoop-worker-3
# The following lines are desirable for IPv6 capable hosts
::1
ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
"""
