#!/bin/bash
sour=$1
dest=$2
. ~/buildbot_script/buildbot/check_update.sh
cd ~/buildbot_script/
. /home/buildfarm/buildbot_script/buildbot/genDeltaPatchDiffFiles.sh ${sour} ${dest}
