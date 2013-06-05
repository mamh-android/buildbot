#!/bin/sh
#
# Need environment variables:
#	SYNC_GIT_WORKING_DIR:	working directory
#	REMOTE_SERVER:		remote target server 
#	REMOTE_MNAME:		remote target server name in manifest file
#	DEST_ROOT:		installation path of remote server
#	REFERENCE_URL:		url of repo reference
#	SRC_URL:		manifest path in source server
#	REPO_URL:		repo url

# Command usage:
#upload_in_rls.sh -t <tag name> -m <manifest xml> -b <manifest branch> --tagsrc

export SYNC_GIT_WORKING_DIR=${SYNC_GIT_WORKING_DIR:-$(pwd)/in_work}
export REMOTE_SERVER=${REMOTE_SERVER:-github-i.marvell.com}
export REMOTE_MNAME=${REMOTE_MNAME:-mars_in}
export DEST_ROOT=${DEST_ROOT:-/mobile/android/default/}
export REFERENCE_URL=${REFERENCE_URL:-"--reference=/mnt/mirror/default"}
export REPO_URL=${REPO_URL:-"--repo-url=ssh://shgit.marvell.com/git/android/tools/repo"}

export SRC_URL=${SRC_URL:-ssh://shgit.marvell.com/git/android/platform/manifest.git}

#script path
SCRIPT_PATH=`pwd`/core

case "$#" in
	7) case "$7" in
		"--tagsrc") TAG_SRC=1 ;;
		*) echo "wrong parameter $3"; exit 1 ;;
	   esac ;;
	6) ;;
	*) echo "wrong parameter nubmer"; exit 1 ;;
esac
case "$1" in
	"-t") TAG_NAME=$2 ;;
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

# Internal variable
BRANCH_DICT=.branch.pck
REVISION_DICT=.revision.pck
CPATH_DICT=.path.pck

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
echo $MANIFEST_XML
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

# Output project name and branch name into .name.pck
$SCRIPT_PATH/getname.py -o $BRANCH_DICT
RET=$?
if [ $RET -ne 0 ]; then
	echo "failed on outputing branch name into dictionary file"
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

# Output project name and revision number into .revision.pck
$SCRIPT_PATH/getname.py -o $REVISION_DICT
RET=$?
if [ $RET -ne 0 ]; then
	echo "failed on outputing revision number into dictionary file"
	echo "exit value:" $RET
	exit 1
fi

# Compare whether different dictories are imported by manifest xml
# $BRANCH_DICT is the parameter source
# $REVISION_DICT is the parameter destination
$SCRIPT_PATH/comparedict.py -s $BRANCH_DICT -d $REVISION_DICT
RET=$?
if [ $RET -lt 0 ]; then
	echo "Keys in these two dictionary files are different"
	echo "exit value:" $RET
	exit 1
elif [ $RET -eq 1 ]; then
	echo "Source repository is the subset of repository that is defined in manifest.xml"
elif [ $RET -eq 2 ]; then
	echo "Repository that is defined in manifest.xml is the subset of source repository"
fi

# Output project name and client path into .path.pck
$SCRIPT_PATH/getname.py -p -o $CPATH_DICT
RET=$?
if [ $RET -ne 0 ]; then
	echo "failed on outputing client path into dictionary file"
	echo "exit value:" $RET
	exit 1
fi

# Compare whether different dictories are imported by manifest xml
# $BRANCH_DICT is the parameter source
# $CPATH_DICT is the parameter destination
$SCRIPT_PATH/comparedict.py -s $BRANCH_DICT -d $CPATH_DICT
RET=$?
if [ $RET -lt 0 ]; then
	echo "Keys in these two dictionary files are different"
	echo "exit value:" $RET
	exit 1
elif [ $RET -eq 1 ]; then
	echo "Source repository is the subset of repository that is defined in manifest.xml"
elif [ $RET -eq 2 ]; then
	echo "Repository that is defined in manifest.xml is the subset of source repository"
fi

# Apply tag on working directory
$SCRIPT_PATH/tag.py -i $CPATH_DICT -r $REMOTE_MNAME -t $TAG_NAME
RET=$?
if [ $RET -ne 0 ]; then
	echo "Failed to apply tag"
	echo "exit value:" $RET
	exit 1
fi

# Upload repository to dest server
$SCRIPT_PATH/push.py -t $TAG_NAME --dict-branch=$BRANCH_DICT --dict-path=$CPATH_DICT -d $REMOTE_SERVER -r $DEST_ROOT -b $MANIFEST_BRANCH
RET=$?
if [ $RET -ne 0 ]; then
	echo "Failed to upload repository to dest server"
	echo "exit value:" $RET
	exit 1
fi

if [ ! -z $TAG_SRC ]; then
	# Upload commits to source server
	$SCRIPT_PATH/push.py -t $TAG_NAME --dict-branch=$BRANCH_DICT --dict-path=$CPATH_DICT --tagsrc
	RET=$?
	if [ $RET -ne 0 ]; then
		echo "Failed to upload repository to dest server"
		echo "exit value:" $RET
		exit 1
	fi
fi

# Verify revision number
$SCRIPT_PATH/verify.py --dict-revision=$REVISION_DICT --dict-path=$CPATH_DICT -t $TAG_NAME
RET=$?
if [ $RET -ne 0 ]; then
	echo "verification fail"
	echo "exit value:" $RET
	exit 1
fi

# Register Uploaded Projects by flushing the project_list cache
ssh $REMOTE_SERVER -p 29418 gerrit flush-caches --cache project_list
echo "flushing caches of $REMOTE_SERVER by account $USER RET = $?"
ssh root@$REMOTE_SERVER /usr/share/gerrit/bin/gerrit.sh restart
RET=$?
if [ $RET -ne 0 ]; then
        echo "flush cache fail"
        echo "exit value:" $RET
        exit 1
fi

echo "upload finished!"
