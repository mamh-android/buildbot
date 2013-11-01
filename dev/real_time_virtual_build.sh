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
#test_setup_code_via_manifest_and_gerrit_patchsetid.sh -b <manifest branch>

export SYNC_GIT_WORKING_DIR=${SYNC_GIT_WORKING_DIR:-~/workspace/aabs/rtvb_work}
export GERRIT_SERVER=${GERRIT_SERVER:-http://shgit.marvell.com}
export GERRIT_ADMIN=${GERRIT_ADMIN:-buildfarm}
export REFERENCE_URL=${REFERENCE_URL:-"--reference=/mnt/mirror/default"}
export SRC_URL=${SRC_URL:-ssh://shgit.marvell.com/git/android/platform/manifest.git}
export REPO_URL=${REPO_URL:-"--repo-url=ssh://shgit.marvell.com/git/android/tools/repo"}

#script path
SCRIPT_PATH=`pwd`/core

# Internal variable
GERRIT_CSV=gerrit_review.csv
BRANCH_DICT=.branch.pck
REVISION_DICT=.revision.pck
CPATH_DICT=.path.pck
COUNTER_FAILURE=0

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
#                        exit 1
                fi
                ;;
        *) echo "wrong parameter $3"; exit 1 ;;
esac
case "$5" in
        "-b") MANIFEST_BRANCH=$6
              echo "MANIFEST_BRANCH= $6"
            ;;
        *) echo "wrong parameter $5"; exit 1 ;;
esac
case "$7" in
        "-d") DEST_DIR=~/workspace/aabs/rtvb/$8 ;;
        *) echo "wrong parameter $7"; exit 1 ;;
esac
case "$9" in
        "-v") ids_10=${10}
                if [ "$ids_10" != "" -a "$ids_10" != "None" ]; then
                  echo "PLATFORM_ANDROID_VARIANT= $ids_10"
                  export PLATFORM_ANDROID_VARIANT=$ids_10
                  export ABS_FORCE_BUILD="ture"
                fi
                ;;
        *) echo "wrong parameter $9"; exit 1 ;;
esac
case "${11}" in
        "-de") ids_12=${12}
                if [ "$ids_12" != "" -a "$ids_12" != "None" -a "$ids_12" != "AABS_Default" ]; then
                  echo "ABS_BUILD_DEVICES= $ids_12"
                  export ABS_BUILD_DEVICES=$ids_12
                  export ABS_FORCE_BUILD="ture"
                fi
                ;;
        *) echo "wrong parameter ${11}"; exit 1 ;;
esac

aabs_build()
{
ids=$MANIFEST_BRANCH
echo "Build Branch: $ids"
#rm -f /home/buildfarm/buildbot_script/args.log
var_0=`echo ${ids%%_*}`
if [ ! "${var_0}" == "rls" ]; then
  target=$ids
  echo "targer $target" #| tee -a /home/buildfarm/buildbot_script/args.log
else
  var_1=`echo ${ids#*_}`
  platform=`echo ${var_1%%_*}`
  echo "platform $platform" #| tee -a /home/buildfarm/buildbot_script/args.log
  last=`echo ${var_1#*_}`
  product=`echo ${last%%_*}`
  echo "product $product" #| tee -a /home/buildfarm/buildbot_script/args.log
  last=`echo ${last#*_}`
  if [ "$product" = "${last}" ]; then
    target="$platform-$product"
    last_build="/autobuild/android/${platform}/LAST_BUILD.${platform}-${product}"
  else
    echo "last $last" #| tee -a /home/buildfarm/buildbot_script/args.log
    target="$platform-$product:$last"
    last_build="/autobuild/android/${platform}/LAST_BUILD.rls_${platform}_${product}_${last}"
  fi
  echo "last_build $last_build" #| tee -a /home/buildfarm/buildbot_script/args.log
  echo $target
fi

# export ABS_SOURCE_DIR and ABS_PUBLISH_DIR to trigger a real time virtual build
export ABS_REAL_TIME_VIRTUAL_BUILD=true
export ABS_SOURCE_DIR=$SYNC_GIT_WORKING_DIR
export ABS_PUBLISH_DIR=$DEST_DIR

cd ~/workspace/aabs
tools/build_platforms.sh ${target} | tee -a log.txt
result=`grep ">PASS<" log.txt`
if [ -n "$result" ]; then
  echo "success"
  rm -f log.txt
  break
#  exit 0
else
  echo "failure"
  rm -f log.txt
  COUNTER_FAILURE=$((COUNTER_FAILURE+1))
  if [ $COUNTER_FAILURE -gt 4 ]; then
    echo build failed 5 times
    exit 1
  fi
fi
}

build_with_gerritpatches()
{
cd $SYNC_GIT_WORKING_DIR

# Output project name and branch name into .name.pck
$SCRIPT_PATH/getname.py -o $BRANCH_DICT
RET=$?
if [ $RET -ne 0 ]; then
        echo "failed on outputing branch name into dictionary file"
        echo "exit value:" $RET
        exit 1
fi

# Output project name and client path into .path.pck
$SCRIPT_PATH/getname.py -p -o $CPATH_DICT
RET=$?
if [ $RET -ne 0 ]; then
        echo "failed on outputing client path into dictionary file"
        echo "exit value:" $RET
        exit 1
fi

# Create gerrit patch csv
$SCRIPT_PATH/create_csv.py -o $GERRIT_CSV -b $BRANCH_DICT -p $CPATH_DICT --review=R+1
RET=$?
if [ $RET -ne 0 ]; then
        echo "failed on outputing client path into dictionary file"
        echo "exit value:" $RET
        exit 1
fi

# Setup code via gerrit patch csv
$SCRIPT_PATH/gerrit_pick_patch.py -t $GERRIT_CSV
RET=$?
if [ $RET -ne 0 ]; then
        echo "failed on outputing client path into dictionary file"
        echo "exit value:" $RET
        exit 1
fi
}

return_change_rev_list()
{
gerrit_list=$(echo $(repo forall -c ~/workspace/buildfarm/buildbot/core/rtvb_patches.sh) | sed 's/ /,/g')
return $gerrit_list
}

# Clean the working directory
#rm -fr $SYNC_GIT_WORKING_DIR

# Create working diretory
mkdir -p $SYNC_GIT_WORKING_DIR
if [ $? -ne 0 ]; then
        echo "failed to create directory " $SYNC_GIT_WORKING_DIR
        exit 1
fi

cd $SYNC_GIT_WORKING_DIR
echo $SYNC_GIT_WORKING_DIR
if [ $? -ne 0 ]; then
        echo "failed to enter " $SYNC_GIT_WORKING_DIR
        exit 1
fi

# Fetch code from Developer Server with specific branch
#$SCRIPT_PATH/fetchcode.py -u $SRC_URL -b $MANIFEST_BRANCH $REFERENCE_URL $REPO_URL
#$SCRIPT_PATH/fetchcode.py -u $SRC_URL -b $MANIFEST_BRANCH $REPO_URL
#RET=$?
#if [ $RET -ne 0 ]; then
#  echo "failed on fetching code from manifest branch"
#  echo "exit value:" $RET
#  exit 1
#fi

repo manifest -r -o first_manifest.xml

while [ 1 ]; do
  break
  cd $SYNC_GIT_WORKING_DIR
  repo sync
  repo manifest -r -o last_manifest.xml
  if [ -n "$(diff first_manifest.xml last_manifest.xml)" ]; then
  aabs_build
  else
  sleep 600
  fi
done

