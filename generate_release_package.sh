#!/bin/bash
input=$1
platform=$2
product=$3
release=$4
RC=$5
Release_package_path=$6
. ~/buildbot_script/buildbot/check_update.sh
echo $*
. /home/buildfarm/buildbot_script/buildbot/bbolt_cdrop.sh ${input} ${platform} ${product} ${release} ${RC} ${Release_package_path}
