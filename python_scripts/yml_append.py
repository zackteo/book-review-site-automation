#!/usr/bin/env python3

import shutil
import sys  # python python_script.py var1

# number of instances
n = int(sys.argv[1])  # var1

if n < 2:
    print("Error: Number of Instances must be 2 or more")
    exit(1)


def append(content, xfile):
    with open(xfile, "a") as fo:
        fo.write(content)


shutil.copyfile(
    "../cloudformation_templates/hdfs-spark-ec2-cluster.yml",
    "hdfs-spark-ec2-cluster-new.yml",
)

# append x - 2 instances
stuff = """  EC2Instance<<number+2>>:
    Type: AWS::EC2::Instance
    DependsOn:
      - InstanceSecurityGroup
      - PublicSubnet1
    Properties:
      InstanceType:
        Ref: InstanceType
      KeyName:
        Ref: KeyName
      ImageId:
        Fn::FindInMap:
        - AWSRegionArch2AMI
        - Ref: AWS::Region
        - Fn::FindInMap:
          - AWSInstanceType2Arch
          - Ref: InstanceType
          - Arch
      NetworkInterfaces:
      - PrivateIpAddress: '172.31.23.<<number+5>>'
        SubnetId: !Ref PublicSubnet1
        DeviceIndex: '0'
        GroupSet:
        - !Ref InstanceSecurityGroup
        #AssociatePublicIpAddress: true
      UserData: !Base64
        'Fn::Join':
          - ''
          - - |
              #!/bin/bash -xe
            - |
              #cd /home/ubuntu/
            - |
              #mkdir setup && cd setup
            - |
              #curl https://gist.githubusercontent.com/zackteo/0924304ec7616a92689dc90dcceabb25/raw/5e42aae45ba2c48a0fe6a235132c56734e9a481a/datanode.sh > setup.sh
            - |
              #chmod +x setup.sh
            - |
              #./setup.sh
            - |+
"""

for x in range(1, n + 1 - 2):
    append(
        stuff.replace("<<number+2>>", str(x + 2)).replace("<<number+5>>", str(x + 5)),
        "hdfs-spark-ec2-cluster-new.yml",
    )


# append outputs to be shown CloudFormation Interface
outputs = """Outputs:
#  InstanceId:
#    Description: InstanceId of the newly created EC2 instance
#    Value:
#      Ref: EC2Instance1
#  AZ:
#    Description: Availability Zone of the newly created EC2 instance
#    Value:
#      Fn::GetAtt:
#      - EC2Instance1
#      - AvailabilityZone
"""

append(outputs, "hdfs-spark-ec2-cluster-new.yml")


dns_output = """#  Instance<<number>>PublicDNS:
#    Description: Public DNSName of the newly created EC2 instance
#    Value:
#      Fn::GetAtt:
#      - EC2Instance<<number>>
#      - PublicDnsName
  Instance<<number>>PublicIP:
    Description: Public IP address of the newly created EC2 instance
    Value:
      Fn::GetAtt:
      - EC2Instance<<number>>
      - PublicIp
"""

# output DNS for each instance in the cluster
for x in range(1, n + 1):
    append((dns_output.replace("<<number>>", str(x))), "hdfs-spark-ec2-cluster-new.yml")
