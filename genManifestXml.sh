#!/bin/bash

# Command usage:
#genManifestXml b <manifest branch>

export SYNC_GIT_WORKING_DIR=${SYNC_GIT_WORKING_DIR:-~/aabs/gen_manifest}
export REFERENCE_URL=${REFERENCE_URL:-"--reference=/mnt/mirror/default"}
export SRC_URL=${SRC_URL:-ssh://shgit.marvell.com/git/android/platform/manifest.git}
export REPO_URL=${REPO_URL:-"--repo-url=ssh://shgit.marvell.com/git/android/tools/repo"}
export MANIFEST_URL=${MANIFEST_URL:-ssh://privgit.marvell.com:29418/buildbot/manifest_backup.git}
export DEVICES_TAB=${DEVICES_TAB:-~/aabs/tools/branchDevicesList}

#script path
SCRIPT_PATH=$(dirname `readlink -f $0`)/core

case "$1" in
    "-b") MANIFEST_BRANCH=$2
          echo "MANIFEST_BRANCH= $2"
          ;;
    *) echo "wrong parameter $1"; exit 1 ;;
esac

# Clean the working directory
rm -fr $SYNC_GIT_WORKING_DIR

# Create working diretory
if [ ! -d $SYNC_GIT_WORKING_DIR ]; then
    mkdir -p $SYNC_GIT_WORKING_DIR
fi
if [ $? -ne 0 ]; then
    echo "failed to create directory " $SYNC_GIT_WORKING_DIR
    exit 1
fi

#sync aabs
cd ~/aabs && git fetch origin && git reset --hard origin/master

cd $SYNC_GIT_WORKING_DIR
if [ $? -ne 0 ]; then
    echo "failed to enter " $SYNC_GIT_WORKING_DIR
    exit 1
fi

echo $SCRIPT_PATH

# Fetch code from Developer Server with mrvl-ics branch
$SCRIPT_PATH/fetchcode.py -u $SRC_URL -b $MANIFEST_BRANCH $REFERENCE_URL $REPO_URL
RET=$?
if [ $RET -ne 0 ]; then
    echo "failed on fetching code from master branch"
    echo "exit value:" $RET
    exit 1
fi

#Create manifest.xml
repo manifest -r -o manifest.xml
RET=$?
if [ $RET -ne 0 ]; then
    echo "failed on gen manifest.xml"
    echo "exit value:" $RET
    exit 1
fi

#create manifest review
if [ -d manifest_backup ]; then
    rm -rf manifest_backup
fi

Devices=$(cat $DEVICES_TAB | grep -w ${MANIFEST_BRANCH}=.* | cut -d '=' -f 2)

git clone $MANIFEST_URL
cp manifest.xml manifest_backup/manifest.xml
cd manifest_backup

for i in $Devices; do
    echo "#!/bin/bash" > run.sh
    echo export MANIFEST_BRANCH=${MANIFEST_BRANCH} >> run.sh
    echo export ABS_BUILD_DEVICES=${i} >> run.sh
    echo export ABS_BUILD_MANIFEST=manifst.xml >> run.sh
    echo export ABS_DEVICE_LIST=${Devices// /,} >> run.sh
    chmod +x run.sh
    git add run.sh manifest.xml
    git commit -sm "$(date) ${MANIFEST_BRANCH} ${i}"
done

#update gerrit
git push origin HEAD:refs/for/master
