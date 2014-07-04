#!/bin/bash
set -o pipefail
TRIGGER=/home/buildfarm/buildbot/slave/ppat_test/build_script/trigger.py
STD_LOG=/home/buildfarm/buildbot_script/stdio.log
PACKAGE_LINK=$( awk -F"<result-dir>http:|</result-dir>" ' /<result-dir>/ { print $2 } ' $STD_LOG )
#IDIR="PROPERTY_DIR"
#USER="buildfarm"
#PPAT_PXA988_SERVER="10.38.32.98"
#PPAT_EDEN_SERVER="10.38.32.98"

ids_1="'"$1"'"
ids_2="'"$2"'"
ids_3="'"$3"'"
ids_4="'"$4"'"
ids_5="'"$5"'"

result=`grep ">PASS<" $STD_LOG`
if [ -n "$result" ]; then
  echo "************start PPAT with parameters*************"
  echo $PACKAGE_LINK $ids_1 $ids_2 $ids_3 $ids_4 $ids_5
  $TRIGGER --imagepath $PACKAGE_LINK --device $ids_1 --blf $ids_2 --assigner $ids_3 --testcase $ids_4 --purpose $ids_5 --mode manual
  exit 0
else
  echo "odvb failure"
  exit 1
fi
