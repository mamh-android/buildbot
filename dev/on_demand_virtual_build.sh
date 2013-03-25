#!/bin/bash
#
# Need environment variables:
#       SYNC_GIT_WORKING_DIR:   working directory
#       GERRIT_SERVER:          gerrit target server
#       GERRIT_ADMIN:           administrator account of gerrit server
#       REFERENCE_URL:          url of repo reference
#       SRC_URL:                manifest path in source server
#       REPO_URL:               repo url

# Command usage:
#test_setup_code_via_manifest_and_gerrit_patchsetid.sh -m <manifest xml> -b <manifest branch> -g <gerrit patchsetID list>
#gerrit patchsetID list must be an array of first-order, such as A="001 002 003 004 005"

export SYNC_GIT_WORKING_DIR=${SYNC_GIT_WORKING_DIR:-$(pwd)/odvb_work}
export GERRIT_SERVER=${GERRIT_SERVER:-http://shgit.marvell.com}
export GERRIT_ADMIN=${GERRIT_MNAME:-buildfarm}
export REFERENCE_URL=${REFERENCE_URL:-"--reference=/mnt/mirror/default"}
export SRC_URL=${SRC_URL:-ssh://shgit.marvell.com/git/android/platform/manifest.git}
export REPO_URL=${REPO_URL:-"--repo-url=ssh://shgit.marvell.com/git/android/tools/repo"}

#script path
SCRIPT_PATH=`pwd`/core

case "$1" in
        "-p") GERRIT_PATCH=$2 ;;
        *) echo "wrong parameter $1"; exit 1 ;;
esac
case "$3" in
        "-m") MANIFEST_XML=$4
                if [ -f $MANIFEST_XML ]; then
                        echo "$MANIFEST_XML exists"
                        MANIFEST_XML=${MANIFEST_XML##*/}
                else
                        echo "$4 doesn't exist"
                        exit 1
                fi
                ;;
        *) echo "wrong parameter $3"; exit 1 ;;
esac
case "$5" in
        "-b") MANIFEST_BRANCH=$6 ;;
        *) echo "wrong parameter $5"; exit 1 ;;
esac
case "$6" in
        "-d") DEST_DIR=/autobuild/odvb/$7 ;;
        *) echo "wrong parameter $8"; exit 1 ;;
esac

# Clean the working directory
#rm -fr $SYNC_GIT_WORKING_DIR

# Create working diretory
#mkdir -p $SYNC_GIT_WORKING_DIR
#if [ $? -ne 0 ]; then
#        echo "failed to create directory " $SYNC_GIT_WORKING_DIR
#        exit 1
#fi

cd $SYNC_GIT_WORKING_DIR
if [ $? -ne 0 ]; then
        echo "failed to enter " $SYNC_GIT_WORKING_DIR
        exit 1
fi

# Copy manifest xml into current directory
echo $4
echo MANIFEST = $MANIFEST_XML
cp $4 $MANIFEST_XML

echo $SCRIPT_PATH

# Fetch code from Developer Server with mrvl-ics branch
$SCRIPT_PATH/fetchcode.py -u $SRC_URL -b $MANIFEST_BRANCH $REFERENCE_URL $REPO_URL
RET=$?
if [ $RET -ne 0 ]; then
        echo "failed on fetching code from manifest branch"
        echo "exit value:" $RET
        exit 1
fi

# Fetch code from Developer Server with manifest xml
$SCRIPT_PATH/fetchcode.py -u $SRC_URL -m $MANIFEST_XML $REFERENCE_URL $REPO_URL
RET=$?
if [ $RET -ne 0 ]; then
        echo "failed on fetching code from manifest xml"
        echo "exit value:" $RET
        exit 1
fi

$SCRIPT_PATH/gerrit_pick_patch.py -p $GERRIT_PATCH --showonly
RET=$?
if [ $RET -ne 0 ]; then
        echo "failed on cherry-pick the patches by gerrit patchSetID list"
        echo "exit value:" $RET
        exit 1
fi

ids=$MANIFEST_BRANCH
echo Build Branch: $ids
rm -f /home/buildfarm/buildbot_script/args.log
cd ~/aabs
var_0=`echo ${ids%%_*}`
if [ ! "${var_0}" == "rls" ]; then
  platform=`echo ${ids%%_*}`
  product=`echo ${ids#*_}`
  last_build="/autobuild/android/${platform}/LAST_BUILD.${platform}_${product}"
  target=${platform}-${product}
  echo "platform $platform" | tee -a /home/buildfarm/buildbot_script/args.log
  echo "product $product" | tee -a /home/buildfarm/buildbot_script/args.log
  echo "last_build $last_build" | tee -a /home/buildfarm/buildbot_script/args.log
  echo $target
else
  var_1=`echo ${ids#*_}`
  platform=`echo ${var_1%%_*}`
  echo "platform $platform" | tee -a /home/buildfarm/buildbot_script/args.log
  last=`echo ${var_1#*_}`
  product=`echo ${last%%_*}`
  echo "product $product" | tee -a /home/buildfarm/buildbot_script/args.log
  last=`echo ${last#*_}`
  if [ "$product" = "${last}" ]; then
    target="$platform-$product"
    last_build="/autobuild/android/${platform}/LAST_BUILD.${platform}-${product}"
  else
    echo "last $last" | tee -a /home/buildfarm/buildbot_script/args.log
    target="$platform-$product:$last"
    last_build="/autobuild/android/${platform}/LAST_BUILD.rls_${platform}_${product}_${last}"
  fi
  echo "last_build $last_build" | tee -a /home/buildfarm/buildbot_script/args.log
  echo $target
fi

# export ABS_SOURCE_DIR and ABS_PUBLISH_DIR to trigger a on demand virtual build
export ABS_SOURCE_DIR=$SYNC_GIT_WORKING_DIR
export ABS_PUBLISH_DIR=$DEST_DIR

tools/build_platforms.sh ${target} | tee -a log.txt
result=`grep ">PASS<" log.txt`
if [ -n "$result" ]; then
  nobuild=`grep ">No build<" log.txt`
  if [ -n "$nobuild" ]; then
    rm -f log.txt
    echo "no build"
    exit 255
  else
    echo "success"
    rm -f log.txt
    exit 0
  fi
else
  rm -f log.txt
  exit 1
  echo "failure"
fi
