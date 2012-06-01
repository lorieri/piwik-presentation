PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
PARTLIST=`mktemp`
CREATELIST=`mktemp`
atexit() {
        rm -f $PARTLIST
        rm -f $CREATELIST
}
trap atexit 0
mysql  -ubackup -pxxxxxxxx piwik  -e "show create table piwik_log_visit" -s |sed "s/\\\n/\n/g" |grep "PARTITION p20"|awk '{print $2}'|tail -1 > $PARTLIST
LEN=`cat $PARTLIST|grep ^p2|wc -l`
if [ "$LEN" -eq "1" ]
then
        MINDATE=`date +%Y%m%d --date="-2 days"`
        MAXDATE=`date +%Y%m%d --date="+21 days"` # maximum date
        LASTPAR=`cat $PARTLIST|sed s/p//`
        if [ "$LASTPAR" -gt "$MINDATE" ]
        then
                for d in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 # create for next 15 days, not a problem create existent days
                do
                        TMPNAME=`date +%Y%m%d --date="+$d days"`
                        if [ "$TMPNAME" -gt "$LASTPAR" ]
                        then
                                TMPD=`echo $d+1|bc`
                                TMPMAXDATE=`date +%Y-%m-%d --date="+$TMPD days"`
                                echo "alter table piwik_log_visit add partition ( partition p$TMPNAME values less than (to_days('$TMPMAXDATE')));" >> $CREATELIST
                        fi
                done
        else
                exit 1
        fi
else
        exit 1
fi
mysql -A -ubackup -pxxxxxxxxxxx piwik < $CREATELIST || exit 1
