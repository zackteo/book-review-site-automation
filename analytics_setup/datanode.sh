#!/usr/bin/env bash

#Update package list & install dependencies
sudo apt-get update #&& sudo apt-get upgrade -y
sudo apt-get install -y openjdk-8-jdk-headless #non-GUI version

sudo mv /home/ubuntu/hosts /etc/hosts

echo checkpoint1

#Allow hadoop user sudo rights w/o password
sudo sh -c 'echo "ubuntu ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/90-ubuntu'
sudo sh -c 'echo "ubuntu ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/90-hadoop'
sudo sh -c 'echo "hadoop ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/90-ubuntu'
sudo sh -c 'echo "hadoop ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/90-hadoop'
#Reduce rate of writing to swap files
sudo sysctl vm.swappiness=10

echo checkpoint2

#Allow password based SSH
sudo sed -i "s/^PasswordAuthentication.*/PasswordAuthentication yes/" /etc/ssh/sshd_config
sudo service sshd restart

echo checkpoint3

sudo adduser --disabled-password --shell /bin/bash --gecos "User" hadoop

sudo mkdir /home/hadoop/.ssh 

sudo cp /home/ubuntu/.ssh/authorized_keys /home/hadoop/.ssh/authorized_keys
sudo chown -R hadoop:hadoop /home/hadoop/.ssh/authorized_keys

sudo su hadoop

cd /home/ubuntu

#once got configured install from namenode ...

while [ ! -f /home/ubuntu/hadoop-3.3.0.tgz ]
do
  sleep 30s # or less like 0.2
  echo "Waiting for hadoop"
done

echo checkpoint4

cd /home/ubuntu

tar zxvf hadoop-3.3.0.tgz
sudo mv hadoop-3.3.0 /opt/

sudo mkdir -p /mnt/hadoop/datanode/
sudo chown -R hadoop:hadoop /mnt/hadoop/datanode/

echo checkpoint5

#Spark here
while [ ! -f /home/ubuntu/spark-3.0.1-bin-hadoop3.2.tgz ]
do
  sleep 30s # or less like 0.2
  echo "Waiting for spark"
done

cd /home/ubuntu
tar zxvf spark-3.0.1-bin-hadoop3.2.tgz
sudo mv spark-3.0.1-bin-hadoop3.2 /opt/
sudo chown -R hadoop:hadoop /opt/spark-3.0.1-bin-hadoop3.2

# Clear Storage
rm -rf hadoop-3.3.0.tgz
rm -rf spark-3.0.1-bin-hadoop3.2.tgz 
