#!/usr/bin/env python3

import json
import sys
import os

n = int(sys.argv[1])  # var1
ssh_key = sys.argv[2] + ".pem"
file_path = sys.argv[3]

if n < 2:
    print("Error: Number of Instances must be 2 or more")
    exit(1)


with open(file_path) as f:
    data = json.load(f)

outputs = dict()

for i in data["Stacks"][0]["Outputs"]:
    outputs[i["OutputKey"]] = i["OutputValue"]

dns = outputs["Instance1PublicIP"]

# send aws-key to namenode
os.system(
    "scp -i ~/.ssh/"
    + ssh_key
    + " -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    + " ~/.ssh/"
    + ssh_key
    + " ubuntu@"
    + dns
    + ":/home/ubuntu/.ssh/id_rsa"
)

# send scripts to nodes
for ip in outputs.values():
    os.system(
        "scp -i ~/.ssh/"
        + ssh_key
        + " -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        + " ~/book-review-site-automation/analytics_setup/datanode.sh"
        + " ubuntu@"
        + ip
        + ":/home/ubuntu/setup.sh"
    )

os.system(
    "scp -i ~/.ssh/"
    + ssh_key
    + " -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    + " ~/book-review-site-automation/analytics_setup/namenode.sh"
    + " ubuntu@"
    + dns
    + ":/home/ubuntu/setup.sh"
)

# create /etc/hosts for all

host_file = """
# /etc/hosts
172.31.23.4 hadoop-node-1
172.31.23.5 hadoop-node-2
172.31.23.6 hadoop-node-3
172.31.23.7 hadoop-node-4
# The following lines are desirable for IPv6 capable hosts
::1
ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
"""

for ip in outputs.values():
    os.system("sudo echo '# /etc/hosts >> /etc/hosts'")
    for i in range(n):
        os.system(
            "sudo echo 172.31.23."
            + str(i + 4)
            + " hadoop-node-"
            + str(i + 1)
            + " >> /etc/hosts"
        )
    os.system(
        "sudo echo '# The following lines are desirable for IPv6 capable hosts >> /etc/hosts'"
    )
    os.system("sudo echo ::1 >> /etc/hosts")
    os.system("sudo echo ip6-localhost ip6-loopback >> /etc/hosts")
    os.system("sudo echo fe00::0 ip6-localnet >> /etc/hosts")
    os.system("sudo echo ff00::0 ip6-mcastprefix >> /etc/hosts")
    os.system("sudo echo ff02::1 ip6-allnodes >> /etc/hosts")
    os.system("sudo echo ff02::2 ip6-allrouters >> /etc/hosts")

# run scripts
for ip in outputs.keys():
    os.system("ssh ubuntu@" + ip + " -i ~/.ssh/" + ssh_key + "chmod +x setup.sh")
    os.system("ssh ubuntu@" + ip + " -i ~/.ssh/" + ssh_key + "./setup.sh > log.txt &")
