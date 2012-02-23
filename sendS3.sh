#!/bin/bash

#crontab line:
#*/5 * * * *  nice /bin/bash /usr/loca/bin/VHOST.sendS3.sh >> /mnt/log/VHOST.send.log 2>&1


date #print date to the log
DEBUGS3=`mktemp`
atexit() {
        rm -f $DEBUGS3
}
trap atexit 0

BUCKET="MYBUCKET"
PROJECT="MYVHOST"
ARCHIVEDIR="/mnt/MYVHOST/"
S3CMD_CONF="/usr/local/s3cmd.cfg"
ORIGINPATH="/mnt/log/nginx/VHOST.access.log"
SNS_ENV="/usr/local/sns_env.source"
SNS_TOPIC="MYTOPIC"
 
HOST=`hostname` #we use instance-id on amazon
DATE=$(date --utc +%Y%m%d_%H%M%S)
DATEDIR=$(date --utc +%Y/%m/%d)

POSTPATH="$PROJECT/$DATEDIR/$PROJECT-$DATE-$HOST.log"
LOCALPATH="$ARCHIVEDIR/$POSTPATH"
GZLOCALPATH="$LOCALPATH.gz"
REMOTEPATH="s3://$BUCKET/$POSTPATH.gz"

echo "->Trying file: $REMOTEPATH"

LOCALDIR="$(dirname "$LOCALPATH")"

#sleep 1 recomended by nginx's wiki
mkdir -p "$LOCALDIR" &&
mv "$ORIGINPATH" "$LOCALPATH" &&
{ [ ! -f /var/run/nginx.pid ] || kill -USR1 `cat /var/run/nginx.pid` ; }  &&
sleep 1 &&
gzip "$LOCALPATH" &&
{ MD5=$(/usr/bin/md5sum "$GZLOCALPATH" | awk '{ print $1 }') ; }

#try 3 times
if [ -z "$MD5" ]
then
        echo "ERROR ON MD5"
        OK=1
else
        OK=$(/usr/bin/s3cmd -d --no-progress -c "$S3CMD_CONF" put "$GZLOCALPATH" "$REMOTEPATH" 2>&1 |grep -q "DEBUG: MD5 sums: computed=$MD5, received=\"$MD5\"";echo $?)
        if [ "$OK" -eq "1" ]
        then
                OK=$(/usr/bin/s3cmd -d --no-progress -c "$S3CMD_CONF" put "$GZLOCALPATH" "$REMOTEPATH" 2>&1 |grep -q "DEBUG: MD5 sums: computed=$MD5, received=\"$MD5\"";echo $?)
                if [ "$OK" -eq "1" ]
                then
                        /usr/bin/s3cmd -d --no-progress -c "$S3CMD_CONF" put "$GZLOCALPATH" "$REMOTEPATH" 2>&1|tee "$DEBUGS3"
                        OK=$(grep -q "DEBUG: MD5 sums: computed=$MD5, received=\"$MD5\"" "$DEBUGS3"; echo $?)
                fi
        fi
fi

# if ok, publish a message on SNS
 
if [ "$OK" = "0" ]
then
        source "$SNS_ENV"
        echo -n '-> Message: '
        sns-publish "$TOPIC" --message "$REMOTEPATH"
        OK=${PIPESTATUS[0]}
fi

echo "OK=$OK"
#for monitoring
#/usr/bin/zabbix_sender -s "$HOST" -z XXXXXX.com -k XXXXXX -o "$OK"
