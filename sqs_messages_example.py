print "getting queue"
logging.info("getting queue")
my_queue = connsqs.get_queue('MYQUEUE')
my_queue.set_message_class(RawMessage) #raw messages from SNS

maxmsgs = 10
msgs = []
msg = my_queue.read()
while msg:
        logging.info("getting message")
        msgsingle = json.loads(msg.get_body())['Message']
        logging.info(msgsingle)
        msgs.append(msgsingle)
 

        logging.info("deleting message")
        my_queue.delete_message(msg)
        if len(msgs) < maxmsg :
                logging.info("getting more messages")
                msg = my_queue.read()
        else:
                msg = False
