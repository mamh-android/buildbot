#!/bin/bash
set -o pipefail
STD_LOG=/home/buildfarm/buildbot_script/stdio.log
rm $STD_LOG
. ~/buildbot_script/buildbot/core/check_update.sh | tee -a $STD_LOG
cd ~/buildbot_script/buildbot
. ~/buildbot_script/buildbot/core/upload_pub_rls.sh $@ | tee -a $STD_LOG
