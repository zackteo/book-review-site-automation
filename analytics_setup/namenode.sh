#!/usr/bin/env bash

#Update package list & install dependencies
sudo apt-get update #&& sudo apt-get upgrade -y
sudo apt-get install -y openjdk-8-jdk-headless
sudo apt-get install -y ssh

#Setup hostname
sudo dd of=/etc/hosts << EOF
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
EOF


#Allow hadoop user sudo rights w/o password
sudo sh -c 'echo "hadoop ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/90-hadoop'
#Reduce rate of writing to swap files
sudo sysctl vm.swappiness=10

#Setup SSH key w/o keyboard input
#ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa <<< y

#Allow password based SSH
sudo sed -i "s/^PasswordAuthentication.*/PasswordAuthentication yes/" /etc/ssh/sshd_config
sudo service sshd restart
#Copy generated public key from name node to worker nodes
#ssh-copy-id hadoop-master
#ssh-copy-id hadoop-worker-1
#ssh-copy-id hadoop-worker-2
#ssh-copy-id hadoop-worker-3

#Change user to hadoop
cd ~
sudo adduser --disabled-password --shell /bin/bash --gecos "User" hadoop
sudo su hadoop

#Hadoop Set-up
sudo mkdir download && cd download
sudo wget https://apachemirror.sg.wuchna.com/hadoop/common/hadoop-3.3.0/hadoop-3.3.0.tar.gz

sudo tar zxvf hadoop-3.3.0.tar.gz
# update the JAVA_HOME
export JH="\/usr\/lib\/jvm\/java-8-openjdk-amd64"
sed -i "s/# export JAVA_HOME=.*/export\ JAVA_HOME=${JH}/g" hadoop-3.3.0/etc/hadoop/hadoop-env.sh
MASTER="hadoop-master"
WORKERS="hadoop-worker-1 hadoop-worker-2 hadoop-worker-3"  



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

for ip in ${WORKERS}; do echo -e "${ip}" >> hadoop-3.3.0/etc/hadoop/workers ; done

#Distributing the configured library
sudo tar czvf hadoop-3.3.0.tgz hadoop-3.3.0
for h in $WORKERS ; do
scp hadoop-3.3.0.tgz $h:.;
done;

cp hadoop-3.3.0.tgz ~/
cd

tar zxvf hadoop-3.3.0.tgz
sudo mv hadoop-3.3.0 /opt/

sudo mkdir -p /mnt/hadoop/namenode/hadoop-${USER}
sudo chown -R hadoop:hadoop /mnt/hadoop/namenode
echo "y" | /opt/hadoop-3.3.0/bin/hdfs namenode -format

#Start Hadoop
/opt/hadoop-3.3.0/sbin/start-dfs.sh && /opt/hadoop-3.3.0/sbin/start-yarn.sh


#Spark here
cd download

wget https://apachemirror.sg.wuchna.com/spark/spark-3.0.1/spark-3.0.1-bin-hadoop3.2.tgz

tar zxvf spark-3.0.1-bin-hadoop3.2.tgz

cp spark-3.0.1-bin-hadoop3.2/conf/spark-env.sh.template \
    spark-3.0.1-bin-hadoop3.2/conf/spark-env.sh

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

for i in ${WORKERS};
do scp spark-3.0.1-bin-hadoop3.2.tgz $i:./spark-3.0.1-bin-hadoop3.2.tgz;
done

mv spark-3.0.1-bin-hadoop3.2.tgz ~/

cd ~
tar zxvf spark-3.0.1-bin-hadoop3.2.tgz
sudo mv spark-3.0.1-bin-hadoop3.2 /opt/
sudo chown -R hadoop:hadoop /opt/spark-3.0.1-bin-hadoop3.2

#Start Spark Cluster
/opt/spark-3.0.1-bin-hadoop3.2/sbin/start-all.sh

#Setup Geni (Clojure's spark interface)
wget https://raw.githubusercontent.com/zero-one-group/geni/develop/scripts/geni
chmod a+x geni
sudo mv geni /usr/local/bin/