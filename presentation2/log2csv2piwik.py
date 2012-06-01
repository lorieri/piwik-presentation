# coding: utf-8
import os
import sys

#check if processes are locked for maintenance
if os.path.isfile("/tmp/lockall") :
    print "locked!"
    sys.exit()

from boto.sqs.connection import SQSConnection
from boto.s3.connection import S3Connection
import json
import base64
from datetime import *

from boto.sqs.message import RawMessage
import tempfile
import signal
import logging
from time import time

from datetime import *
from dateutil.parser import parse
import gzip
import random
import urllib
import re
import csv
#put your website's token below 
piwik_token_auth = "xxxxxxxxxxxxxxx"

# log regexp for ncsa combined log
log_pattern = re.compile("""^(?P<ip>\d+\.\d+\.\d+\.\d+)
                         \s+-\s+-\s+
                         \[(?P<data>\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}\s(?:-|\+)\d{4})\]
                         \s+\"GET.*\"\s+(?:2\d{2}|3\d{2})\s+\d+\s+\"(?P<refererproto>(?:http|https)://)
                         (?P<refererurl>.*)\"
                         \s+\"(?P<useragent>[^"]*?)\" # user agent                         
                         \s+\"uid2=\w+(?P<cookie>\w{16})\"$
                         """,re.VERBOSE)

query_log_pattern = re.compile("(?P<action_name>([^\?|#]+))")

piwik_action_name_remove_dot = re.compile("\./")
piwik_action_name_remove_dot_end = re.compile("\.$")

logfile = 'mylog.log'
logging.basicConfig(filename=logfile,level=logging.INFO)

now = datetime.now()
now = now.strftime("%Y-%m-%d %H:%M:%S")+":"+str(now.microsecond)
logging.info("started at: "+now)


# do you need proxy ?
os.environ['http_proxy']='http://myproxy:8080'

# max SQS files message to be processed
maxmsg = 32

#change below for debug purposes
delmsgs = 1


# AWS configs

mybucket='xxxxxxx'
myqueue='xxxxxxx'

sqs_key='xxxxxxxxxxxxxxxxxx'
sqs_sec='xxxxxxxxxxxxxxxxxx'

s3_key='xxxxxxxxxxxxxxxxxxxxxxxxx'
s3_sec='xxxxxxxxxxxxxxxxxxxxxxxxx'

print "connecting to sqs"
logging.info("connecting to sqs")
connsqs = SQSConnection(sqs_key, sqs_sec)
print "connecting to s3"
logging.info("connection to s3")
conns3 = S3Connection(s3_key, s3_sec)

print "getting queue"
logging.info("getting queue")
my_queue = connsqs.get_queue(myqueue)
my_queue.set_message_class(RawMessage)

llog="getting messages (max of "+str(maxmsg)+")"
print llog
logging.info(llog)

# getting the file list
msgdata = []
msgs = []
if maxmsg > 0 :
    msg = my_queue.read()
    while msg:
        print "getting message"
        logging.info("getting message")
        msgsingle = msg.get_body()

        # accept raw messages from SNS or base64 inputed by hand during maintenances
        if "{" in msgsingle :
            msgsingle = json.loads(msg.get_body())['Message']
        else :
            msgsingle = base64.decodestring(msgsingle)

        logging.info(msgsingle)

        # put file in the list
        msgs.append(msgsingle)
        print msgsingle

        #remove message, get more messages
        print "deleting  message"
        logging.info("deleting message")
        if delmsgs > 0 :
            my_queue.delete_message(msg)
        if len(msgs) < maxmsg :
            print "getting more messages"
            logging.info("getting more messages")
            msg = my_queue.read()
        else:
            msg = False
# send metric to monitoring system
os.system("/usr/bin/zabbix_sender -s `hostname` -z myzabbixserver.com -k worker.mysite.msgs -o "+str(len(msgs))+" > /dev/null")

div = 0 # line count
filename = '/tmp/tmppiwikpy.%s.txt' % os.getpid() #create temp file
csv_file = '/var/csv/mysite/mysite.%s' % os.getpid()
csv_handle = open(csv_file,'wb')
csv_out = csv.writer(csv_handle,dialect='excel',quoting=csv.QUOTE_MINIMAL)
for msg_data in msgs:  # msgs here is a name of a file
    llog = "trying file "+msg_data
    print llog
    logging.info(llog)
    if "s3://"+mybucket+"/" in msg_data : #our case, get files from S3
        s3obj = msg_data.replace("s3://"+mybucket+"/","")
        llog = "downloading "+msg_data
        print llog
        logging.info(llog)
        key = conns3.get_bucket(mybucket).get_key(s3obj)
        key.get_contents_to_filename(filename)
        llog = "decompressing file"+msg_data
        print llog
        logging.info(llog)
        fgz = gzip.open(filename, 'r');
        for line in fgz: #for each file line
            line = line.rstrip('\r\n')
            log_match = log_pattern.match(line)
            if log_match:
                piwik_idsite = X # put your site's ID here
                log = log_match.groupdict()
                data = parse(log['data'],fuzzy=True)
                data_utc = data - data.utcoffset() # data offset from the ncsa log 
                data_utc = data_utc.replace(tzinfo=None)
                piwik_action_name = log['refererurl']
                piwik_useragent = log['useragent'] # get user agent to be replaced in the php-cli script
                piwik_action_name = piwik_action_name_remove_dot.sub("/",piwik_action_name)
                piwik_action_name = piwik_action_name_remove_dot_end.sub("",piwik_action_name)
                piwik_action_name = piwik_action_name.lower()
                query_match = query_log_pattern.match(piwik_action_name)
                if query_match:
                    query = query_match.groupdict()
                    piwik_action_name = query['action_name']
                piwik_cip = log['ip']
                piwik_id = str(log['cookie']).lower()
                piwik_url = urllib.quote_plus(log['refererproto']+piwik_action_name)
                piwik_cdt = urllib.quote_plus(str(data_utc))
                piwik_rand = str(random.randint(1000000,9999999)) # required random number for piwik API

                # write all lines in a  single file, remember that each file contains only 5 minutes of log
                csv_out.writerow( [piwik_idsite, piwik_url, piwik_action_name, piwik_cip, piwik_id, piwik_cdt, piwik_rand, piwik_token_auth, piwik_useragent] )
                div=div+1

        csv_handle.flush()
        llog = "closing and deleting temporary file"
        print llog
        logging.info(llog)
        fgz.close()
        os.remove(filename)

# divide the CSV in 60 pieces
sp=div/60
if sp < 1 :
        sp = 1

csv_handle.close()

now = datetime.now()
now = now.strftime("%Y-%m-%d %H:%M:%S")+":"+str(now.microsecond)

logging.info("running php: "+now)
logging.info("csv_file: "+csv_file)

#split file
os.system("split -l " + str(sp) + " " + csv_file + " " + csv_file + "-split")

# for each splited file, run our php custom script 
os.system("(for i in `ls " + csv_file + "-split*`; do echo \"/usr/bin/php5 -q /var/www/piwik-r7.php -- $i > /dev/null &\";done;echo wait)|bash")  # wait waits all php finish

os.remove(csv_file)

now = datetime.now()
now = now.strftime("%Y-%m-%d %H:%M:%S")+":"+str(now.microsecond)
logging.info("finished at: "+now)

