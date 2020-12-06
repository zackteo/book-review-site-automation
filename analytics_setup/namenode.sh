#!/usr/bin/env bash

#Update package list & install dependencies
sudo apt-get update #&& sudo apt-get upgrade -y
sudo apt-get install -y openjdk-8-jdk-headless
sudo apt-get install -y ssh

sudo mv /home/ubuntu/hosts /etc/hosts

echo checkpoint1

#Allow hadoop user sudo rights w/o password
sudo sh -c 'echo "ubuntu ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/90-ubuntu'
sudo sh -c 'echo "ubuntu ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/90-hadoop'
#Reduce rate of writing to swap files
sudo sysctl vm.swappiness=10

#Setup SSH key w/o keyboard input
#ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa <<< y

#Allow password based SSH
sudo sed -i "s/^PasswordAuthentication.*/PasswordAuthentication yes/" /etc/ssh/sshd_config
sudo service sshd restart
#Copy generated public key from name node to worker nodes
#ssh-copy-id hadoop-node-1
#ssh-copy-id hadoop-node-2
#ssh-copy-id hadoop-node-3
#ssh-copy-id hadoop-node-4

echo checkpoint2

#Change user to hadoop
#cd ~
#sudo adduser --disabled-password --shell /bin/bash --gecos "User" hadoop
su - ubuntu

cd /home/ubuntu

echo checkpoint3

#Hadoop Set-up
#sudo mkdir download && cd download
sudo wget https://apachemirror.sg.wuchna.com/hadoop/common/hadoop-3.3.0/hadoop-3.3.0.tar.gz

sudo tar zxvf hadoop-3.3.0.tar.gz

echo checkpoint4

# update the JAVA_HOME
export JH="\/usr\/lib\/jvm\/java-8-openjdk-amd64"
sed -i "s/# export JAVA_HOME=.*/export\ JAVA_HOME=${JH}/g" hadoop-3.3.0/etc/hadoop/hadoop-env.sh
MASTER="hadoop-node-1"
WORKERS="hadoop-node-2 hadoop-node-3 hadoop-node-4 hadoop-node-5 hadoop-node-6 hadoop-node-7 hadoop-node-8 hadoop-node-9 hadoop-node-10"  

echo -e "<?xml version=\"1.0\"?>
<?xml-stylesheet type=\"text/xsl\" href=\"configuration.xsl\"?>
<\x21-- Put site-specific property overrides in this file. -->
<configuration>
<property>
<name>fs.defaultFS</name>
<value>hdfs://${MASTER}:9000</value>
</property>
</configuration>
" > hadoop-3.3.0/etc/hadoop/core-site.xml

# configure hdfs-site.xml
echo -e "<?xml version=\"1.0\"?>
<?xml-stylesheet type=\"text/xsl\" href=\"configuration.xsl\"?>
<\x21-- Put site-specific property overrides in this file. -->
<configuration>
<property>
<name>dfs.replication</name>
<value>3</value>
</property>
<property>
<name>dfs.namenode.name.dir</name>
<value>file:/mnt/hadoop/namenode</value>
</property>
<property>
<name>dfs.datanode.data.dir</name>
<value>file:/mnt/hadoop/datanode</value>
</property>
</configuration>
" > hadoop-3.3.0/etc/hadoop/hdfs-site.xml

# configure yarn-site.xml
echo -e "<?xml version=\"1.0\"?>
<?xml-stylesheet type=\"text/xsl\" href=\"configuration.xsl\"?>
<\x21-- Put site-specific property overrides in this file. -->
<configuration>
<\x21-- Site specific YARN configuration properties -->
<property>
<name>yarn.nodemanager.aux-services</name>
<value>mapreduce_shuffle</value>
<description>Tell NodeManagers that there will be an auxiliary
service called mapreduce.shuffle
that they need to implement
</description>
</property>
<property>
<name>yarn.nodemanager.aux-services.mapreduce_shuffle.class</name>
<value>org.apache.hadoop.mapred.ShuffleHandler</value>
<description>A class name as a means to implement the service
</description>
</property>
<property>
<name>yarn.resourcemanager.hostname</name>
<value>${MASTER}</value>
</property>
</configuration>
" > hadoop-3.3.0/etc/hadoop/yarn-site.xml

