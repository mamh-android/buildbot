#!/bin/bash

#BRANCHES="android-5.0.0_r2 android-4.4_r1 master android-5.1.0_r1"
BRANCHES="master"

LOGFILE=sync.log

REPO=~/bin/repo

cd .repo/manifests
git reset --hard
cd -

sync_gerrit_permission(){
GERRIT_S=buildfarm@shgit.marvell.com
find . -name "[a-zA-Z0-9]*.git" -type d |while read file
do
    if ! (find $file -name "meta" | grep -q "meta"); then
        echo $file
        ssh -p 29418 $GERRIT_S gerrit set-project-parent --parent Permission_parent/All-android /git/android${file#*.}
    fi
done
}

for branch in $BRANCHES; do
    echo "" | tee -a $LOGFILE
    echo "[$(date)] start sync branch:$branch" | tee -a $LOGFILE
    while [ 1 ]; do
        $REPO init -b $branch 2>&1 | tee -a $LOGFILE &&
        $REPO sync -f 2>&1 | tee -a $LOGFILE 
        if [ $? -eq 0 ]; then
            echo "[$(date)] sync branch:$branch successfully." | tee -a $LOGFILE
            break
        else
            echo "[$(date)] error encounted in sync branch $branch. retry in 10 seconds." | tee -a $LOGFILE
            sleep 10s
        fi
    done    
done
