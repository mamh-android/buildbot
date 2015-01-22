#!/bin/bash
#
# V1: 2014-12-3:Yufei: initial code

set -e

VERSION=1
DB_GIT_PATH="/home/gerrit2/backup_gerritdatabase/shgit_database/"
PG_DUMP="pg_dump reviewdb_2015_01 > reviewdb.sql"

#dump DB
cd $DB_GIT_PATH && pg_dump reviewdb_2015_01 > reviewdb.sql
RET=$?
if [ $RET -ne 0 ]; then
    echo "failed on dumping the databases"
    echo "exit value:" $RET
    exit 1
fi

#push to git
git commit -a -s -m "Autodump: $PG_DUMP `date --rfc-3339=seconds`" && git push origin HEAD:master
RET=$?
if [ $RET -ne 0 ]; then
    echo "failed on pushing git"
    echo "exit value:" $RET
    exit 1
fi
