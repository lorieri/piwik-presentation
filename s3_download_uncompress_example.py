msg_data[]
lines = []
filename = '/tmp/tmppiwikpy.%s.txt' % os.getpid()
for msg_data in msgs:
        llog = "trying file "+msg_data
        logging.info(llog)
        if "s3://MYBUCKET/" in msg_data :
                s3obj = msg_data.replace("s3://MYBUCKET/","")
                llog = "downloading "+msg_data
                logging.info(llog)
                key = conns3.get_bucket('MYBUCKET').get_key(s3obj)
                key.get_contents_to_filename(filename)
                llog = "decompressing file"+msg_data
                logging.info(llog)
                fgz = gzip.open(filename, 'r');
                line = fgz.readline()
                while line:
                        lines.append(line)
                        line = fgz.readline()
 
llog = "closing and deleting temporary file"
logging.info(llog)
fgz.close()
os.remove(filename)
