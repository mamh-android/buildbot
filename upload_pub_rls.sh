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
#upload_pub_rls.sh -t <tag name> -m <manifest xml> -b <manifest branch> --tagsrc

export SYNC_GIT_WORKING_DIR=$(pwd)/pub_work
export REMOTE_SERVER=10.38.32.104
export REMOTE_MNAME=mars

#script path
SCRIPT_PATH=`pwd`

#call upload_in_rls.sh pushing code to public server
$SCRIPT_PATH/upload_in_rls.sh $@
