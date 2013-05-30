#!/bin/bash
set -o pipefail
STD_LOG=/home/buildfarm/buildbot_script/stdio.log
PACKAGE_LINK=$( awk -F"<result-dir>http:|</result-dir>" ' /<result-dir>/ { print $2 } ' $STD_LOG )
IDIR="PROPERTY_DIR"
USER="buildfarm"
PPAT_SERVER="10.38.32.203"

result=`grep ">PASS<" $STD_LOG`
if [ -n "$result" ]; then
  a=${@//$IDIR/$PACKAGE_LINK}
  ssh $USER@$PPAT_SERVER /home/buildfarm/ppat/startPPAT.sh $a
  exit 0
else
  echo "odvb failure"
  exit 1
fi
