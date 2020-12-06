
import boto3
import os
import sys
import time
from fabric import Connection
from botocore.exceptions import ClientError
from analytics_functions import *
# import credentials

sys.path.append('../')

print("Start of production automation - please follow the following instructions to key in necessary aws credentials \n")

# Request for AWS Credentials
aws_access_key_id = input('Please key in your AWS access key ID: ')
aws_secret_access_key = input('Please key in your AWS secret access key: ')
aws_session_token = input('Please key in your session token: ')
region_name = 'us-east-1'

credentials_file = open("../credentials", 'w')
credentials_file.write('aws_access_key_id={}\n'.format(aws_access_key_id))
credentials_file.write('aws_secret_access_key={}\n'.format(aws_secret_access_key))
credentials_file.write('aws_session_token={}\n'.format(aws_session_token))
credentials_file.write('region_name={}\n'.format(region_name))
credentials_file.close()


ec2 = boto3.client(
    'ec2',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    aws_session_token=aws_session_token,
    region_name=region_name
)

list_ec2_instances(ec2)
# -------------------------------------------- Set all the security group config ------------------------------------------------

## Permissions for MongoDB
permissions_mongodb = [{'IpProtocol': 'tcp',
                      'FromPort': 22,
                      'ToPort': 22,
                      'IpRanges': [{
                          'CidrIp': '0.0.0.0/0',
                          'Description': 'SSH'}]
                        },
                       {'IpProtocol': '-1',
                      'IpRanges': [{
                          'CidrIp': '0.0.0.0/0',
                          'Description': 'All'}]},
                       {'IpProtocol': 'tcp',
                      'FromPort': 8000,
                      'ToPort': 8000,
                      'IpRanges': [{
                          'CidrIp': '0.0.0.0/0',
                          'Description': 'MongoDB'}]}]

## Permissions for MySQL
permissions_mysql = [{'IpProtocol': 'tcp',
                      'FromPort': 22,
                      'ToPort': 22,
                      'IpRanges': [{
                          'CidrIp': '0.0.0.0/0',
                          'Description': 'SSH'}]},
                     {'IpProtocol': 'tcp',
                      'FromPort': 80,
                      'ToPort': 80,
                      'IpRanges': [{
                          'CidrIp': '0.0.0.0/0',
                          'Description': 'HTTP'}]},
                     {'IpProtocol': 'tcp',
                      'FromPort': 7000,
                      'ToPort': 7000,
                      'IpRanges': [{
                          'CidrIp': '0.0.0.0/0',
                          'Description': 'MySQL'}]}]

permissions_web = [{'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{
                        'CidrIp': '0.0.0.0/0',
                        'Description': 'SSH'}]},
                   {'IpProtocol': '-1',
                    'IpRanges': [{
                        'CidrIp': '0.0.0.0/0',
                        'Description': 'All'}]},
                   {'IpProtocol': 'tcp',
                    'FromPort': 3000,
                    'ToPort': 3000,
                    'IpRanges': [{
                        'CidrIp': '0.0.0.0/0',
                        'Description': 'HTTP'}]},
                   {'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{
                        'CidrIp': '0.0.0.0/0',
                        'Description': 'HTTP'}]}]

# -------------------------------------------- create the security groups ------------------------------------------------
mongodb_security_group_name = 'MongoDB'
mongodb_des = 'MongoDB'
mongodb_secure = create_security_group(mongodb_security_group_name, mongodb_des, permissions_mongodb, ec2)

mysql_security_group_name = 'MySQL'
mysql_des = 'MySQL'
mysql_secure = create_security_group(mysql_security_group_name, mysql_des, permissions_mysql, ec2)

web_security_group_name = 'FE_Server'
web_des = 'FE_Server'
web_secure = create_security_group(web_security_group_name, web_des, permissions_web, ec2)

# -------------------------------------------- create the key_pair ------------------------------------------------
key_pair = 'kindleAutomationKeyPair'
# test to see if this key name already exists
create_key_pair(key_pair, ec2)

# tier can be made bigger to make the whole process faster, example: 't2.medium'
tier = 't2.medium'
instance_ami = 'ami-00ddb0e5626798373'  # using the basic image with ubuntu18.04LTS

# -------------------------------------------- getting the necessary IPs ------------------------------------------------

mongo_instance = create_instances(instance_ami, 1, tier, key_pair, mongodb_secure, ec2, 'mongo')
mongo_node_id = mongo_instance[0]

mysql_instance = create_instances(instance_ami, 1, tier, key_pair, mysql_secure, ec2, 'mysql')
mysql_node_id = mysql_instance[0]

web_instance = create_instances(instance_ami, 1, tier, key_pair, web_secure, ec2, 'server')
web_node_id = web_instance[0]

time.sleep(3)

instance_dic = list_ec2_instances(ec2)
dns_dic = get_publicdns(ec2)

