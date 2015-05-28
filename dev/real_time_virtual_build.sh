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
#./dev/real_time_virtual_build.sh -b pxa988-jb4.3 -v userdebug -de pxa1L88dkb_def:pxa1L88dkb

export SYNC_GIT_WORKING_DIR=${SYNC_GIT_WORKING_DIR:-~/aabs/rtvb_work}
export GERRIT_SERVER=${GERRIT_SERVER:-shgit.marvell.com}
export GERRIT_ADMIN=${GERRIT_ADMIN:-buildfarm}
export REFERENCE_URL=${REFERENCE_URL:-"--reference=/mnt/mirror/default"}
export SRC_URL=${SRC_URL:-ssh://shgit.marvell.com/git/android/platform/manifest.git}
export REPO_URL=${REPO_URL:-"--repo-url=ssh://shgit.marvell.com/git/android/tools/repo"}


#script path
SCRIPT_PATH=`pwd`/core

# Internal variable
GERRIT_CSV=.gerrit_review_rtvb
BRANCH_DICT=.branch.pck
REVISION_DICT=.revision.pck
CPATH_DICT=.path.pck
COUNTER_FAILURE=0
MAKE_JOBS=8
START_LAST_RUN="false"

BUILD_TYPE="[RTVB]"
DEST_DIR=~/aabs/rtvb_out/
BUILD_RESULT=""
BUILD_RESULT="success"
LIST_BUILD_RESULT_S=.gerrit.success.list
LIST_BUILD_RESULT_F=.gerrit.failure.list
LAST_RESULT_LIST_BACKUP=/autobuild/rtvb/last_result_list_backup/
FILE_SERVER_HTTP="http://sh-fs04"
RTVB_MAKE_LOG_BACKUP=/autobuild/rtvb/changeid_make_logs/


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

echo "ANDROID_SOURCE_DIR: $ABS_SOURCE_DIR"
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
$SCRIPT_PATH/create_rtvb_patch_list.py -o $GERRIT_CSV -b $BRANCH_DICT -p $CPATH_DICT
RET=$?
if [ $RET -ne 0 ]; then
        echo "failed on creating $GERRIT_CSV"
        echo "exit value:" $RET
        exit 1
fi
}

