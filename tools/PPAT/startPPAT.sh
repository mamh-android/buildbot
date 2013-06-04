#!/bin/bash
set -o pipefail
STD_LOG=/home/buildfarm/buildbot_script/stdio.log
PACKAGE_LINK=$( awk -F"<result-dir>http:|</result-dir>" ' /<result-dir>/ { print $2 } ' $STD_LOG )
IDIR="PROPERTY_DIR"
USER="buildfarm"
PPAT_SERVER="10.38.32.203"

ids_0=$1
ids_1=$2
ids_2=$3
ids_3=$PACKAGE_LINK
ids_4=$5
ids_5=$6
ids_6=$7
ids_7=$8
ids_8=$9
ids_9=${10}
ids_10=${11}
ids_11=${12}
ids_12=${13}
ids_13=${14}
ids_14=${15}
ids_15="'"${16}"'"
ids_16=${17}
ids_17="'"${18}"'"

result=`grep ">PASS<" $STD_LOG`
if [ -n "$result" ]; then
  echo "************start PPAT with parameters*************"
  echo $ids_0 $ids_1 $ids_2 $ids_3 $ids_4 $ids_5 $ids_6 $ids_7 $ids_8 $ids_9 $ids_10 $ids_11 $ids_12 $ids_13 $ids_14 $ids_15 $ids_16 $ids_17
  ssh $USER@$PPAT_SERVER /home/buildfarm/ppat/startPPAT.sh $ids_0 $ids_1 $ids_2 $ids_3 $ids_4 $ids_5 $ids_6 $ids_7 $ids_8 $ids_9 $ids_10 $ids_11 $ids_12 $ids_13 $ids_14 $ids_15 $ids_16 $ids_17 
  exit 0
else
  echo "odvb failure"
  exit 1
fi
