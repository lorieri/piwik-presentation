PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

CHECK=`date +%Y%m%d --date='+1 Days'`
ls /var/db/mysql/piwik/piwik_log_visit#P#p20* |grep p$CHECK > /dev/null || exit 1
TOTAL=`ls /var/db/mysql/piwik/piwik_log_visit#P#p20*|wc -l`


# 21 days ago + 15 days ahead, 15 subpartitions for each day = 540 files, limit is 1024, 800 is a good alert number
if [ "$TOTAL" -gt "800" ] 
then
    exit 1
else
    if [ "$TOTAL" -lt "5" ]  # did I get the right table ? dumb check
    then
        exit 1
    fi
fi
