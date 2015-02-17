#!/bin/sh
#

set -e

PWD=$(pwd)
LOGFILE=$PWD/"mirror-projects.log"

echo ============= | tee -a $LOGFILE
echo "[$(date)] start sync the projects" | tee -a $LOGFILE

#mirror added 2015-02-17 owner Tingting wang (BSP)
#git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git
    cd /git/git/ose/linux/mirror/git.kernel.org/kernel/linux-stable.git && git fetch origin | tee -a $LOGFILE

echo "[$(date)] completed sync the projects" | tee -a $LOGFILE
echo ============= | tee -a $LOGFILE
