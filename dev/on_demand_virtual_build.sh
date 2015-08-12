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
function printcolor(){
    printf "\033[1;33m[odvb]\033[0m\033[1;31m$1\n\033[0m"
}

export SYNC_GIT_WORKING_DIR=${SYNC_GIT_WORKING_DIR:-~/aabs/odvb_work}
export GERRIT_SERVER=${GERRIT_SERVER:-http://shgit.marvell.com}
export GERRIT_ADMIN=${GERRIT_ADMIN:-buildfarm}
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
                        MANIFEST_DIR=$(dirname $4)
                        MANIFEST_XML=${MANIFEST_XML##*/}
                elif [ "${MANIFEST_XML}" == "None" ]; then
                        echo "MANIFEST_XML is $MANIFEST_XML"
                        MANIFEST_DIR=$MANIFEST_XML
                        MANIFEST_XML=$MANIFEST_XML
                else
                        echo "$4 doesn't exist"
                        exit 1
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
        "-d") DEST_DIR=/miscbuild/odvb/$8 ;;
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

if [ "$MANIFEST_BRANCH" = "pxa1936-mpre" ];then
export SRC_URL=ssh://shgit.marvell.com/git/lpre/platform/manifest.git
export REFERENCE_URL="--reference=/home/buildfarm/aabs/jenkins/mirror/mpre"
echo "=mpre branch==$SRC_URL = $REFERENCE_URL"
fi

# Clean the working directory
printcolor "clean the working drectory: $SYNC_GIT_WORKING_DIR"
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
printcolor "copy manifest: $4"
cp $4 $MANIFEST_XML

printcolor $SCRIPT_PATH

# Fetch code from Developer Server with mrvl-ics branch
if [ -f $MANIFEST_DIR/manifest.commit ]; then
    MANIFEST_C=$(cat $MANIFEST_DIR/manifest.commit)
    $SCRIPT_PATH/fetchcode.py -u $SRC_URL -b $MANIFEST_C $REFERENCE_URL $REPO_URL
else
    $SCRIPT_PATH/fetchcode.py -u $SRC_URL -b $MANIFEST_BRANCH $REFERENCE_URL $REPO_URL
fi
RET=$?
if [ $RET -ne 0 ]; then
        echo "failed on fetching code from manifest branch"
        echo "exit value:" $RET
        exit 1
fi

# Fetch code from Developer Server with manifest xml
printcolor "fetch code: "
if [ -f $MANIFEST_XML ];then
    $SCRIPT_PATH/fetchcode.py -u $SRC_URL -m $MANIFEST_XML $REFERENCE_URL $REPO_URL
    # Reset hard aabs
    cd ~/aabs
    git fetch origin
    git reset --hard $(cat $MANIFEST_DIR/abs.commit)
else
    echo "Buildcode with None Specific manifest.xml"
    # Reset aabs
    if [ ! ${MANIFEST_BRANCH%%_*} == "rls" ]; then
        cd ~/aabs
        git fetch origin
        git reset --hard origin/master
    else
        cd ~/aabs
        git fetch origin
        git reset --hard origin/$MANIFEST_BRANCH
    fi
fi
RET=$?
if [ $RET -ne 0 ]; then
        echo "failed on fetching code from manifest xml"
        echo "exit value:" $RET
        exit 1
fi

# Cherry-pick the listed patched from gerrit to $SYNC_GIT_WORKING_DIR
cd $SYNC_GIT_WORKING_DIR
if [ "$GERRIT_PATCH" != "" -a "$GERRIT_PATCH" != "None" ]; then
  $SCRIPT_PATH/gerrit_pick_patch.py -p $GERRIT_PATCH
  RET=$?
  if [ $RET -ne 0 ]; then
    echo "failed on cherry-pick the patches by gerrit patchSetID list"
    echo "exit value:" $RET
    exit 1
  fi
else
  echo "Build with a saved manifest $4, without any gerrit patches."
fi

ids=$MANIFEST_BRANCH
echo "Build Branch: $ids"
rm -f /home/buildfarm/buildbot_script/args.log
cd ~/aabs
var_0=`echo ${ids%%_*}`
if [ ! "${var_0}" == "rls" ]; then
  target=$ids
  echo "targer $target" | tee -a /home/buildfarm/buildbot_script/args.log
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

echo "ANDROID_SOURCE_DIR: $ABS_SOURCE_DIR"
tools/build_platforms.sh ${target} no-checkout | tee -a log.txt
result=`grep ">PASS<" log.txt`
if [ -n "$result" ]; then
  echo "success"
  rm -f log.txt
  exit 0
else
  rm -f log.txt
  exit 1
  echo "failure"
fi
