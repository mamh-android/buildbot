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

export SYNC_GIT_WORKING_DIR=${SYNC_GIT_WORKING_DIR:-~/aabs/rtvb_work}
export GERRIT_SERVER=${GERRIT_SERVER:-http://shgit.marvell.com}
export GERRIT_ADMIN=${GERRIT_ADMIN:-buildfarm}
export REFERENCE_URL=${REFERENCE_URL:-"--reference=/mnt/mirror/default"}
export SRC_URL=${SRC_URL:-ssh://shgit.marvell.com/git/android/platform/manifest.git}
export REPO_URL=${REPO_URL:-"--repo-url=ssh://shgit.marvell.com/git/android/tools/repo"}

#script path
SCRIPT_PATH=`pwd`/core

# Internal variable
GERRIT_CSV=gerrit_review_rtvb.csv
BRANCH_DICT=.branch.pck
REVISION_DICT=.revision.pck
CPATH_DICT=.path.pck
COUNTER_FAILURE=0
MAKE_JOBS=8

BUILD_TYPE="[RTVB]"
DEST_DIR=~/aabs/rtvb_out/
BUILD_RESULT=""
BUILD_RESULT="success"
LIST_BUILD_RESULT_S=.gerrit.success.list
LIST_BUILD_RESULT_F=.gerrit.failure.list


case "$1" in
        "-b") MANIFEST_BRANCH=$2
              echo "MANIFEST_BRANCH= $2"
            ;;
        *) echo "wrong parameter $1"; exit 1 ;;
esac
case "$3" in
        "-v") ids_4=${4}
                if [ "$ids_4" != "" -a "$ids_4" != "None" ]; then
                  echo "PLATFORM_ANDROID_VARIANT= $ids_4"
                  export PLATFORM_ANDROID_VARIANT=$ids_4
                  export ABS_FORCE_BUILD="ture"
                fi
                ;;
        *) echo "wrong parameter $3"; exit 1 ;;
esac
case "${5}" in
        "-de") ids_6=${6}
                if [ "$ids_6" != "" -a "$ids_6" != "None" -a "$ids_6" != "AABS_Default" ]; then
                  echo "ABS_BUILD_DEVICES= $ids_6"
                  export ABS_BUILD_DEVICES=$ids_6
                  export ABS_FORCE_BUILD="ture"
                fi
                ;;
        *) echo "wrong parameter ${5}"; exit 1 ;;
esac

get_date()
{
  echo $(date "+%Y-%m-%d %H:%M:%S")
}

return_make_jobs()
{
core_number=`cat /proc/cpuinfo | grep "cpu cores" | head -1 | awk -F: '{ print $2 }'`
ht=`cat /proc/cpuinfo | grep -w ht`
if [ -z $? ]; then
        ht=1
else
        ht=2
fi
MAKE_JOBS=$((core_number=core_number*ht*2))
echo "MAKE_JOBS: $MAKE_JOBS"
}

aabs_build()
{
ids=$MANIFEST_BRANCH
echo "Build Branch: $ids"
var_0=`echo ${ids%%_*}`
if [ ! "${var_0}" == "rls" ]; then
  target=$ids
  echo "targer $target"
else
  var_1=`echo ${ids#*_}`
  platform=`echo ${var_1%%_*}`
  echo "platform $platform"
  last=`echo ${var_1#*_}`
  product=`echo ${last%%_*}`
  echo "product $product"
  last=`echo ${last#*_}`
  if [ "$product" = "${last}" ]; then
    target="$platform-$product"
    last_build="/autobuild/android/${platform}/LAST_BUILD.${platform}-${product}"
  else
    echo "last $last"
    target="$platform-$product:$last"
    last_build="/autobuild/android/${platform}/LAST_BUILD.rls_${platform}_${product}_${last}"
  fi
  echo "last_build $last_build"
  echo $target
fi

# export ABS_SOURCE_DIR and ABS_PUBLISH_DIR to trigger a real time virtual build
export ABS_REAL_TIME_VIRTUAL_BUILD=true
export ABS_SOURCE_DIR=$SYNC_GIT_WORKING_DIR
export ABS_PUBLISH_DIR=$DEST_DIR

~/aabs/tools/build_platforms.sh ${target} | tee -a log.txt
result=`grep ">PASS<" log.txt`
if [ -n "$result" ]; then
  echo "success"
  BUILD_RESULT="success"
  rm -f log.txt
#  exit 0
else
  echo "failure"
  rm -f log.txt
  BUILD_RESULT="failure"
  COUNTER_FAILURE=$((COUNTER_FAILURE+1))
  if [ $COUNTER_FAILURE -gt 4 ]; then
    echo build failed 5 times
    exit 1
  fi
fi
}

setup_gerritpatches_csv_for_rtvb()
{
echo "$BUILD_TYPE [$(get_date)] Start setup patch csv for RTVB"
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
$SCRIPT_PATH/create_csv.py -o $GERRIT_CSV -b $BRANCH_DICT -p $CPATH_DICT --rtvb
RET=$?
if [ $RET -ne 0 ]; then
        echo "failed on creating $GERRIT_CSV"
        echo "exit value:" $RET
        exit 1
fi
}

