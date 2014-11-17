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

build_maintainer="yfshi@marvell.com"
DEV_TEAM="APSE"

#script path
SCRIPT_PATH=$(dirname `readlink -f $0`)/core

dir_to_branch() {
    filename=$(basename $1)
    id_1=${filename#*_pxa}
    id_2=${id_1#*_}
    if [ $id_1 == $id_2 ]; then
        output=pxa$id_1
    else
        output=rls_pxa${id_1//-/_}
    fi
    echo $output
}

generate_success_notification_email() {
cat <<-EOF
From: $build_maintainer
To: $USEREMAIL,
Subject: [Create a release branch] is done.

This is an automated email from the autobuild script. It was
generated because createRlsBranch is success.

=====================
How to fetch the code
=====================
repo init -u $SRC_URL -b $MANIFEST_BRANCH $REPO_URL
repo sync


Complete Time: $(date)
Build Host: $(hostname)

---
Team of $DEV_TEAM
EOF
}

send_success_notification() {
  echo "generating success notification email"
  generate_success_notification_email | /usr/sbin/sendmail -t $build_maintainer
}

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
        MANIFEST_DIR=$(dirname $4)
        #inherit branch
        INHERIT_BRANCH=$(dir_to_branch $MANIFEST_DIR)
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
case "$7" in
    "-e") USEREMAIL=$8
          echo "$8"
          ;;
    *) echo "wrong parameter $7"; exit 1 ;;
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
echo Copy: $MANIFEST_XML
cp $MANIFEST_XML $MANIFEST_NAME

echo $SCRIPT_PATH

# Fetch code from Developer Server with mrvl-ics branch
#$SCRIPT_PATH/fetchcode.py -u $SRC_URL -b $MANIFEST_BRANCH $REFERENCE_URL $REPO_URL
$SCRIPT_PATH/fetchcode.py -u $SRC_URL -b $INHERIT_BRANCH $REFERENCE_URL $REPO_URL
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

#Clean the shallow
echo "clean shallow of git tree"
FILES=$(find .repo/ -name "shallow")
for i in $FILES;do
    rm $i
done

#Usage: rls_branch.sh <create|delete> <release-branch-name> <unique|multiple> [<actual-run>] [<project> ...]
$SCRIPT_PATH/rls_branch.sh create $MANIFEST_BRANCH multiple $RUN_TYPE
RET=$?
if [ $RET -ne 0 ]; then
    echo "create branch failed"
    echo "exit value:" $RET
    exit 1
fi

#create_aabs_branch
if [ $RUN_TYPE == "actual-run" ]; then
    git push origin $(cat $MANIFEST_DIR/abs.commit):refs/heads/$MANIFEST_BRANCH
    RET=$?
    if [ $RET -ne 0 ]; then
        echo "failed to create aabs branch"
        echo "exit value:" $RET
        exit 1
    else
        echo ">PASS< ALL success"
        send_success_notification
        exit 0
    fi
fi
