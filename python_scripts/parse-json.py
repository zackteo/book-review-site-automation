#!/usr/bin/env python3

import json
import sys
import os
import collections

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

print(outputs)

ordered_outputs = collections.OrderedDict(sorted(outputs.items()))

print(ordered_outputs)

# create hosts file
os.system("echo '# ~/hosts >> ~/hosts'")
for i, ip in enumerate(ordered_outputs.values()):
    os.system("echo " + str(ip) + " hadoop-node-" + str(i + 1) + " >> ~/hosts")
os.system(
    "echo '# The following lines are desirable for IPv6 capable hosts >> ~/hosts'"
)
os.system("echo ::1 >> ~/hosts")
os.system("echo ip6-localhost ip6-loopback >> ~/hosts")
os.system("echo fe00::0 ip6-localnet >> ~/hosts")
os.system("echo ff00::0 ip6-mcastprefix >> ~/hosts")
os.system("echo ff02::1 ip6-allnodes >> ~/hosts")
os.system("echo ff02::2 ip6-allrouters >> ~/hosts")


for ip in outputs.values():
    os.system(
        "scp -i ~/.ssh/"
        + ssh_key
        + " -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        + " ~/hosts"
        + " ubuntu@"
        + ip
        + ":/home/ubuntu/hosts"
    )

for i in range(2, len(ordered_outputs) + 1):
    os.system("echo -e hadoop-node-" + str(i) + " >> ~/workers")

for ip in outputs.values():
    os.system(
        "scp -i ~/.ssh/"
        + ssh_key
        + " -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        + " ~/workers"
        + " ubuntu@"
        + ip
        + ":/home/ubuntu/workers"
    )


# run scripts
for ip in outputs.values():
    os.system(
        "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@"
        + ip
        + " -i ~/.ssh/"
        + ssh_key
        + " chmod +x setup.sh"
    )

# send spark scripts
os.system(
    "scp -i ~/.ssh/"
    + ssh_key
    + " -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    + " ~/book-review-site-automation/spark_scripts/pearson.py"
    + " ubuntu@"
    + dns
    + ":/home/ubuntu/pearson.py"
)

os.system(
    "scp -i ~/.ssh/"
    + ssh_key
    + " -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    + " ~/book-review-site-automation/spark_scripts/tfidf.py"
    + " ubuntu@"
    + dns
    + ":/home/ubuntu/tfidf.py"
)

os.system("echo hdfs://" + str(dns) + ":9000/ > ~/namenode_ip.txt")

os.system(
    "scp -i ~/.ssh/"
    + ssh_key
    + " -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    + " ~/namenode_ip.txt"
    + " ubuntu@"
    + dns
    + ":/home/ubuntu/namenode_ip.txt"
)
