#!/bin/bash
sour=$1
dest=$2
. ~/buildbot_script/buildbot/core/check_update.sh
cd ~/buildbot_script/
. ~/buildbot_script/buildbot/core/genDeltaPatchDiffFiles.sh ${sour} ${dest}
