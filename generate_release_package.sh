#!/bin/bash
input=$1
platform=$2
product=$3
release=$4
RC=$5
echo $*
foldername="${platform}-${product}.${release}${RC}"
cd ~/buildbot_script
mkdir ${foldername}
. /home/buildfarm/buildbot_script/buildbot/bbolt_cdrop.sh -i /autobuild/android/${platform}/${input} -o ~/buildbot_script/${foldername}  -l /home/buildfarm/buildbot_script/content
