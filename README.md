# Kindle Book Review Site Project

## Test
Start up an EC2 instance with basic OS image - `ami-0f82752aa17ff8f5d`

## Automation
### Requirements
Please download necessary python libraries needed - they are in requirements.txt.   
(We are using a mix of python and bash scripts to automate the system)
```bash
git clone https://github.com/zackteo/book-review-site-automation.git
cd book-review-site-automation
sudo apt-get update && sudo apt-get install -y python-pip
pip install -r requirements.txt
```
### Production System
#### Set up
The whole set up of the system can be automated by running just one command.    
The setup and tear down of production system is primarily located at /production_setup folder
```
python production_setup/production.py
```
After running this file, it will automatically request you to key in the inputs for AWS credentials:  
- aws access key id
- aws secret access key
- aws session token    

You can retrieve these values in your AWS console at main page.    
At the end of the set up, the url of the website will be given in console.      
               
Note:            
The IP addresses of the servers will also be saved in .env file         
The node IDs of the aws instances will be saved in /production_setup/teardown_environment_production.txt, which will be used for teardown later on.

#### Tear Down
Similarly, the teardown only requires running of a python file. 
The required data(node ids of aws instances) are already saved locally so you don't have to key in anything.
```
python production_setup/teardown_production.py
```
_______________________________
### Analytics System
#### Set Up
...

#### Tear Down
...
```bash
git clone https://github.com/zackteo/book-review-site-automation.git
cd book-review-site-automation
chmod +x start-analytics.sh 
./start-analytics.sh
```

May have to manually ssh, change user to hadoop and run scripts at the end of `namenode.sh` from line 242

Because for user data script doesn't seem to allow user change (only root)
