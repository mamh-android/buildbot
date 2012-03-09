#!/bin/bash
input=$1
platform=$2
product=$3
release=$4
RC=$5
echo $*
foldername="${platform}-${product}.${release}${RC}"
cd /home/buildfarm/release
mkdir ${foldername}
. /home/buildfarm/buildbot_script/buildbot/bbolt_cdrop.sh -i ${input} -o /home/buildfarm/release/${foldername} -l /home/buildfarm/release/content
