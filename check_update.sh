#!/bin/bash
get_date()
{
  echo $(date "+%Y-%m-%d %H:%M:%S")
}
LOG=buildbot_script_update.log
echo "[buildbot][$(get_date)] start to fetch buildbot scripts..." | tee -a $LOG
cd ~/buildbot_script/buildbot
git fetch origin 2>&1 | tee -a $LOG
if [ $? -ne 0 ]; then
    echo "[buildbot] fetch scripts failed" | tee -a $LOG
    exit 10
fi
echo "[buildbot] fetch scripts done." | tee -a $LOG
current_head=$(git rev-parse HEAD)
if [ $? -ne 0 ]; then
    echo "[buildbot] git rev-parse HEAD return errors" | tee -a $LOG
    exit 20
fi
new_head=$(git rev-parse origin/master)
if [ $? -ne 0 ]; then
    echo "[buildbot] git -rev-parse origin/master return errors" | tee -a $LOG
    exit 30
fi
if [ ! "$current_head" = "$new_head" ]; then
    echo "[buildbot]=============================" | tee -a $LOG
    echo "[buildbot] start to check orign/master " | tee -a $LOG
    echo "[buildbot]=============================" | tee -a $LOG
    git checkout origin/master 2>&1 | tee -a $LOG
    if [ $? -ne 0 ]; then
    echo "[buildbot] git checkout orign/master failed" | tee -a $LOG
    exit 40
    fi
    echo "[buildbot]$(get_date) update scripts done" | tee -a $LOG
else
    echo "[buildbot][$(get_date)] there is nothing to update" | tee -a $LOG
fi
cd ~/buildbot_script/buildbot
