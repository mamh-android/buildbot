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
folder_name=$1
choose=`echo ${folder_name} | grep honeycomb`
if [ -n "${choose}" ];then
REPO_DIR="ssh://partner.source.android.com:29418/platform/manifest -b honeycomb-mr2-release"
GIT_LOCAL_MIRROR=/mnt/mirror/restricted/
else
REPO_DIR="git://android.googlesource.com/platform/manifest -b master"
GIT_LOCAL_MIRROR=/mnt/mirror/default/
fi
autobuild_dir=/autobuild/android/$2/$1/src
#autobuild_dir=$HOME/share/for_MyWindows/autobuild/$1
android_dir=$test_dir/android_source
marvell_dir=$test_dir/marvell_patch
droidall_dir=$test_dir/droidall_source

mkdir $test_dir
cd $test_dir
mkdir $android_dir
mkdir $marvell_dir
mkdir $droidall_dir

echo "Copy marvell source code and patch from autobuild server..."
cp $autobuild_dir/android_patches.tgz $autobuild_dir/android_src.tgz $autobuild_dir/kernel_patches.tgz $autobuild_dir/kernel_src.tgz \
   $autobuild_dir/obm_src.tgz $autobuild_dir/uboot_src.tgz $autobuild_dir/uboot_patches.tgz \
   $autobuild_dir/marvell_manifest.xml $autobuild_dir/setup_android.sh $marvell_dir &&
cp $autobuild_dir/droid_all_src.tgz $droidall_dir
check_result

echo "Download the android initial code base..."
cd $android_dir
echo test | repo init -u ${REPO_DIR}
check_result

echo "Switch the code base specified by marvell..."
cp $marvell_dir/marvell_manifest.xml .repo/manifests/
echo test | repo init -m marvell_manifest.xml --reference ${GIT_LOCAL_MIRROR}
repo sync
check_result

echo "Apply the marvell patches..."
cd $marvell_dir
chmod a+x ./setup_android.sh
./setup_android.sh $android_dir
check_result

echo "Compare with the droid all package..."
cd $test_dir
tar xzvf $droidall_dir/droid_all_src.tgz -C $droidall_dir
find $android_dir -type l | xargs rm -f
find $droidall_dir/source -type l | xargs rm -f
diff -X $root_dir/exclude.pats -urN $android_dir $droidall_dir/source
if [ $? -eq 0 ]; then
  echo "Test passed!"
else
  echo "Test failed!"
fi
rm -fr /home/buildfarm/buildbot_script/buildbot/${folder_name}