pick_patch_from_csv_build()
{
cd $SYNC_GIT_WORKING_DIR
$SCRIPT_PATH/fetchcode.py -u $SRC_URL -m first_manifest.xml $REFERENCE_URL $REPO_URL
RET=$?
if [ $RET -ne 0 ]; then
        echo "failed on fetching code from manifest xml"
        echo "exit value:" $RET
        exit 1
fi
if [ -s $GERRIT_CSV ]; then
    # Setup code via gerrit patch csv
    echo "$BUILD_TYPE [$(get_date)] Pick one patch from csv for RTVB"
    $SCRIPT_PATH/gerrit_pick_patch.py -t $GERRIT_CSV
    RET=$?
    if [ $RET -ne 0 ]; then
        echo "failed on picking patch from $GERRIT_CSV"
        echo "exit value:" $RET
        exit 1
    fi
    . build/envsetup.sh
    lunch ${ABS_BUILD_DEVICES%%:*}-$PLATFORM_ANDROID_VARIANT
    make -j$MAKE_JOBS
    RET=$?
    if [ $RET -eq 0 ]; then
        echo "$BUILD_TYPE [$(get_date)] success, exit value $RET"
        BUILD_RESULT="success"
    else
        echo "$BUILD_TYPE [$(get_date)] failure, exit value $RET"
        BUILD_RESULT="failure"
    fi
else
    echo "$GERRIT_CSV is empty"
fi
}

return_change_rev_list()
{
cd $SYNC_GIT_WORKING_DIR
gerrit_list=$(echo $(repo forall -c $SCRIPT_PATH/rtvb_patches.sh) | sed 's/ /,/g')
}

# Clean the working directory
rm -rf $SYNC_GIT_WORKING_DIR
rm -rf $DEST_DIR

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
echo "$BUILD_TYPE [$(get_date)] sync code"
$SCRIPT_PATH/fetchcode.py -u $SRC_URL -b $MANIFEST_BRANCH $REFERENCE_URL $REPO_URL
RET=$?
if [ $RET -ne 0 ]; then
  echo "failed on fetching code from manifest branch"
  echo "exit value:" $RET
  exit 1
fi

echo "$BUILD_TYPE [$(get_date)] sync code done"

#Main loop for current code build by aabs
while [ 1 ]; do
echo "$BUILD_TYPE Start aabs build while loop"
  cd $SYNC_GIT_WORKING_DIR
  if [ -n "$(diff first_manifest.xml last_manifest.xml)" ] || [ ! -s last_manifest.xml ] || [ ! -s first_manifest.xml ]; then
    echo "$BUILD_TYPE [$(get_date)] Launch aabs build and return BUILD_RESULT"
    aabs_build
      if [ $BUILD_RESULT == "success" ]; then
        echo "$BUILD_TYPE [$(get_date)] build success exit the aabs while loop"
        repo manifest -r -o first_manifest.xml
        break
      else
        echo "$BUILD_TYPE Build failed, Sleep 600s"
        repo manifest -r -o first_manifest.xml
        sleep 600
      fi
  fi
  echo "$BUILD_TYPE Resync the code"
  repo sync
  repo manifest -r -o last_manifest.xml
done

#Setup csv for rtvb
setup_gerritpatches_csv_for_rtvb

return_make_jobs

#Main loop for picking and building
while [ -s $GERRIT_CSV ]; do
pick_patch_from_csv_build
if [ $BUILD_RESULT == "success" ]; then
    echo "$BUILD_TYPE [$(get_date)] build success, create $LIST_BUILD_RESULT_S"
    echo $(repo forall -c $SCRIPT_PATH/rtvb_patches.sh) | sed 's/ /\n/g' >> $LIST_BUILD_RESULT_S
else
    echo "$BUILD_TYPE [$(get_date)] build failed, create $LIST_BUILD_RESULT_F"
    tmp_a=$(echo $(repo forall -c $SCRIPT_PATH/rtvb_patches.sh) | sed 's/ /:/g')
    echo ${tmp_a%%:*} >> $LIST_BUILD_RESULT_F
fi
done

#Updating gerrit patch status
if [ -s $LIST_BUILD_RESULT_F ]; then
    echo "$BUILD_TYPE [$(get_date)] Updating failure gerrit patch"
    for GERRIT_PATCH in `sort -k2n $LIST_BUILD_RESULT_F | uniq`; do
        $SCRIPT_PATH/gerrit_review_update.py -p $GERRIT_PATCH -m $MANIFEST_BRANCH-${ABS_BUILD_DEVICES%%:*}-$PLATFORM_ANDROID_VARIANT -r "failure" -d "RTVB"
    done
fi

if [ -s $LIST_BUILD_RESULT_S ]; then
    echo "$BUILD_TYPE [$(get_date)] Updating success gerrit patch"
    for GERRIT_PATCH in `sort -k2n $LIST_BUILD_RESULT_S | uniq`; do
        $SCRIPT_PATH/gerrit_review_update.py -p $GERRIT_PATCH -m $MANIFEST_BRANCH-${ABS_BUILD_DEVICES%%:*}-$PLATFORM_ANDROID_VARIANT -r "success" -d "RTVB"
    done
fi

echo "$BUILD_TYPE [$(get_date)] process is done"
