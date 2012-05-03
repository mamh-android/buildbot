#!/bin/bash
sour=$1
dest=$2
cd ~/buildbot_script/
. /home/buildfarm/buildbot_script/buildbot/genDeltaPatchDiffFiles.sh ${sour} ${dest}