pick_patch_from_csv_build()
{
#change_id=$(awk -F"," ' { print $15; exit } ' $GERRIT_CSV)
#patch_set_id=$(awk -F"," ' { print $15; exit } ' $GERRIT_CSV)
#commit_id=$(ssh -p 29418 $GERRIT_ADMIN@$GERRIT_SERVER gerrit gsql -c "select\ revision\ from\ patch_sets\ WHERE\ change_id=\'$change_id\'\ AND\ patch_set_id=\'$patch_set_id\'" | head -3 | tail -1)
#STD_LOG=$RTVB_MAKE_LOG_BACKUP$commit_id
cd $SYNC_GIT_WORKING_DIR
STD_LOG=.rtvb.build.log
$SCRIPT_PATH/fetchcode.py -u $SRC_URL -m first_manifest.xml $REFERENCE_URL $REPO_URL | tee -a $STD_LOG
RET=$?
if [ $RET -ne 0 ]; then
        echo "failed on fetching code from manifest xml"
        echo "exit value:" $RET
        exit 1
fi
if [ -s $GERRIT_CSV ]; then
    # Setup code via gerrit patch csv
    echo "$BUILD_TYPE [$(get_date)] Pick one patch from csv for RTVB" | tee -a $STD_LOG
    $SCRIPT_PATH/gerrit_pick_patch_new.py -t $GERRIT_CSV | tee -a $STD_LOG
    RET=$?
    if [ $RET -ne 0 ]; then
        echo "failed on picking patch from $GERRIT_CSV" | tee -a $STD_LOG
        echo "exit value:" $RET
        exit 1
    fi
    . build/envsetup.sh
    lunch ${ABS_BUILD_DEVICES%%:*}-$PLATFORM_ANDROID_VARIANT
    make -j$MAKE_JOBS | tee -a $STD_LOG
    RET=$?
    if [ $RET -eq 0 ]; then
        echo "$BUILD_TYPE [$(get_date)] success, exit value $RET" | tee -a $STD_LOG
        BUILD_RESULT="success"
    else
        echo "$BUILD_TYPE [$(get_date)] failure, exit value $RET" | tee -a $STD_LOG
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
if [ $START_LAST_RUN == "false" ]; then
rm -rf $SYNC_GIT_WORKING_DIR
rm -rf $DEST_DIR
fi

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
if [ $START_LAST_RUN == "false" ]; then
  $SCRIPT_PATH/fetchcode.py -u $SRC_URL -b $MANIFEST_BRANCH $REFERENCE_URL $REPO_URL
fi
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
    if [ $START_LAST_RUN == "false" ]; then
      aabs_build
    fi
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
  if [ $COUNTER_FAILURE -gt 4 ]; then
    echo "$BUILD_TYPE build failed 5 times"
    exit 1
  fi
  echo "$BUILD_TYPE COUNTER_FAILURE:($COUNTER_FAILURE), Resync the code"
  repo sync
  repo manifest -r -o last_manifest.xml
done

#Setup csv for rtvb
if [ $START_LAST_RUN == "false" ]; then
  setup_gerritpatches_csv_for_rtvb
fi

return_make_jobs

#Main loop for picking and building
while [ -s $GERRIT_CSV ]; do
pick_patch_from_csv_build
if [ $BUILD_RESULT == "success" ]; then
    echo "$BUILD_TYPE [$(get_date)] build success, create $LIST_BUILD_RESULT_S"
    echo $(repo forall -c $SCRIPT_PATH/rtvb_patches.sh) | sed 's/ /\n/g' >> $LIST_BUILD_RESULT_S
    rm $STD_LOG
else
    echo "$BUILD_TYPE [$(get_date)] build failed, create $LIST_BUILD_RESULT_F"
    tmp_a=$(echo $(repo forall -c $SCRIPT_PATH/rtvb_patches.sh) | sed 's/ /:/g')
    echo ${tmp_a%%:*} >> $LIST_BUILD_RESULT_F
    mv $STD_LOG $RTVB_MAKE_LOG_BACKUP${tmp_a%%:*}.failure.log
fi
done

#Updating gerrit patch status
if [ -s $LIST_BUILD_RESULT_F ]; then
    echo "$BUILD_TYPE [$(get_date)] Updating failure gerrit patch"
    #ingore the failed patches was failed last time
    new_failed_list=$(grep -v -f $LAST_RESULT_LIST_BACKUP$LIST_BUILD_RESULT_F $LIST_BUILD_RESULT_F)
    for GERRIT_PATCH in $new_failed_list; do
        #$SCRIPT_PATH/gerrit_review_update.py -p $GERRIT_PATCH -m $MANIFEST_BRANCH-${ABS_BUILD_DEVICES%%:*}-$PLATFORM_ANDROID_VARIANT -r "failure" -d "$RTVB_MAKE_LOG_BACKUP$GERRIT_PATCH"
        $SCRIPT_PATH/gerrit_review_update.py -p $GERRIT_PATCH -m $MANIFEST_BRANCH-${ABS_BUILD_DEVICES%%:*}-$PLATFORM_ANDROID_VARIANT -r "failure" -d "$FILE_SERVER_HTTP$RTVB_MAKE_LOG_BACKUP$GERRIT_PATCH.failure.log"
    done
fi

if [ -s $LIST_BUILD_RESULT_S ]; then
    echo "$BUILD_TYPE [$(get_date)] Updating success gerrit patch"
    for GERRIT_PATCH in `sort -k2n $LIST_BUILD_RESULT_S | uniq`; do
        $SCRIPT_PATH/gerrit_review_update.py -p $GERRIT_PATCH -m $MANIFEST_BRANCH-${ABS_BUILD_DEVICES%%:*}-$PLATFORM_ANDROID_VARIANT -r "success" -d "RTVB"
    done
fi

#backup last result list to fileserver
cp $LIST_BUILD_RESULT_S $LAST_RESULT_LIST_BACKUP
cp $LIST_BUILD_RESULT_F $LAST_RESULT_LIST_BACKUP

echo "$BUILD_TYPE [$(get_date)] process is done"
