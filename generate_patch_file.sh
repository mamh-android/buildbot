#!/bin/bash
sour=$1
dest=$2
output=$3
cd ~/buildbot_script/
. /home/buildfarm/buildbot_script/buildbot/genDiff.sh ${sour} ${dest} ${output}
. /home/buildfarm/buildbot_script/buildbot/genDeltaPatch.sh ${sour} ${dest} ${output}
