#!/bin/bash

cbranch=$1

if [ ${cbranch%%/*} == "master" ]; then
    changid=${cbranch#*/}
    obj=$(echo $changid|rev|cut -c-2|rev)
    git clone ssh://privgit.marvell.com:29418/buildbot/manifest_backup
    cd manifest_backup && git fetch ssh://privgit.marvell.com:29418/buildbot/manifest_backup refs/changes/$obj/$changid/1 && git reset --hard FETCH_HEAD && cd -
    . manifest_backup/run.sh
else
    MANIFEST_BRANCH=$1
fi

echo Build Branch: $MANIFEST_BRANCH
echo ABS_BUILD_DEVICES: $ABS_BUILD_DEVICES
echo ABS_BUILD_MANIFEST: $ABS_BUILD_MANIFEST
echo ABS_DEVICE_LIST: $ABS_DEVICE_LIST

ids_2=$2
echo PLATFORM_ANDROID_VARIANT: $2
STD_LOG=/home/buildfarm/buildbot_script/stdio.log
rm -f $STD_LOG
. ~/buildbot_script/buildbot/core/check_update.sh
cd ~/aabs && git reset --hard origin/master
if [ "$ids_2" != "" -a "$ids_2" != "None" ]; then
  export PLATFORM_ANDROID_VARIANT=$ids_2
  export ABS_FORCE_BUILD="ture"
fi

var_0=`echo ${MANIFEST_BRANCH%%_*}`
if [ ! "${var_0}" == "rls" ]; then
  target=$MANIFEST_BRANCH
  last_build="/autobuild/android/${platform}/LAST_BUILD.${target}"
  echo "platform-product $target" | tee -a $STD_LOG
  echo "last_build $last_build" | tee -a $STD_LOG
else
  var_1=`echo ${MANIFEST_BRANCH#*_}`
  platform=`echo ${var_1%%_*}`
  echo "platform $platform" | tee -a $STD_LOG
  last=`echo ${var_1#*_}`
  product=`echo ${last%%_*}`
  echo "product $product" | tee -a $STD_LOG
  last=`echo ${last#*_}`
  if [ "$product" = "${last}" ]; then
    target="$platform-$product"
    last_build="/autobuild/android/${platform}/LAST_BUILD.${platform}-${product}"
  else
    echo "last $last" | tee -a $STD_LOG
    target="$platform-$product:$last"
    last_build="/autobuild/android/${platform}/LAST_BUILD.rls_${platform}_${product}_${last}"
  fi
  echo "last_build $last_build" | tee -a $STD_LOG
  echo $target
fi
tools/build_platforms.sh ${target} | tee -a $STD_LOG
result=`grep ">PASS<" $STD_LOG`
if [ -n "$result" ]; then
  nobuild=`grep ">No build<" $STD_LOG`
  if [ -n "$nobuild" ]; then
    echo "no build"
    exit 255
  else
    echo "success"
    exit 0
  fi
else
  exit 1
  echo "failure"
fi