mongo_ip = instance_dic[mongo_node_id]
print('MongoDB IP: ', mongo_ip)
mongo_dns = dns_dic[mongo_node_id]
print('MongoDB DNS: ', mongo_dns)

mysql_ip = instance_dic[mysql_node_id]
print('MySQL IP: ', mysql_ip)
mysql_dns = dns_dic[mysql_node_id]
print('MySQL DNS: ', mysql_dns)

web_ip = instance_dic[web_node_id]
print('Web IP: ', web_ip)
web_dns = dns_dic[web_node_id]
print('Web DNS: ', web_dns)

all_node_ips = [mongo_ip, mysql_ip, web_ip]
all_node_ids = [mongo_node_id, mysql_node_id, web_node_id]
all_node_security_groups = [mongodb_secure, mysql_secure, web_secure]

print("Waiting for instances  to start up")
time.sleep(60)

# ---------------------------------- update the packages ------------------------------------------- >


for instance_ip in all_node_ips:
    success = False
    while (not success):
        try:
            c = theconnector(instance_ip, key_pair)
            c.sudo('apt-get update')
            success = True

        except:
            # in case fail
            print('Command not successful, retrying')
            time.sleep(10)

# ------------------------------------------- reboot ---------------------------------------------------- >

try:
    ec2.reboot_instances(InstanceIds=all_node_ids, DryRun=True)
except ClientError as e:
    if 'DryRunOperation' not in str(e):
        print("You don't have permission to reboot instances.")
        raise

try:
    response = ec2.reboot_instances(InstanceIds=all_node_ids, DryRun=False)
    print('Success', response)
except ClientError as e:
    print('Error', e)

time.sleep(60)

# ------------------------------------------- DATABASE CONFIGURATIONS ---------------------------------------------------- >

name_of_db_meta_data = 'kindle'
name_of_collection_meta_data = 'metadata'
name_of_db_user_logs = 'kindle'
name_of_collection_user_logs = 'log'
mongo_url = '{}'.format(mongo_ip)  # insert mongo url here

# ------------------------------------- writing to an environment file for teardown ------------------------------
teardown_environment_file = open("teardown_environment_production.txt", "w")
teardown_environment_file.write('ec2_ids={}\n'.format(all_node_ids))
teardown_environment_file.write('security_groups={}\n'.format(all_node_security_groups))
teardown_environment_file.write('key_pair=\'{}\''.format(key_pair))
teardown_environment_file.close()

# ------------------------------------ writing to env file for the frontend server to know the IPs to use --------------------------
environment_file = open("../.env", 'w')
environment_file.write('database_name_meta_data={}\n'.format(name_of_db_meta_data))
environment_file.write('database_name_user_logs={}\n'.format(name_of_collection_meta_data))
environment_file.write('URL_METADATA_MONGODB={}\n'.format(mongo_url))
environment_file.write('URL_MYSQL_REVIEWS={}\n'.format(mysql_ip))
environment_file.close()

# # ------------------------ writing to a js file for the front-end -----------------
# ip_js = open("ip.js", 'w')
# ip_js.write('const ip = {\n')
# ip_js.write('   ip:"{}:5000"\n'.format(web_ip))
# ip_js.write('};\n')
# ip_js.write('\n')
# ip_js.write('export { ip }\n')
# ip_js.close()

# -------------------------------- set up mongodb instance-----------------------
success = False
while (not success):
    try:
        print(00)
        # start a connection to MongoDB
        c = theconnector(mongo_ip, key_pair)
        print(0)
        c.sudo('apt update -y')
        c.sudo('apt upgrade -y')
        print(1)
        c.sudo('apt install unzip')
        print(2)
        c.sudo('apt install -y openjdk-8-jre-headless')
        print(3)
        c.sudo('apt install -y leiningen')
        print('----------------------------------------step 0 done---------------------------------------')
        c.sudo('apt-get install gnupg')
        print('----------------------------------------step 1 done---------------------------------------')
        c.run('wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -')
        print('----------------------------------------step 2 done--------------------------------------')
        c.run('echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list')
        print('---------------------------------------step 3 done--------------------------------------')
        c.sudo('apt-get update')
        print('----------------------------------------step 4 done---------------------------------------')
        c.sudo('apt-get install -y mongodb-org')
        print('----------------------------------------step 5 done---------------------------------------')
        c.sudo('service mongod start')
        print('----------------------------------------step 6 done---------------------------------------')
        c.run('wget https://kindle-production-system.s3.amazonaws.com/meta_Kindle_Store.json')
        print('----------------------------------------step 8 done---------------------------------------')
        c.run('mongoimport --db {} --collection {} --file meta_Kindle_Store.json --legacy'.format(name_of_db_meta_data, name_of_collection_meta_data))
        print('----------------------------------------step 7 done---------------------------------------')
        # c.sudo("sed -i 's/127.0.0.1/0.0.0.0/g' /etc/mongod.conf")
        print('----------------------------------------step 8 done---------------------------------------')
        c.sudo('service mongod restart')
        print('----------------------------------------step 9 done---------------------------------------')
        c.run('git clone https://github.com/daryllman/clojure-rest-mongodb.git')
        c.run('cd clojure-rest-mongodb && screen -dmSL mainlein lein run 8000')
        success = True
        print('---------------------------------------All steps done--------------------------------------')
    except:
        # If any commands fail
        print('Command not successful, retrying')
        time.sleep(10)

