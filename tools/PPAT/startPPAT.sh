#!/bin/bash
set -o pipefail
STD_LOG=/home/buildfarm/buildbot_script/stdio.log
PACKAGE_LINK=$( awk -F"<result-dir>http://10.38.116.40|</result-dir>" ' /<result-dir>/ { print $2 } ' $STD_LOG )
IDIR="PROPERTY_DIR"

result=`grep ">PASS<" $STD_LOG`
if [ -n "$result" ]; then
  a=${@//$IDIR/$PACKAGE_LINK}
  ssh zhoulz@10.38.32.178 /home/zhoulz/ppat/startPPAT.sh $a
  exit 0
else
  echo "odvb failure"
  exit 1
fi
