#!/bin/bash
set -o pipefail
input=$1
platform=$2
product=$3
release=$4
RC=$5
Release_package_path=$6
. ~/buildbot_script/buildbot/core/check_update.sh
echo $*
. ~/buildbot_script/buildbot/core/bbolt_cdrop.sh ${input} ${platform} ${product} ${release} ${RC} ${Release_package_path}
