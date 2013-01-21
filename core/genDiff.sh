#!/bin/bash

###############################################
#
# File: genDiff.sh
# Author: YuanZhang
# Date: 06/17/2011
# Update: 04/27/2012
# -----------------------------------
#
# Description:
#
#   1. Generate result of diffz two folders.
#   2. Process the result file to move different file 
#      into each same structure folder as before.
#   3. xxxxxxx
#
################################################

#---------------------
# Global definition
#---------------------
CUR_PATH="${PWD}"
WORKSPACE="${CUR_PATH}"
RESULT_FOLDER="${WORKSPACE}/DiffResult"
RELEASE_FOLDER="${3}"

FOLDER1="$(cd ${1} && pwd)"
FOLDER2="$(cd ${2} && pwd)"
FOLDER1_NAME="${FOLDER1##*/}"
FOLDER2_NAME="${FOLDER2##*/}"

DIFF_EXECU="/home/buildfarm/buildbot_script/buildbot/core/diffz"
DIFF_PARAM="-rsq -x .git -x .repo"

RAWDATA="${RESULT_FOLDER}/RawData"
DIFFDATA="${RESULT_FOLDER}/DiffData"
ONLYDATA="${RESULT_FOLDER}/OnlyData"
IDENTICALDATA="${RESULT_FOLDER}/IdenticalData"

FOLDER1_ONLY_LIST="${RESULT_FOLDER}/OnlyIn_${FOLDER1_NAME}.lst"
FOLDER2_ONLY_LIST="${RESULT_FOLDER}/OnlyIn_${FOLDER2_NAME}.lst"
DIFF_LIST="${RESULT_FOLDER}/DiffBetween_${FOLDER1_NAME}_${FOLDER2_NAME}.lst"

RETURN_VALUE_PASS="[DIFFFILES][PASS]"
RETURN_VALUE_FAIL="[DIFFFILES][FAIL]"

#-------------------------
# Function: help
# Usage: display help info
#-------------------------
function help(){

	echo "Usage: $0 FOLDER1 FOLDER2"
}

#------------------------
# Function: checkReturn
# Usage: check the return value of last command, if fail, already_fail set to 1. and exit
#-----------------------
function checkReturn(){

	if [ $? -ne 0 ];then
		echo "${RETURN_VALUE_FAIL} : ${1}"
		exit
	fi
}

#---------------------------
# Function: clobber
# Usage: clean all result in result folder.
#---------------------------
function clobber(){

	rm -rf "${RESULT_FOLDER}" 1>/dev/null 2>&1
	mkdir -p "${RESULT_FOLDER}"

}

#---------------------
# Function: checkEnvironment
# Usage: check all environment
#--------------------
function checkEnvironment(){

	if [ "${1}" == "" ] || [ "${2}" == "" ];then
		echo "Please offer two folders for differ."
		help
		echo "${RETURN_VALUE_FAIL}"
		exit
	fi

	if [ ! -d "${1}" ] || [ ! -d "${2}" ];then
		echo "Please offer exists folders for differ."
		echo "${RETURN_VALUE_FAIL}"
		exit
	fi

	if [ ! -f "${DIFF_EXECU}" ];then
		echo "Cannot find diff executation file: \"${DIFF_EXECU}\""
		echo "${RETURN_VALUE_FAIL}"
		exit
	fi

}

#--------------------
# Function: genRawData
# Usage: use diffz to generate raw diff result.
#--------------------
function genRawData(){

	echo "-> Generating difference between folders: \"${FOLDER1}\" and \"${FOLDER2}\" ..."
	${DIFF_EXECU} ${DIFF_PARAM} "${FOLDER1}" "${FOLDER2}" > "${RAWDATA}"
}

#---------------------
# Function: retrieveData
# Usage: use grep to get all diff or only data into file.
#---------------------
function retrieveData(){

	echo "-> Retrieve identical, only, differ data from raw data ..."
	
	cat "${RAWDATA}" | grep '\[\%\:DIFFER\:\%\]' > "${DIFFDATA}"
	cat "${RAWDATA}" | grep '\[\%\:ONLY\:\%\]' > "${ONLYDATA}"
	cat "${RAWDATA}" | grep '\[\%\:IDENTICAL\:\%\]' > "${IDENTICALDATA}"

}

#---------------------
# Function: processOnlyData
# Usage: process the OnlyData, move only files 
#        into same structure folder.
#---------------------
function processOnlyData(){

	echo "-> Processing Only Files Data ..."

	while read LINEINFO
	do
		
		FOLDERPATH=`echo ${LINEINFO} | cut -d# -f2`
		# since the only data maybe contain only folders, use name for variable.
		NAME=`echo ${LINEINFO} | cut -d# -f4`

		# check whether failed to cut and empty LINEINFO.
		if [ "${FOLDERPATH}" == "${LINEINFO}" ] || [ "${NAME}" == "${LINEINFO}" ] || [ "${LINEINFO}" == "" ];then
			continue;
		fi
		
		SOURCEPATH="${FOLDERPATH}/${NAME}"

		# check which folder only have this file or folder.
		CHECK=`echo ${FOLDERPATH} | grep "${FOLDER1}"`
		if [ "${CHECK}" != "" ];then
			RELATIVE_FOLDERPATH="${FOLDERPATH##*/${FOLDER1_NAME}}"
			TARGETFOLDERPATH="${RESULT_FOLDER}/${FOLDER1_NAME}/${RELATIVE_FOLDERPATH}"
			if [ ! -d "${SOURCEPATH}" ];then
				echo "${SOURCEPATH}" >> "${FOLDER1_ONLY_LIST}"
			else
				find "${SOURCEPATH}" -type f >> "${FOLDER1_ONLY_LIST}"
			fi
		else
			RELATIVE_FOLDERPATH="${FOLDERPATH##*/${FOLDER2_NAME}}"
			TARGETFOLDERPATH="${RESULT_FOLDER}/${FOLDER2_NAME}/${RELATIVE_FOLDERPATH}"
			if [ ! -d "${SOURCEPATH}" ];then
				echo "${SOURCEPATH}" >> "${FOLDER2_ONLY_LIST}"
			else
				find "${SOURCEPATH}" -type f >> "${FOLDER2_ONLY_LIST}"
			fi
		fi

		if [ ! -d ${TARGETFOLDERPATH} ];then
			mkdir -p "${TARGETFOLDERPATH}"
		fi

		cp -af "${SOURCEPATH}" "${TARGETFOLDERPATH}/${NAME}"

		checkReturn "processOnlyData, Copy \"${SOURCEPATH}\" to \"${TARGETFOLDERPATH}/${NAME}\" Failed."

	done < "${ONLYDATA}"

}

