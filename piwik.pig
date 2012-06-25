
-- COPIED FROM AMAZON TUTORIALS
-- http://aws.amazon.com/articles/Elastic-MapReduce
--
-- setup piggyback functions
--
register file:/home/hadoop/lib/pig/piggybank.jar
DEFINE EXTRACT org.apache.pig.piggybank.evaluation.string.EXTRACT;
DEFINE FORMAT org.apache.pig.piggybank.evaluation.string.FORMAT;
DEFINE REPLACE org.apache.pig.piggybank.evaluation.string.REPLACE;
DEFINE DATE_TIME org.apache.pig.piggybank.evaluation.datetime.DATE_TIME;
DEFINE FORMAT_DT org.apache.pig.piggybank.evaluation.datetime.FORMAT_DT;

--
-- import logs and break into tuples
--
RAW_LOGS =
  -- load the weblogs into a sequence of one element tuples
  LOAD '$INPUT' USING TextLoader AS (line:chararray);


LOGS_BASE = FOREACH RAW_LOGS GENERATE
    FLATTEN(
      EXTRACT(line, '^(\\S+) (\\S+) (\\S+) \\[([\\w:/]+\\s[+\\-]\\d{4})\\]\\s+"(.+?)" (\\S+) (\\S+) "([^"]*)" "([^"]*)" "([^"]*\\buid=([A-Fa-f0-9]+)[^"]*)"') ) as (
      remoteAddr:    chararray,
      remoteLogname: chararray,
      user:          chararray,
      time:          chararray,
      request:       chararray,
      status:        int,
      bytes_string:  chararray,
      referrer:      chararray,
      browser:       chararray,
      cookies:       chararray,
      uid:       chararray
  )
;

J = foreach LOGS_BASE generate uid;
K = DISTINCT J;
store K into '$OUTPUT';

