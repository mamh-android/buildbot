#!/bin/sh

#upload_pub_rls.sh -t <tag name> -m <manifest xml> -b <manifest branch> --tagsrc

MANIFEST_BRANCH=rls-mrvl-android-rc1
MANIFEST_XML=manifest.xml
TAG_NAME=rls-mrvl-android-alpha1sp1
REFERENCE_URL="--reference=/mnt/mirror/default/"
REPO_URL="--repo-url=ssh://shgit.marvell.com/git/android/tools/repo"

# remote name in manifest default.xml
IN_RLS_URL=ssh://wdong1@10.38.32.104/home/wdong1/internal_android/platform/manifest.git
REMOTE_MNAME=wdong1@10.38.32.104
DEST_ROOT=/home/wdong1/publish_android/

case "$#" in
	7) case "$7" in
		"--tagsrc");; # TAG_SRC=1 ;;
		*) echo "wrong parameter $3"
	   esac ;;
	6) ;;
	*) echo "wrong parameter nubmer"; exit ;;
esac
case "$1" in
	"-t") TAG_NAME=$2 ;;
	*) echo "wrong parameter $1" ;;
esac
case "$3" in
	"-m") MANIFEST_BRANCH=$4 ;;
	*) echo "wrong parameter $3" ;;
esac
case "$5" in
	"-b") MANIFEST_BRANCH=$6 ;;
	*) echo "wrong parameter $5" ;;
esac

# Internal variable
BRANCH_DICT=.branch.pck
REVISION_DICT=.revision.pck
CPATH_DICT=.path.pck

# Fetch code from Developer Server with mrvl-ics branch
python /home/buildfarm/buildbot_script/buildbot/fetchcode.py -u $IN_RLS_URL -b $MANIFEST_BRANCH $REFERENCE_URL $REPO_URL
RET=$?
if [ $RET -ne 0 ]; then
	echo "failed on fetching code from manifest branch"
	echo "exit value:" $RET
	exit 1
fi

# Output project name and branch name into .name.pck
python /home/buildfarm/buildbot_script/buildbot/getname.py -o $BRANCH_DICT
RET=$?
if [ $RET -ne 0 ]; then
	echo "failed on outputing branch name into dictionary file"
	echo "exit value:" $RET
	exit 1
fi

# Fetch code from Developer Server with manifest xml
python /home/buildfarm/buildbot_script/buildbot/fetchcode.py -u $IN_RLS_URL -m $MANIFEST_XML $REFERENCE_URL $REPO_URL
RET=$?
if [ $RET -ne 0 ]; then
	echo "failed on fetching code from manifest xml"
	echo "exit value:" $RET
	exit 1
fi

# Output project name and revision number into .revision.pck
python /home/buildfarm/buildbot_script/buildbot/getname.py -o $REVISION_DICT
RET=$?
if [ $RET -ne 0 ]; then
	echo "failed on outputing revision number into dictionary file"
	echo $?
	exit
fi

# Compare whether different dictories are imported by manifest xml
python /home/buildfarm/buildbot_script/buildbot/comparedict.py -s $BRANCH_DICT -d $REVISION_DICT
RET=$?
if [ $RET -ne 0 ]; then
    echo "Keys in these two dictionary files are different"
    echo "exit value:" $RET
    exit 1
elif [ $RET -eq 1 ]; then
    echo "Source repository is the subset of repository that is defined in manifest.xml"
elif [ $RET -eq 2 ]; then
    echo "Repository that is defined in manifest.xml is the subset of source repository"
fi

# Output project name and client path into .path.pck
python /home/buildfarm/buildbot_script/buildbot/getname.py -p -o $CPATH_DICT
RET=$?
if [ $RET -ne 0 ]; then
	echo "failed on outputing client path into dictionary file"
	echo "exit value:" $RET
	exit 1
fi

# Compare whether different dictories are imported by manifest xml
python /home/buildfarm/buildbot_script/buildbot/comparedict.py -s $BRANCH_DICT -d $CPATH_DICT
RET=$?
if [ $RET -ne 0 ]; then
    echo "Keys in these two dictionary files are different"
    echo "exit value:" $RET
    exit 1
elif [ $RET -eq 1 ]; then
    echo "Source repository is the subset of repository that is defined in manifest.xml"
elif [ $RET -eq 2 ]; then
    echo "Repository that is defined in manifest.xml is the subset of source repository"
fi

# Apply tag on working directory
python /home/buildfarm/buildbot_script/buildbot/tag.py -i $CPATH_DICT -r $REMOTE_MNAME -t $TAG_NAME
RET=$?
if [ $RET -ne 0 ]; then
	echo "Failed to apply tag"
	echo "exit value:" $RET
	exit 1
fi

# Upload repository to dest server
python /home/buildfarm/buildbot_script/buildbot/push.py -t $TAG_NAME --dict-branch=$BRANCH_DICT --dict-path=$CPATH_DICT -d $REMOTE_MNAME -r $DEST_ROOT -b $TAG_NAME
RET=$?
if [ $RET -ne 0 ]; then
	echo "Failed to upload repository to dest server"
	echo "exit value:" $RET
	exit 1
fi

if [ ! -z $TAG_SRC ]; then
	# Upload commits to source server
	python /home/buildfarm/buildbot_script/buildbot/push.py -t $TAG_NAME --dict-branch=$BRANCH_DICT --dict-path=$CPATH_DICT --tagsrc
        RET=$?
	if [ $RET -ne 0 ]; then
		echo "Failed to upload repository to dest server"
		echo "exit value:" $RET
		exit 1
	fi
fi

# Verify revision number
python /home/buildfarm/buildbot_script/buildbot/verify.py --dict-revision=$REVISION_DICT --dict-path=$CPATH_DICT -t $TAG_NAME
RET=$?
if [ $RET -ne 0 ]; then
	echo "verification fail"
	echo "exit value:" $RET
	exit 1
fi

echo "upload finished!"
