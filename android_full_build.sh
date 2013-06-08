#!/bin/bash
ids=$1  
echo Build Branch: $1
ids_2=$2
echo PLATFORM_ANDROID_VARIANT: $2
STD_LOG=/home/buildfarm/buildbot_script/stdio.log
rm -f $STD_LOG
. ~/buildbot_script/buildbot/core/check_update.sh
cd ~/aabs
if [ "$ids_2" != "" -a "$ids_2" != "None" ]; then
  export PLATFORM_ANDROID_VARIANT=$ids_2
  export ABS_FORCE_BUILD="ture"
fi
var_0=`echo ${ids%%_*}`
if [ ! "${var_0}" == "rls" ]; then
  platform=`echo ${ids%%_*}`
  product=`echo ${ids#*_}`
  last_build="/autobuild/android/${platform}/LAST_BUILD.${platform}_${product}"
  target=${platform}-${product}
  echo "platform $platform" | tee -a $STD_LOG
  echo "product $product" | tee -a $STD_LOG
  echo "last_build $last_build" | tee -a $STD_LOG
  echo $target
else
  var_1=`echo ${ids#*_}`
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