# configure mapred-site.xml
echo -e "<?xml version=\"1.0\"?>
<?xml-stylesheet type=\"text/xsl\" href=\"configuration.xsl\"?>
<\x21-- Put site-specific property overrides in this file. -->
<configuration>
<\x21-- Site specific YARN configuration properties -->
<property>
<name>mapreduce.framework.name</name>
<value>yarn</value>
<description>Use yarn to tell MapReduce that it will run as a YARN application
</description>
</property>
<property>
<name>yarn.app.mapreduce.am.env</name>
<value>HADOOP_MAPRED_HOME=/opt/hadoop-3.3.0/</value>
</property>
<property>
<name>mapreduce.map.env</name>
<value>HADOOP_MAPRED_HOME=/opt/hadoop-3.3.0/</value>
</property>
<property>
<name>mapreduce.reduce.env</name>
<value>HADOOP_MAPRED_HOME=/opt/hadoop-3.3.0/</value>
</property>
</configuration>
" > hadoop-3.3.0/etc/hadoop/mapred-site.xml

rm hadoop-3.3.0/etc/hadoop/workers

echo checkpoint5

for ip in ${WORKERS}; do echo -e "${ip}" >> hadoop-3.3.0/etc/hadoop/workers ; done

for ip in ${WORKERS}; do echo -e "${ip}"  ; done

#Distributing the configured library
tar czvf hadoop-3.3.0.tgz hadoop-3.3.0
echo checkpoint6

WORKERS="hadoop-node-2 hadoop-node-3 hadoop-node-4 hadoop-node-5 hadoop-node-6 hadoop-node-7 hadoop-node-8 hadoop-node-9 hadoop-node-10"  

for h in $WORKERS
do
scp -i /home/ubuntu/.ssh/id_rsa -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@host:/home/ubuntu/hadoop-3.3.0.tgz ${h}:/home/ubuntu/hadoop-3.3.0.tgz 
echo $h
done


echo checkpoint7

cp hadoop-3.3.0.tgz ~/
cd /home/ubuntu

tar zxvf hadoop-3.3.0.tgz
sudo mv hadoop-3.3.0 /opt/

sudo mkdir -p /mnt/hadoop/namenode/hadoop-${USER}
sudo chown -R ubuntu:ubuntu /mnt/hadoop/namenode
echo "y" | /opt/hadoop-3.3.0/bin/hdfs namenode -format

echo checkpoint7.5

#Spark here
#cd download

wget https://apachemirror.sg.wuchna.com/spark/spark-3.0.1/spark-3.0.1-bin-hadoop3.2.tgz

tar zxvf spark-3.0.1-bin-hadoop3.2.tgz

cp spark-3.0.1-bin-hadoop3.2/conf/spark-env.sh.template \
    spark-3.0.1-bin-hadoop3.2/conf/spark-env.sh

echo checkpoint8

echo -e "
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export HADOOP_HOME=/opt/hadoop-3.3.0
export SPARK_HOME=/opt/spark-3.0.1-bin-hadoop3.2
export SPARK_CONF_DIR=\${SPARK_HOME}/conf
export HADOOP_CONF_DIR=\${HADOOP_HOME}/etc/hadoop
export YARN_CONF_DIR=\${HADOOP_HOME}/etc/hadoop
export SPARK_EXECUTOR_CORES=1
export SPARK_EXECUTOR_MEMORY=2G
export SPARK_DRIVER_MEMORY=1G
export PYSPARK_PYTHON=python3
" >> spark-3.0.1-bin-hadoop3.2/conf/spark-env.sh

tar czvf spark-3.0.1-bin-hadoop3.2.tgz spark-3.0.1-bin-hadoop3.2/

WORKERS="hadoop-node-2 hadoop-node-3 hadoop-node-4 hadoop-node-5 hadoop-node-6 hadoop-node-7 hadoop-node-8 hadoop-node-9 hadoop-node-10"  

for i in ${WORKERS}
do
scp -i /home/ubuntu/.ssh/id_rsa -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@host:/home/ubuntu/spark-3.0.1-bin-hadoop3.2.tgz ${i}:/home/ubuntu/spark-3.0.1-bin-hadoop3.2.tgz
echo $i
done

echo checkpoint9

cd /home/ubuntu
tar zxvf spark-3.0.1-bin-hadoop3.2.tgz
sudo mv spark-3.0.1-bin-hadoop3.2 /opt/
sudo chown -R ubuntu:ubuntu /opt/spark-3.0.1-bin-hadoop3.2

echo checkpoint9.5

sleep 3m

#Start Hadoop
/opt/hadoop-3.3.0/sbin/start-dfs.sh && /opt/hadoop-3.3.0/sbin/start-yarn.sh

echo checkpoint9.75

#Start Spark Cluster
/opt/spark-3.0.1-bin-hadoop3.2/sbin/start-all.sh

echo checkpoint10

#Setup Geni (Clojure's spark interface)
wget https://raw.githubusercontent.com/zero-one-group/geni/develop/scripts/geni
chmod a+x geni
sudo mv geni /usr/local/bin/
