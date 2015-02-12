#!/bin/bash
#
# disk release script, clean src.* and out.* of unactive branches
#
# History:
# V1: 2015-2-12:Yufei: initial code

set -e

VERSION=1

  BUILDMASTER=10.38.34.92
  BRANCHES=$(ssh $BUILDMASTER cat ~/buildbot/sandbox/master/master.cfg | awk -F'=|\"|\,' ' /timed.Nightly\(name=/ { print $8 } ')
  AABS_F=~/aabs

PWD=$(pwd)
LOGFILE=$PWD/"disk-release.log"

get_build_dir(){
    branch=$1
    var=`echo ${branch%%_*}`
    if [ ! "${var}" == "rls" ]; then
        export platform=`echo ${branch%%_*}`
        export version=`echo ${branch#*_}`
        export srcDir="src.$platform-$version"
        export outDir="out.$platform-$version"
    else
        var_1=`echo ${branch#*_}`
        export platform=`echo ${var_1%%_*}`
        last=`echo ${var_1#*_}`
        export version=`echo ${last%%_*}`
        export ex_version=`echo ${last#*_}`
        export srcDir="src.$platform-$version.$ex_version"
        export outDir="out.$platform-$version.$ex_version"
    fi
    echo srcDir: $srcDir
}

cd $AABS_F
srcList=$(ls -d src.*)
outList=$(ls -d out.*)

for branch in $BRANCHES; do
    get_build_dir $branch
    srcList=$(echo $srcList | sed "s/${srcDir}//")
    outList=$(echo $outList | sed "s/${outDir}//")
done

echo =============
echo $srcList
echo =============
echo $outList

#clean folder
echo ============= | tee -a $LOGFILE
echo "[$(date)] start clean the folder" | tee -a $LOGFILE
for i in $srcList; do
    if [ -d $i ]; then
        echo "[$(date)] clean folder: $i" | tee -a $LOGFILE
        rm -rf $i
    fi
done
for i in $outList; do
    if [ -d $i ]; then
        echo "[$(date)] clean folder: $i" | tee -a $LOGFILE
        rm -rf $i
    fi
done
echo "[$(date)] completed clean the folder" | tee -a $LOGFILE
