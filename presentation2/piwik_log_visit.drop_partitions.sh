PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# creating temp files
PARTLIST=`mktemp`
DELLIST=`mktemp`

# creating trap to remove files when finished
atexit() {
        rm -f $PARTLIST
        rm -f $DELLIST
}
trap atexit 0

# get partition list, will break in next century
mysql  -ubackup -pxxxxx piwik  -e "show create table piwik_log_visit" -s |sed "s/\\\n/\n/g" |grep "PARTITION p20"|awk '{print $2}' > $PARTLIST

# check for minimum partitions quantity
LEN=`cat $PARTLIST|grep ^p2|wc -l`

if [ "$LEN" -gt "20" ]
then
        MINDATE=`date +%Y%m%d --date="21 days ago"` # get minimum date, 21 days of log tables
        if [ "$MINDATE" -lt "20120100" ] # dumb check for the data
        then
                echo ERRO ERRO ERRO ERRO # I told it is dumb
                exit 1 # exit 1 means it failed
        else

                for d in `cat $PARTLIST`
                do
                        TMP=`echo $d | sed s/p//` # get partition name
                        if [ "$TMP" -gt "20120000" ] # yet another dumb check
                        then
                                if [ "$TMP" -lt "$MINDATE" ]  # if partition is too old, put it in the deletion list
                                then
                                    echo "alter table piwik_log_visit drop partition $d ;"  >> $DELLIST
                                fi
                        else
                                echo ERRO1 ERRO1 ERRO1 ERRO1 # dumb error message
                                exit 1 # this is not dumb, exit code is captured by the monitoring system
                        fi
                done
        fi
fi

# format date to the dump's 'where'
MINDATE2=`date +%Y-%m-%d --date="21 days ago"` 

# format date for the dump's file name
UTC=`date +%s`

# make a backup of the deleted partitions
mysqldump -q -ubackup -pxxxxxxxxx piwik piwik_log_visit -w "visit_last_action_time < \"$MINDATE2 00:00:00\"" |gzip  > /db/backups/piwik_log_visit_BEFORE_$MINDATE2-$UTC.sql.gz || exit 1

# remove old partitions
mysql -ubackup -pxxxxxxxxxxxxx piwik < $DELLIST || exit 1
