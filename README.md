# book-review-site-automation

## Test
Start up an EC2 instance with basic OS image - `ami-0f82752aa17ff8f5d`

```bash
git clone https://github.com/zackteo/book-review-site-automation.git
cd book-review-site-automation
chmod +x start-analytics.sh 
./start-analytics.sh
```

May have to manually ssh, change user to hadoop and run scripts at the end of `namenode.sh` from line 242

Because for user data script doesn't seem to allow user change (only root)
