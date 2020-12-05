#!/usr/bin/env bash

#Update package list & install dependencies
sudo apt-get update #&& sudo apt-get upgrade -y
sudo apt-get install -y openjdk-8-jdk-headless #non-GUI version

sudo mv /home/ubuntu/hosts /etc/hosts

echo checkpoint1

#Allow hadoop user sudo rights w/o password
sudo sh -c 'echo "hadoop ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/90-hadoop'
#Reduce rate of writing to swap files
sudo sysctl vm.swappiness=10

echo checkpoint2

#Allow password based SSH
sudo sed -i "s/^PasswordAuthentication.*/PasswordAuthentication yes/" /etc/ssh/sshd_config
sudo service sshd restart

echo checkpoint3

#cd ~
#sudo adduser --disabled-password --shell /bin/bash --gecos "User" hadoop
#sudo su hadoop

#once got configured install from namenode ...

while [ ! -f /hadoop-3.3.0.tgz ]
do
  sleep 10 # or less like 0.2
  echo "test"
done
ls -l /hadoop-3.3.0.tgz

echo checkpoint4

tar zxvf hadoop-3.3.0.tgz
sudo mv hadoop-3.3.0 /opt/

sudo mkdir -p /mnt/hadoop/datanode/
sudo chown -R hadoop:hadoop /mnt/hadoop/datanode/

echo checkpoint5

#Spark here
#cd ~
#tar zxvf spark-3.0.1-bin-hadoop3.2.tgz
#sudo mv spark-3.0.1-bin-hadoop3.2 /opt/
#sudo chown -R hadoop:hadoop /opt/spark-3.0.1-bin-hadoop3.2
