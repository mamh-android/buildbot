#!/bin/sh

SCRIPT=`readlink -f $0`
BASEDIR=$SCRIPT
REMOTE_SERVER=github.marvell.com
ADMIN_USER=buildfarm
SRC_DIR=/mobile/android/default
DEST_DIR=/home/github_backup

#cd $BASEDIR

rsync -az --delete -e ssh $ADMIN_USER@$REMOTE_SERVER:$SRC_DIR $DEST_DIR
# Add as many directory as you wish.
# rsync -az --delete -e ssh $ADMIN_USER@$REMOTE_SERVER:$SRC_DIR $DEST_DIR

cd $DEST_DIR

if [ ! -d ".git" ]; then
  git init .
fi

git add -A
git commit -a -s -m "Autorsync:synced from $REMOTE_SERVER:$SRC_DIR `date --rfc-3339=seconds`"
git gc
