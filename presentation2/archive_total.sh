for TEST_PHP_BIN in php5 php php-cli php-cgi; do
  if which $TEST_PHP_BIN >/dev/null 2>/dev/null; then
    PHP_BIN=`which $TEST_PHP_BIN`
    break
  fi
done
if test -z $PHP_BIN; then
  echo "php binary not found. Make sure php5 or php exists in PATH." >&2
  exit 1
fi

act_path() {
  local pathname="$1"
  readlink -f "$pathname" 2>/dev/null || \
  realpath "$pathname" 2>/dev/null || \
  type -P "$pathname" 2>/dev/null
}

ARCHIVE=`act_path ${0}`
PIWIK_CRON_FOLDER=`dirname ${ARCHIVE}`
PIWIK_PATH="$PIWIK_CRON_FOLDER"/../../index.php
PIWIK_CONFIG="$PIWIK_CRON_FOLDER"/../../config/config.ini.php

PIWIK_SUPERUSER=`sed '/^\[superuser\]/,$!d;/^login[ \t]*=[ \t]*"*/!d;s///;s/"*[ \t]*$//;q' $PIWIK_CONFIG`
PIWIK_SUPERUSER_MD5_PASSWORD=`sed '/^\[superuser\]/,$!d;/^password[ \t]*=[ \t]*"*/!d;s///;s/"*[ \t]*$//;q' $PIWIK_CONFIG`

CMD_TOKEN_AUTH="$PHP_BIN -q $PIWIK_PATH -- module=API&method=UsersManager.getTokenAuth&userLogin=$PIWIK_SUPERUSER&md5Password=$PIWIK_SUPERUSER_MD5_PASSWORD&format=php&serialize=0"
TOKEN_AUTH=`$CMD_TOKEN_AUTH`

CMD_GET_ID_SITES="$PHP_BIN -q $PIWIK_PATH -- module=API&method=SitesManager.getAllSitesId&token_auth=$TOKEN_AUTH&format=csv&convertToUnicode=0"
ID_SITES=`$CMD_GET_ID_SITES`

#same as piwik's archive.sh until this line


echo "Starting Piwik reports archiving... `date`"
echo ""

# daily

A=0
for idsite in $ID_SITES; do
  A=`echo $A+1|bc`
  TEST_IS_NUMERIC=`echo $idsite | egrep '^[0-9]+$'`
  if test -n "$TEST_IS_NUMERIC"; then
    if [ "$idsite" -ne "66" ]; then
      period=day
      last=last2
      echo ""
      echo "Archiving $period = $period for idsite = $idsite... `date`"
      CMD="$PHP_BIN -q $PIWIK_PATH -- module=API&method=VisitsSummary.getVisits&idSite=$idsite&period=$period&date=$last&format=xml&token_auth=$TOKEN_AUTH"
      $CMD &
      if [ "$A" -gt "5" ]
      then
          A=0
          wait
      fi
    fi
  fi
done
wait




# week

A=0
for idsite in $ID_SITES; do
  A=`echo $A+1|bc`
  TEST_IS_NUMERIC=`echo $idsite | egrep '^[0-9]+$'`
  if test -n "$TEST_IS_NUMERIC"; then
    if [ "$idsite" -ne "66" ]; then
      period=week
      last=last2
      echo ""
      echo "Archiving $period = $period for idsite = $idsite... `date`"
      CMD="$PHP_BIN -q $PIWIK_PATH -- module=API&method=VisitsSummary.getVisits&idSite=$idsite&period=$period&date=$last&format=xml&token_auth=$TOKEN_AUTH"
      $CMD &
      if [ "$A" -gt "1"]
      then
          A=0
          wait
      fi
    fi
  fi
done
wait




# month

A=0
for idsite in $ID_SITES; do
  A=`echo $A+1|bc`
  TEST_IS_NUMERIC=`echo $idsite | egrep '^[0-9]+$'`
  if test -n "$TEST_IS_NUMERIC"; then
    if [ "$idsite" -ne "66" ]; then
      period=month
      last=last2
      echo ""
      echo "Archiving $period = $period for idsite = $idsite... `date`"
      CMD="$PHP_BIN -q $PIWIK_PATH -- module=API&method=VisitsSummary.getVisits&idSite=$idsite&period=$period&date=$last&format=xml&token_auth=$TOKEN_AUTH"
      $CMD &
      if [ "$A" -gt "4" ]
      then
          A=0
          wait
      fi
    fi
  fi
done
wait




# year

A=0
for idsite in $ID_SITES; do
  A=`echo $A+1|bc`
  TEST_IS_NUMERIC=`echo $idsite | egrep '^[0-9]+$'`
  if test -n "$TEST_IS_NUMERIC"; then
    if [ "$idsite" -ne "66" ]; then
      period=year
      last=last2
      echo ""
      echo "Archiving $period = $period for idsite = $idsite... `date`"
      CMD="$PHP_BIN -q $PIWIK_PATH -- module=API&method=VisitsSummary.getVisits&idSite=$idsite&period=$period&date=$last&format=xml&token_auth=$TOKEN_AUTH"
      $CMD &
      if [ "$A" -gt "4" ]
      then
          A=0
          wait
      fi
    fi
  fi
done
wait


echo "End `date`"
