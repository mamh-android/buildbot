CRIPT=`readlink -f $0`
BASEDIR=$(dirname $SCRIPT)
REMOTE_SERVER=github.marvell.com
ADMIN_USER=buildfarm
SRC_DIR=/mobile/android/default
DEST_DIR=/home/buildfarm/github_backup
LOGFILE=$BASEDIR/logs/backup_github.log

for remote_server in $REMOTE_SERVER; do
        echo "" | tee -a $LOGFILE
        echo "start at: `date --rfc-3339=seconds`" | tee -a $LOGFILE

        rsync -azv --delete -e ssh $ADMIN_USER@$REMOTE_SERVER:$SRC_DIR $DEST_DIR | tee -a $LOGFILE
        # Add as many directory as you wish.
        # rsync -az --delete -e ssh $ADMIN_USER@$REMOTE_SERVER:$SRC_DIR $DEST_DIR
        echo "rsync done at: `date --rfc-3339=seconds`" | tee -a $LOGFILE
        cd $DEST_DIR

        if [ ! -d ".git" ]; then
                git init . | tee -a $LOGFILE
        fi

        git add -A | tee -a $LOGFILE
        git commit -a -s -m "Autorsync:synced from $REMOTE_SERVER:$SRC_DIR `date --rfc-3339=seconds`" | tee -a $LOGFILE
        git gc | tee -a $LOGFILE

        echo "done at: `date --rfc-3339=seconds`" | tee -a $LOGFILE
done
