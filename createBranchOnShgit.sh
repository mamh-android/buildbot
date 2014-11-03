#!/bin/bash
#
# Need environment variables:
#       SYNC_GIT_WORKING_DIR:   working directory
#       REFERENCE_URL:          url of repo reference
#       SRC_URL:                manifest path in source server
#       REPO_URL:               repo url

# Command usage:
#createBranchOnShgit.sh b <manifest branch> -m <manifest xml>

export SYNC_GIT_WORKING_DIR=${SYNC_GIT_WORKING_DIR:-~/aabs/create_branch}
export REFERENCE_URL=${REFERENCE_URL:-"--reference=/mnt/mirror/default"}
export SRC_URL=${SRC_URL:-ssh://shgit.marvell.com/git/android/platform/manifest.git}
export REPO_URL=${REPO_URL:-"--repo-url=ssh://shgit.marvell.com/git/android/tools/repo"}

#script path
SCRIPT_PATH=$(dirname `readlink -f $0`)/core

case "$1" in
    "-b") MANIFEST_BRANCH=$2
          echo "MANIFEST_BRANCH= $2"
          ;;
    *) echo "wrong parameter $1"; exit 1 ;;
esac
case "$3" in
    "-m") MANIFEST_XML=$4
    if [ -f $MANIFEST_XML ]; then
        echo "$MANIFEST_XML exists"
        MANIFEST_NAME=$(basename $4)
        BUILD_DIR=$(dirname $4)
    else
        echo "$4 doesn't exist"
        exit 1
    fi
    ;;
    *) echo "wrong parameter $3"; exit 1 ;;
esac
case "$5" in
    "-a") RUN_TYPE=$6
          echo "$6"
          ;;
    *) echo "wrong parameter $5"; exit 1 ;;
esac

# Clean the working directory
rm -fr $SYNC_GIT_WORKING_DIR

# Create working diretory
mkdir -p $SYNC_GIT_WORKING_DIR
if [ $? -ne 0 ]; then
    echo "failed to create directory " $SYNC_GIT_WORKING_DIR
    exit 1
fi

cd $SYNC_GIT_WORKING_DIR
if [ $? -ne 0 ]; then
    echo "failed to enter " $SYNC_GIT_WORKING_DIR
    exit 1
fi

# Copy manifest xml into current directory
echo Copy: $4
cp $4 $MANIFEST_NAME

echo $SCRIPT_PATH

# Fetch code from Developer Server with mrvl-ics branch
#$SCRIPT_PATH/fetchcode.py -u $SRC_URL -b $MANIFEST_BRANCH $REFERENCE_URL $REPO_URL
$SCRIPT_PATH/fetchcode.py -u $SRC_URL -b master $REFERENCE_URL $REPO_URL
RET=$?
if [ $RET -ne 0 ]; then
    echo "failed on fetching code from master branch"
    echo "exit value:" $RET
    exit 1
fi

# Fetch code from Developer Server with manifest xml
$SCRIPT_PATH/fetchcode.py -u $SRC_URL -m $MANIFEST_NAME $REFERENCE_URL $REPO_URL
RET=$?
if [ $RET -ne 0 ]; then
    echo "failed on fetching code from manifest xml"
    echo "exit value:" $RET
    exit 1
fi

#Usage: rls_branch.sh <create|delete> <release-branch-name> <unique|multiple> [<actual-run>] [<project> ...]
$SCRIPT_PATH/rls_branch.sh create $MANIFEST_BRANCH multiple $RUN_TYPE