# -------------------------------- set up mysql instance -----------------------
# # Prepare the Mqsql instance
success = False

while (not success):
    try:
        c = theconnector(mysql_ip, key_pair)
        # c = theconnector('3.90.190.227', 'try')
        ### Install the mysql
        c.sudo('apt update -y')
        c.sudo('apt upgrade -y')
        c.sudo('apt install unzip')
        c.sudo('apt install -y openjdk-8-jre-headless')
        c.sudo('apt install -y leiningen')
        print('----------------------------------------step 0 done---------------------------------------')
        c.sudo('apt-get -y install mysql-server')
        print('----------------------------------------step 1 done---------------------------------------')
        c.sudo('mysql -e \'update mysql.user set plugin = "mysql_native_password" where user="root"\'')
        print('----------------------------------------step 2 done---------------------------------------')
        c.sudo('mysql -e \'create user "root"@"%" identified by ""\'')
        print('----------------------------------------step 3 done---------------------------------------')
        c.sudo('mysql -e \'grant all privileges on *.* to "root"@"%" with grant option\'')

        # c.sudo('mysql -e \'grant all privileges on reviews.* to \'sqoop\'@\'%\' identified by \'sqoop123\';\'')
        # c.sudo("""'mysql -e 'GRANT ALL PRIVILEGES on reviews.* to 'sqoop'@'%' identified by 'sqoop123';'""")
        #c.sudo('mysql -e \'GRANT ALL PRIVILEGES on reviews.* to "sqoop"@"%" identified by "sqoop123";\'')
        print('----------------------------------------step 4 done---------------------------------------')
        c.sudo('mysql -e "flush privileges"')
        print('----------------------------------------step 5 done---------------------------------------')
        c.sudo('service mysql restart')
        print('----------------------------------------step 6 done---------------------------------------')
        #c.sudo('sed -i "s/.*bind-address.*/bind-address = 0.0.0.0/" /etc/mysql/mysql.conf.d/mysqld.cnf')
        print('----------------------------------------step 8 done---------------------------------------')
        # c.run('mkdir data')
        print('----------------------------------------step 9 done---------------------------------------')
        c.run('wget -c https://kindle-production-system.s3.amazonaws.com/kindle_reviews.csv')
        c.run('git clone https://github.com/daryllman/clojure-mysql-rest.git')
        print('----------------------------------------step 10 done---------------------------------------')
        c.sudo('mysql -e "create database \`kindle-reviews\`"')
        print('----------------------------------------step 11 done---------------------------------------')
        c.run('mv clojure-mysql-rest/dbsetup.sql ./')
        c.sudo('mysql -u root -D kindle-reviews -e "source dbsetup.sql"')
        print('----------------------------------------step 12 done---------------------------------------')
        # c.sudo("sed -i 's/bind-address/#bind-address/g' /etc/mysql/mysql.conf.d/mysqld.cnf")
        # c.sudo("sed -ir 's/127.0.0.1/0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf")
        print('----------------------------------------step 13 done---------------------------------------')
        # c.sudo('service mysql restart')
        print('----------------------------------------step 14 done---------------------------------------')
        c.run('cd clojure-mysql-rest && screen -dmSL mainlein lein run 7000')
        success = True
    except:
        # If any commands fail
        print('Command not successful, retrying')
        time.sleep(10)

# -------------------------------- set up server instance -----------------------
success = False
while (not success):
    try:
        c = theconnector(web_ip, key_pair)

        c.sudo('apt update -y')
        c.sudo('apt upgrade -y')
        c.sudo('apt install unzip')
        c.sudo('apt install -y openjdk-8-jre-headless')
        c.sudo('apt install -y leiningen')
        c.put('../.env')
        print("to be done - pseudo git pull frontend")
        success = True
    except:
        # If any commands fail
        print('Command not successful, retrying')
        time.sleep(10)

# print('-----------------------------------these are the ip address of the instances------------------------------')

print('MongoDB IP:', mongo_ip)
print('MySQL IP:', mysql_ip)
print("------------------------------Front end website below--------------------------")

print('Website is at:')
print(f"{web_ip:3000}")
print('Just copy paste this into the browser')
try:
    c = theconnector(web_ip, key_pair)
    print("Run website")

except ValueError:
    pass

print("------------------------Done-------------------------")








