#!/bin/bash
sour=$1
dest=$2
output=$3
cd ${output}
cp /home/buildfarm/buildbot_script/buildbot/diffz ./
. /home/buildfarm/buildbot_script/buildbot/genDiff.sh ${sour} ${dest}
. /home/buildfarm/buildbot_script/buildbot/genDeltaPatch.sh ${sour} ${dest}