#----------------------
# Function: processDiffData
# Usage: process the DiffData, move different 
#        files into each same structure folder.
#---------------------
function processDiffData(){

	echo "-> Processing Differ Files Data ..."

	while read LINEINFO
	do
		
		FILEPATH1=`echo ${LINEINFO} | cut -d# -f2`
		FILEPATH2=`echo ${LINEINFO} | cut -d# -f4`
		# check whether failed to cut and empty LINEINFO.
		if [ "${FILEPATH1}" == "${LINEINFO}" ] || [ "${FILEPATH2}" == "${LINEINFO}" ] || [ "${LINEINFO}" == "" ];then
			continue;
		fi

		FILENAME1="${FILEPATH1##*/}"
		FILENAME2="${FILEPATH2##*/}"

		# convert absolute folder path into relative folder path without folder root name
		ABSOLUTE_FOLDERPATH1="${FILEPATH1%%${FILENAME1}}"
		RELATIVE_FOLDERPATH1="${ABSOLUTE_FOLDERPATH1##*/${FOLDER1_NAME}}"
		ABSOLUTE_FOLDERPATH2="${FILEPATH2%%${FILENAME2}}"
		RELATIVE_FOLDERPATH2="${ABSOLUTE_FOLDERPATH2##*/${FOLDER2_NAME}}"
		
		TARGETFOLDERPATH1="${RESULT_FOLDER}/${FOLDER1_NAME}/${RELATIVE_FOLDERPATH1}"
		TARGETFOLDERPATH2="${RESULT_FOLDER}/${FOLDER2_NAME}/${RELATIVE_FOLDERPATH2}"

		if [ ! -d "${TARGETFOLDERPATH1}" ];then
			mkdir -p "${TARGETFOLDERPATH1}"
		fi

		if [ ! -d "${TARGETFOLDERPATH2}" ];then
			mkdir -p "${TARGETFOLDERPATH2}"
		fi

		cp -af "${FILEPATH1}" "${TARGETFOLDERPATH1}/${FILENAME1}" &&
		cp -af "${FILEPATH2}" "${TARGETFOLDERPATH2}/${FILENAME2}"

		checkReturn "processDiffData, Copy \"${FILEPATH1}\" \"${TARGETFOLDERPATH1}/${FILENAME1}\" Failed."

		echo "${FILEPATH1}" >> "${DIFF_LIST}"

	done < "${DIFFDATA}"
}

#------------------------
# Function: tarResult
# Usage: tarball results as DiffFiles
#------------------------
function tarResult(){

	echo "-> Making Result Tarball ..."
	OUTPUT_NAME="diff_files"
	cd "${RESULT_FOLDER}"
	
	# check whether all files exists.
	if [ ! -e "OnlyIn_${FOLDER1_NAME}.lst" ];then
		touch "OnlyIn_${FOLDER1_NAME}.lst"
	fi
	if [ ! -e "OnlyIn_${FOLDER2_NAME}.lst" ];then
		touch "OnlyIn_${FOLDER2_NAME}.lst"
	fi
	if [ ! -e "DiffBetween_${FOLDER1_NAME}_${FOLDER2_NAME}.lst" ];then
		touch "DiffBetween_${FOLDER1_NAME}_${FOLDER2_NAME}.lst"
	fi
	if [ ! -d "${FOLDER1_NAME}" ];then
		mkdir -p "${FOLDER1_NAME}"
	fi
	if [ ! -d "${FOLDER2_NAME}" ];then
		mkdir -p "${FOLDER2_NAME}"
	fi

	tar czf ${OUTPUT_NAME}.tgz "${FOLDER1_NAME}" "${FOLDER2_NAME}" "OnlyIn_${FOLDER1_NAME}.lst" "OnlyIn_${FOLDER2_NAME}.lst" "DiffBetween_${FOLDER1_NAME}_${FOLDER2_NAME}.lst"

	cp -f "${OUTPUT_NAME}.tgz" "${RELEASE_FOLDER}/"

	checkReturn "tarResult ${OUTPUT_NAME}.tgz \"${FOLDER1_NAME}\" \"${FOLDER2_NAME}\" Failed."
}

#------------------------
# Function: summary
# Usage: display the result
#------------------------
function summary(){

	echo "=========== Summary ============="
	echo "-> Result File: \"${RESULT_FOLDER}/diff_files.tgz\""
	echo ""
	echo "${RETURN_VALUE_PASS}"
}


#------------------------
# Function: main
# Usage: where the script begin
#------------------------
function main(){

	checkEnvironment $*
	clobber
	genRawData
	retrieveData
	processDiffData
	processOnlyData
	tarResult
	#summary

}

main $*
