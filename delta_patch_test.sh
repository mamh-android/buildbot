#!/bin/bash
#
#

check_result() {
  if [ $? -ne 0 ]; then
    echo
    echo
    echo "FAIL: Test is aborted. Current working dir:$(pwd)"
    echo
    exit 1
  fi
}

root_dir=$(pwd)
test_dir=$root_dir/$1
autobuild_dir=/autobuild/android/brownstone/$1
#$autobuild_dir=$HOME/temp/test/$1
android_dir=$test_dir/android_source
marvell_dir=$test_dir/marvell_patch
dpatch_dir=$test_dir/delta_patch
droidall_dir=$test_dir/droidall_source

mkdir $test_dir
cd $test_dir
mkdir $android_dir
mkdir $marvell_dir
mkdir $dpatch_dir
mkdir $droidall_dir

echo "Copy marvell delta patch and droidall source from autobuild server..."
cp $autobuild_dir/delta_patches.tgz $dpatch_dir &&
cp $autobuild_dir/droid_all_src.tgz $droidall_dir
check_result
tar xzvf $dpatch_dir/delta_patches.tgz -C $dpatch_dir
tar xzvf $droidall_dir/droid_all_src.tgz -C $droidall_dir

echo "Copy marvell source code and patch of last milestone from autobuild server..."
autobuild_dir_last=`grep "[:blank:]*Package:" $autobuild_dir/delta_patches.base | awk 'BEGIN {FS=":"} {print $2}'`
cp $autobuild_dir_last/android_patches.tgz $autobuild_dir_last/android_src.tgz $autobuild_dir_last/kernel_patches.tgz $autobuild_dir_last/kernel_src.tgz \
   $autobuild_dir_last/obm_src.tgz $autobuild_dir_last/uboot_src.tgz $autobuild_dir_last/uboot_patches.tgz \
   $autobuild_dir_last/marvell_manifest.xml $autobuild_dir_last/setup_android.sh $marvell_dir
check_result

echo "Download the android initial code base..."
cd $android_dir
echo test | repo init -u ssh://partner.source.android.com:29418/platform/manifest -b honeycomb-mr2-release
repo sync
check_result

echo "Switch the code base specified by marvell..."
cp $marvell_dir/marvell_manifest.xml .repo/manifests/
echo test | repo init -m marvell_manifest.xml
repo sync
check_result

echo "Apply the marvell patches..."
cd $marvell_dir
chmod a+x ./setup_android.sh
./setup_android.sh $android_dir
check_result

echo "Apply the delta patches..."
cd $dpatch_dir
android_patch_list=$(find . -type f -name "*.patch" | sort) &&
for android_patch in $android_patch_list; do
  android_project=$(dirname $android_patch)
  echo "    applying patches on $android_project ..."
  cd $android_dir/$android_project 
  git am $dpatch_dir/$android_patch	
  check_result
done

if [ -e $dpatch_dir/PURGED_PROJECTS ]; then
  cat $dpatch_dir/PURGED_PROJECTS | while read purged_prj
  do
    purged_prj=${purged_prj##*:}
    echo "    removing newly purged project:$purged_prj ..."
    rm -rf $android_dir/$purged_prj
    check_result
  done
fi

cd $dpatch_dir
newly_added_project=$(find . -type f -name mrvl_base_src.tgz) &&
for added_prj in $newly_added_project; do
  echo "    umcompressing newly added project:$added_prj ..."
  android_project=$(dirname $added_prj)
  mkdir -p $android_dir/$android_project
  tar xzvf $added_prj -C $android_dir/$android_project
  cd $android_dir/$android_project &&
  git init &&
  git add ./. -f &&
  git commit -s -m "init code from marvell"
  check_result
  cd -
done

echo "Compare with the droid all package..."
cd $test_dir
find $android_dir -type l | xargs rm -f
find $droidall_dir/source -type l | xargs rm -f
diff -X $root_dir/exclude.pats -urN $android_dir $droidall_dir/source
if [ $? -eq 0 ]; then
  echo "Test passed!"
else
  echo "Test failed!"
  exit 1
fi
