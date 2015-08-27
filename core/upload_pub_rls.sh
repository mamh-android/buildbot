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

export SYNC_GIT_WORKING_DIR=${SYNC_GIT_WORKING_DIR:-~/aabs/pub_work}
export REMOTE_SERVER=${REMOTE_SERVER:-github.marvell.com}
export REMOTE_MNAME=${REMOTE_MNAME:-mars}

#script path
SCRIPT_PATH=`pwd`/core

#call upload_in_rls.sh pushing code to public server
$SCRIPT_PATH/upload_in_rls.sh $@
