# coding: utf-8
import os
import sys
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
#lista de parceiros
import modules.sites as sites

piwik_token_auth = "xxxxxxxxxxxxxxxx"
log_pattern = re.compile("""^(?P<ip>\d+\.\d+\.\d+\.\d+)
                         \s+-\s+-\s+
                         \[(?P<data>\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}\s(?:-|\+)\d{4})\]
                         \s+\"GET\s/(?P<img>.*)\s.*\"\s+(?:2\d{2}|3\d{2})\s+\d+\s+\"(?P<refererproto>(?:http|https)://)
                         (?P<refererurl>.*)\"
                         \s+\"(?P<useragent>[^"]*?)\" # user agent                         
                         \s+\"uid2=\w+(?P<cookie>\w{16})\"$
                         """,re.VERBOSE)

site_log_pattern = re.compile("^(?:www\.){0,1}(?P<sites1>[^\.]+)\.(?P<sites2>[^\.]+).*")

piwik_action_name_remove_dot = re.compile("\./")
piwik_action_name_remove_dot_end = re.compile("\.$")

logfile = 'multisite.log'
logging.basicConfig(filename=logfile,level=logging.INFO)

now = datetime.now()
now = now.strftime("%Y-%m-%d %H:%M:%S")+":"+str(now.microsecond)
logging.info("started: "+now)

os.environ['http_proxy']='http://myproxycom.br:8080'

maxmsg = 10
delmsgs= 1

mybucket='xxxxxxxxxxxxxx'
myqueue='xxxxxxxxxxxxxxxx'
sqs_key='xxxxxxxxxxxxxxxx'
sqs_sec='xxxxxxxxxxxxxxxx'

s3_key='xxxxxxxxxxxxxxxx'
s3_sec='xxxxxxxxxxxxxxxx'

lista = parceiros.list()

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

msgdata = []
msgs = []
msg = my_queue.read()

if maxmsg > 0 :
    while msg:
        print "getting message"
        logging.info("getting message")
        msgsingle = msg.get_body()
        if "{" in msgsingle :
            msgsingle = json.loads(msg.get_body())['Message']
        else :
            msgsingle = base64.decodestring(msgsingle)

        logging.info(msgsingle)
        msgs.append(msgsingle)
        print msgsingle

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

os.system("/usr/bin/zabbix_sender -s `hostname` -z myzabbixserver.com -k worker.parceiros.msgs -o "+str(len(msgs))+" > /dev/null")

div = 0

filename = '/tmp/tmppiwikpy.%s.txt' % os.getpid()
csv_file = '/var/csv/sites/sites.%s' % os.getpid()
csv_handle = open(csv_file,'wb')
csv_out = csv.writer(csv_handle,dialect='excel',quoting=csv.QUOTE_MINIMAL)
for msg_data in msgs:
    llog = "trying file "+msg_data
    print llog
    logging.info(llog)
    if "s3://"+mybucket+"/" in msg_data :
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
        for line in fgz:
            line = line.rstrip('\r\n')
            log_match = log_pattern.match(line)
            if log_match:
                piwik_idsite = 21 # default website for debug
                log = log_match.groupdict()
                data = parse(log['data'],fuzzy=True)
                data_utc = data - data.utcoffset()
                data_utc = data_utc.replace(tzinfo=None)
                piwik_action_name = log['refererurl']
                piwik_useragent = log['useragent']                
                piwik_action_name = piwik_action_name_remove_dot.sub("/",piwik_action_name)
                piwik_action_name = piwik_action_name_remove_dot_end.sub("",piwik_action_name)
                piwik_action_name = piwik_action_name.lower()
                sites_match = sites_log_pattern.match(piwik_action_name)
                if sites_match:
                    site = site_match.groupdict()
                    if site['site1'] in lista:
                        piwik_idsite = lista.get(site['site1'])
                    else:
                        piwik_idsite = lista.get(site['site2'], 21) #default site
                piwik_cip = log['ip']
                piwik_id = str(log['cookie']).lower()
                piwik_url = urllib.quote_plus(log['refererproto']+piwik_action_name)
                piwik_cdt = urllib.quote_plus(str(data_utc))
                piwik_rand = str(random.randint(1000000,9999999))
                csv_out.writerow([piwik_idsite,piwik_url,piwik_action_name,piwik_cip,piwik_id,piwik_cdt,piwik_rand,piwik_token_auth,piwik_useragent])
		div=div+1

        csv_handle.flush()
        llog = "closing and deleting temporary file"
        print llog
        logging.info(llog)
        fgz.close()
        os.remove(filename)

sp=div/100
if sp < 1 :
	sp = 1

csv_handle.close()
now = datetime.now()
now = now.strftime("%Y-%m-%d %H:%M:%S")+":"+str(now.microsecond)
logging.info("running the php scripts: "+now)
logging.info("csv_file: "+csv_file)
os.system("split -l " + str(sp) + " " + csv_file + " " + csv_file + "-split")
os.system("(for i in `ls " + csv_file + "-split*`; do echo \"/usr/bin/php5 -q /var/www/piwik-r7.php -- $i > /dev/null &\";done;echo wait)|bash")
os.remove(csv_file)
now = datetime.now()
now = now.strftime("%Y-%m-%d %H:%M:%S")+":"+str(now.microsecond)
logging.info("End : "+now)
