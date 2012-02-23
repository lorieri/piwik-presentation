from boto.sqs.connection import SQSConnection
from boto.s3.connection import S3Connection
from boto.sqs.message import RawMessage # for SNS messages
import json

print "connecting to sqs"
logging.info("connecting to sqs")
connsqs = SQSConnection('xxxxxxxxxxxx', 'xxxxxxxxxxxxx')

print "connecting to s3"
logging.info("connection to s3")
conns3 = S3Connection('xxxxxxxxxxxxxxxx', 'xxxxxxxxxxxxx')
