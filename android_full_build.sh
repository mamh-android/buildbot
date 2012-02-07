#!/bin/bash
ids=$1  
echo $1
rm -f /home/buildfarm/buildbot_script/args.log
cd ~/aabs
var_0=`echo ${ids%%_*}`
if [ ! "${var_0}" == "rls" ]; then
  platform=`echo ${ids%%_*}`
  product=`echo ${ids#*_}`
  last_build="/autobuild/android/${platform}/LAST_BUILD.${platform}_${product}"
  target=${platform}-${product}
  echo "platform $platform" | tee -a /home/buildfarm/buildbot_script/args.log
  echo "product $product" | tee -a /home/buildfarm/buildbot_script/args.log
  echo "last_build $last_build" | tee -a /home/buildfarm/buildbot_script/args.log
  echo $target
else
  var_1=`echo ${ids#*_}`
  platform=`echo ${var_1%%_*}`
  echo "platform $platform" | tee -a /home/buildfarm/buildbot_script/args.log
  last=`echo ${var_1#*_}`
  product=`echo ${last%%_*}`
  echo "product $product" | tee -a /home/buildfarm/buildbot_script/args.log
  last=`echo ${last#*_}`
  if [ "$product" = "${last}" ]; then
    target="$platform-$product"
    last_build="/autobuild/android/${platform}/LAST_BUILD.${platform}-${product}"
  else
    echo "last $last" | tee -a /home/buildfarm/buildbot_script/args.log
    target="$platform-$product:$last"
    last_build="/autobuild/android/${platform}/LAST_BUILD.rls_${platform}_${product}_${last}"
  fi
  echo "last_build $last_build" | tee -a /home/buildfarm/buildbot_script/args.log
  echo $target
fi
tools/build_platforms.sh ${target} | tee -a log.txt
result=`grep ">PASS<" log.txt`
if [ -n "$result" ]; then
  nobuild=`grep ">No build<" log.txt`
  if [ -n "$nobuild" ]; then
    rm -f log.txt
    echo "no build"
    exit 255
  else
    echo "success"
    rm -f log.txt
    exit 0
  fi
else
  rm -f log.txt
  exit 1
  echo "failure"
fi
