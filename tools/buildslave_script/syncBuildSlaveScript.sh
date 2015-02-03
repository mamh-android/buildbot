#!/bin/bash
#
# V1: 2014-12-3:Yufei: initial code

set -e

VERSION=1
BUILDSLAVE_LIST="bf-c2 bf-c3 bf-c4 bf-c5 bf-f1 bf-f2 bf-f3"
SCRIPT_PATH=/home/buildfarm/buildbot_script/buildbot
GIT_SYNC="cd $SCRIPT_PATH && git fetch origin;cd $SCRIPT_PATH && git reset --hard origin/master;"

for i in $BUILDSLAVE_LIST; do
    echo ====================================
    echo sync BuildScript of buildslave $i
    ssh buildfarm@$i "$GIT_SYNC"
done
