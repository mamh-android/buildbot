#!/bin/sh
#buildmaster backup

SCRIPT=`readlink -f $0`
BASEDIR=$(dirname $SCRIPT)
GIT_DIR=/home/buildfarm/buildbot_backup_script/backup_last_buildmaster/
SRC_DIR_1=/home/buildfarm/buildbot/sandbox/lib/python2.6/site-packages/buildbot-0.8.5-py2.6.egg
DEST_DIR_1=/home/buildfarm/buildbot_backup_script/backup_last_buildmaster/buildbot/
SRC_DIR_2=/home/buildfarm/buildbot/sandbox/master/master.cfg
DEST_DIR_2=/home/buildfarm/buildbot_backup_script/backup_last_buildmaster/
SRC_DIR_3=/home/buildfarm/buildbot/sandbox/master/public_html
DEST_DIR_3=/home/buildfarm/buildbot_backup_script/backup_last_buildmaster/
SRC_DIR_4=/home/buildfarm/buildbot/sandbox/master/updateuser
DEST_DIR_4=/home/buildfarm/buildbot_backup_script/backup_last_buildmaster/
LOGFILE=$BASEDIR/backup.log

echo "" | tee -a $LOGFILE
echo "start at: `date --rfc-3339=seconds`" | tee -a $LOGFILE
rsync -azv $SRC_DIR_1 $DEST_DIR_1 | tee -a $LOGFILE
rsync -azv $SRC_DIR_2 $DEST_DIR_2 | tee -a $LOGFILE
rsync -azv $SRC_DIR_3 $DEST_DIR_3 | tee -a $LOGFILE
rsync -azv $SRC_DIR_4 $DEST_DIR_4 | tee -a $LOGFILE
echo "rsync done at: `date --rfc-3339=seconds`" | tee -a $LOGFILE

cd $GIT_DIR

if [ ! -d ".git" ]; then
  git init . | tee -a $LOGFILE
fi

git add -A | tee -a $LOGFILE
git commit -asm "Autorsync:synced done `date --rfc-3339=seconds`" | tee -a $LOGFILE
git gc | tee -a $LOGFILE
git push ssh://shgit/git/android/shared/Buildbot/buildbot_master.git HEAD:refs/heads/backup | tee -a $LOGFILE

echo "done at: `date --rfc-3339=seconds`" | tee -a $LOGFILE
