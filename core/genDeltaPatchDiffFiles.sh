#############################################
#
# File: genDeltaPatchDiffFiles.sh
# Author: YuanZhang
# Create Data: 06/13/2011
# Update Date: 04/27/2012
# ---------------------------------------
# 
# Description:
#
#  This is the shell script for calling genDeltaPatch.sh and genDiff.sh
#
##############################################

#---------------
# Global Definition
#--------------
CUR_PATH="${PWD}"
WORKSPACE="${CUR_PATH}"
FIRST_SYNC_FOLDER="${WORKSPACE}/FirstSyncFolder"
SECOND_SYNC_FOLDER="${WORKSPACE}/SecondSyncFolder"
DELTA_RESULT_FOLDER="${WORKSPACE}/DeltaPatchResult"
DIFF_RESULT_FOLDER="${WORKSPACE}/DiffResult"

XML_ONE="$1"
XML_TWO="$2"

XML_ONE_NAME="${1##*/}"
XML_TWO_NAME="${2##*/}"

RELEASE_FOLDER=`echo ${XML_TWO%%${XML_TWO_NAME}*}`

#--------------------
# Function: clobber
# Usage: clean all result
#-------------------
function clobber(){

	rm -rf "${DELTA_RESULT_FOLDER}" 1>/dev/null 2>&1
	rm -rf "${DIFF_RESULT_FOLDER}" 1>/dev/null 2>&1
	rm -rf "${FIRST_SYNC_FOLDER}" 1>/dev/null 2>&1
	rm -rf "${SECOND_SYNC_FOLDER}" 1>/dev/null 2>&1

}

#-----------------
# Function: main
# Usage: where the script begin
#----------------
function main(){

	bash ~/buildbot_script/buildbot/core/genDeltaPatch.sh "${XML_ONE}" "${XML_TWO}"
	bash ~/buildbot_script/buildbot/core/genDiff.sh "${FIRST_SYNC_FOLDER}" "${SECOND_SYNC_FOLDER}" "${RELEASE_FOLDER}"
	
	#clean the tmp files & folder
	clobber
}

main $*
