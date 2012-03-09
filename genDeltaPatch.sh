#############################################
#
# File: genDeltaPatch.sh
# Author: YuanZhang
# Create Data: 06/13/2011
# Update Date: 06/15/2011
# ---------------------------------------
# 
# Description:
#
#  1. Get branch name from two manifest.xml, if same, fetch branch, or exit.
#  2. Retrieve two manifest.xml projects revision.
#  3. In branch, generate patch for each project.
#  4. Move all patches into new same structure directory folder as synced branch.
#
##############################################

#---------------
# Global Definition
#--------------
CUR_PATH="${PWD}"
WORKSPACE="${CUR_PATH}"
FIRST_SYNC_FOLDER="${WORKSPACE}/FirstSyncFolder"
SECOND_SYNC_FOLDER="${WORKSPACE}/SecondSyncFolder"
RESULT_FOLDER="${WORKSPACE}/DeltaPatchResult"
OUTPUT_FOLDER="${WORKSPACE}/DeltaPatchResult/Output"
PATCHES_SUB="${OUTPUT_FOLDER}/patches_sub"
PATCHES_ADD="${OUTPUT_FOLDER}/patches_add"

PATCH_PATH="ANDROID_PATCHES"

XML_ONE="$1"
XML_TWO="$2"

XML_ONE_NAME="${1##*/}"
XML_TWO_NAME="${2##*/}"
REFERENCE_FOLDER="$3"

XML_ONE_LOG="${RESULT_FOLDER}/${XML_ONE_NAME}.log"
android_version_1=echo ${XML_ONE} | grep honeycomb -i
if [ -n ${android_version_1} ]; then
MANIFEST_GIT_1="ssh://shgit.marvell.com/git/droid/platform/manifest.git"
REPO_GIT_1="ssh://shgit.marvell.com/git/droid/tools/repo.git"
else 
NIFEST_GIT_1="ssh://shgit.marvell.com/git/droid/platform/manifest.git"
REPO_GIT_1="ssh://shgit.marvell.com/git/android/tools/repo.git"
fi
android_version_2=echo ${XML_TWO} | grep honeycomb -i
if [ -n ${android_version_2} ]; then
MANIFEST_GIT_2="ssh://shgit.marvell.com/git/droid/platform/manifest.git"
REPO_GIT_2="ssh://shgit.marvell.com/git/droid/tools/repo.git"
else
NIFEST_GIT_2="ssh://shgit.marvell.com/git/droid/platform/manifest.git"
REPO_GIT_2="ssh://shgit.marvell.com/git/android/tools/repo.git"
fi
XML_TWO_LOG="${RESULT_FOLDER}/${XML_TWO_NAME}.log"
FIRST_PROJECTS_LIST="${RESULT_FOLDER}/FirstProjectsList.log"
SECOND_PROJECTS_LIST="${RESULT_FOLDER}/SecondProjectsList.log"
PATCHES_RESULT="${RESULT_FOLDER}/PatchesResult.log"
REVISION_RESULT="${RESULT_FOLDER}/RevisionResult.log"

#MANIFEST_GIT_OTHER="ssh://shgit.marvell.com/git/android/platform/manifest.git"
#MANIFEST_GIT_HONEYCOMB="ssh://shgit.marvell.com/git/droid/platform/manifest.git"
#REPO_GIT="ssh://shgit.marvell.com/git/android/tools/repo.git"

FOLDER_MODE=0

ALREADY_FAILED=0
RETURN_VALUE_PASS="[DELTAPATCH][PASS]"
RETURN_VALUE_FAIL="[DELTAPATCH][FAIL]"

#-----------------
# Function: help
# Usage: show the help
#-----------------
function help(){

	echo "Usage: ${0} old_manifest1.xml new_manifest2.xml [reference_folder]"
	echo "     : ${0} old_folder new_folder [reference_folder]"
}

#--------------------
# Function: clobber
# Usage: clean all result
#-------------------
function clobber(){

	if [ "${FOLDER_MODE}" != "1" ];then
		rm -rf "${FIRST_SYNC_FOLDER}" 1>/dev/null 2>&1
		rm -rf "${SECOND_SYNC_FOLDER}" 1>/dev/null 2>&1
	fi

	rm -rf "${OUTPUT_FOLDER}" 1>/dev/null 2>&1
	rm -rf "${RESULT_FOLDER}" 1>/dev/null 2>&1
	rm -rf "${FIRST_SYNC_FOLDER}/${PATCH_PATH}" 1>/dev/null 2>&1
	rm -rf "${SECOND_SYNC_FOLDER}/${PATCH_PATH}" 1>/dev/null 2>&1

	if [ "${FOLDER_MODE}" != "1" ];then
		mkdir -p "${FIRST_SYNC_FOLDER}"
		mkdir -p "${SECOND_SYNC_FOLDER}"
	else
		FIRST_SYNC_FOLDER=`cd ${XML_ONE} ; pwd`
		SECOND_SYNC_FOLDER=`cd ${XML_TWO} ; pwd`
	fi

	mkdir -p "${OUTPUT_FOLDER}"
	mkdir -p "${RESULT_FOLDER}"
}

#---------------
# Function: checkEnvironment
# Usage: check two paramter manifest files.
#---------------
function checkEnvironment(){

	if [ "$(which repo)" == "" ];then
		echo "Please install repo before running me."
		echo "${RETURN_VALUE_FAIL}"
		exit 1
	fi

	if [ -d "$1" ] && [ -d "$2" ];then
		if [ -f "$1/.repo/manifest.xml" ] && [ -f "$2/.repo/manifest.xml" ];then
			FOLDER_MODE=1
			return
		fi
	fi

	if [ ! -f "$1" ] || [ "$1" == "" ];then
		echo "first manifest file cannot be found."
		help
		echo "${RETURN_VALUE_FAIL}"
		exit 1
	fi

	if [ ! -f "$2" ] || [ "$2" == "" ];then
		echo "second manifest file cannot be found."
		help
		echo "${RETURN_VALUE_FAIL}"
		exit 1
	fi

	if [ "$3" != "" ] && [ ! -d "$3" ];then
		echo "reference offered not exists."
		echo "${RETURN_VALUE_FAIL}"
		exit 1
	fi
}

#---------------
# Function: fetchLatestBranch
# Usage: fetch the branch in xml defined.
#--------------
function fetchLatestBranch(){

	if [ "${FOLDER_MODE}" == "1" ];then
		return
	fi

	if [ "${REFERENCE_FOLDER}" != "" ];then
		REFERENCE_PARAMETER="--reference=${REFERENCE_FOLDER}"
	else
		REFERENCE_PARAMETER=""
	fi

	# IMPROVE ME, next three code line to prevent absolute or relative filename. 

	echo "-> Repo sync first manifest.xml to \"${FIRST_SYNC_FOLDER}\"..."

	cd "${FIRST_SYNC_FOLDER}" &&
	repo init -u ${MANIFEST_GIT_1} ${REFERENCE_PARAMETER} --repo-url=${REPO_GIT_1} 1>/dev/null 2>&1 &&
	cp "${WORKSPACE}/${XML_ONE}" "${FIRST_SYNC_FOLDER}/.repo/manifests/" &&
	repo init -m ${XML_ONE_NAME} 1>/dev/null 2>&1 &&
	repo sync

	checkReturn "fetchLatestBranch ${XML_ONE_NAME} failed."

	echo "-> Repo sync second manifest.xml to \"${SECOND_SYNC_FOLDER}\"..."

	cd "${SECOND_SYNC_FOLDER}" &&
	repo init -u ${MANIFEST_GIT_2} ${REFERENCE_PARAMETER} --repo-url=${REPO_GIT_2} 1>/dev/null 2>&1 &&
	cp "${WORKSPACE}/${XML_TWO}" "${SECOND_SYNC_FOLDER}/.repo/manifests/" &&
	repo init -m ${XML_TWO_NAME} 1>/dev/null 2>&1 &&
	repo sync

	checkReturn "fetchLatestBranch ${XML_TWO_NAME} failed."

	cd "${WORKSPACE}"

}

#-------------------------
# Function: getProjectsInfo
# Usage: get projects list name and path
#-------------------------
function getProjectsInfo(){

	echo "-> Genereate project list ..."

	cd "${FIRST_SYNC_FOLDER}"
	repo list | sed 's/ : /,/g' >> ${FIRST_PROJECTS_LIST}
	checkReturn "getProjectsInfo ${FIRST_PROJECTS_LIST} failed."
	
	cd "${SECOND_SYNC_FOLDER}"
	repo list | sed 's/ : /,/g' >> ${SECOND_PROJECTS_LIST}
	checkReturn "getProjectsInfo ${SECOND_PROJECTS_LIST} failed."
	
	cd "${WORKSPACE}"
	
}

#-------------------------
# Function: genAllPatches
# Usage: genereate all patches in folder1 and folder2
# Param: $1=[first/second folder], $2=[second/first folder], $3=projectlists[first/second projects list]
#-------------------------
function genAllPatches(){

	OLD_SRC_PATH=${1}
	NEW_SRC_PATH=${2}
	PROJECTS_LIST=${3}


	while read PROJECTINFO
	do
		PROJECTPATH=`echo $PROJECTINFO | cut -d, -f1` &&
		PROJECTNAME=`echo $PROJECTINFO | cut -d, -f2` 
		checkReturn

		cd "${OLD_SRC_PATH}/${PROJECTPATH}"
		OLD_REV=`git rev-parse HEAD`
		
		if [ -z ${OLD_REV} ]; then
			echo "${RETURN_VALUE_FAIL} Cannot fetch old rev."
			exit 1
		fi

		if [ -d "${NEW_SRC_PATH}/${PROJECTPATH}" ]; then
			cd "${NEW_SRC_PATH}/${PROJECTPATH}"
		else
			
			# 1. Project path is changed.
			GIT_NAME=`git remote -v | grep "push" | cut -f2 | cut -d' ' -f1`
			GIT_NAME=${GIT_NAME%.git*}
			#`git remote -v | grep "push" | sed "s/.*[[:blank:]]\(.*\)\.git[[:blank:]].*/\1/g"`
			NEW_PRJ_PATH=`grep ${GIT_NAME##*/} ${NEW_SRC_PATH}/.repo/manifest.xml | sed 's/.*path=//g' | cut -d '"' -f2`
			
			# 2. Project path is the same as name.
			if [ -z "${NEW_PRJ_PATH}" ] || [ ! -d "${NEW_SRC_PATH}/${NEW_PRJ_PATH}" ]; then
				NEW_PRJ_PATH=`grep ${GIT_NAME##*/} ${NEW_SRC_PATH}/.repo/manifest.xml | sed 's/.*name=//g' | cut -d '"' -f2`
			fi

			# 3. Project is newly added.
			if [ -z "${NEW_PRJ_PATH}" ] || [ ! -d "${NEW_SRC_PATH}/${NEW_PRJ_PATH}" ]; then
				echo "[WARNING] Project \"${GIT_NAME##*/}\" is a newly added project. Making Tarball ..."
				mkdir -p "${OLD_SRC_PATH}/${PATCH_PATH}/${PROJECTPATH}"
				tar czvf ${OLD_SRC_PATH}/${PATCH_PATH}/${PROJECTPATH}/0001-${GIT_NAME##*/}.tgz ./* > /dev/null
				return
			fi
			cd ${NEW_SRC_PATH}/${NEW_PRJ_PATH}
		fi
		NEW_REV=`git rev-parse HEAD`
		if [ -z ${NEW_REV} ]; then
			echo "${RETURN_VALUE_FAIL} Cannot fetch new rev."
			exit 1
		fi

		GIT_MERGE_BASE=`git merge-base ${OLD_REV} ${NEW_REV}`
		cd "${OLD_SRC_PATH}/${PROJECTPATH}"
		CUR_REV=`git rev-parse HEAD`

		if [ "${GIT_MERGE_BASE}" != "${CUR_REV}" ]; then
			mkdir -p "${OLD_SRC_PATH}/${PATCH_PATH}/${PROJECTPATH}"
			git format-patch ${GIT_MERGE_BASE}..HEAD -o "${OLD_SRC_PATH}/${PATCH_PATH}/${PROJECTPATH}" > /dev/null
			echo "${PROJECTPATH} : ${GIT_MERGE_BASE} --> ${CUR_REV}"
		fi

	done < "${PROJECTS_LIST}"
}

#-------------------------
# Function: diffPatches
# Usage: diff all patches in two output patches folder.
#        delete same patches.
# Param: $1=oldpatches folder, $2=newpatches folder.
#------------------------
function diffPatches(){

	OLD_PATCHES_FOLDER=${1}
	NEW_PATCHES_FOLDER=${2}

	find "${OLD_PATCHES_FOLDER}" -name "*.patch" > "/tmp/opjxxx"
	
	while read FILE1
	do
		STRIPFILE1="/tmp/${FILE1##*/}_strip1"
		cp -f "${FILE1}" "${STRIPFILE1}"
		# strip header/Change-Id/Sign/index/Line-ref/Blank-line/dos-character from patch
		sed -i -e "1,4d" -e "/Change-Id:/d" -e "/Signed-off-by:/d" \
			-e "/index[[:blank:]][a-zA-Z0-9]*\.\.[a-zA-Z0-9]*/d" \
			-e "s/@@[^@]*@@//" -e "/^$/d" -e "s/\r$//" "${STRIPFILE1}"
		FULLNAME=${FILE1##*/}
		FILENAME=`echo ${FULLNAME%\.*} | sed "s/[0-9][0-9][0-9][0-9]-//"`
		
		find "${NEW_PATCHES_FOLDER}" -name "*${FILENAME}*.patch" > "/tmp/npjxxx"
		
		while read FILE2
		do
			STRIPFILE2="/tmp/${FILE2##*/}_strip2"
			cp -f "${FILE2}" "${STRIPFILE2}"
			sed -i -e "1,4d" -e "/Change-Id:/d" -e "/Signed-off-by:/d" \
				-e "/index[[:blank:]][a-zA-Z0-9]*\.\.[a-zA-Z0-9]*/d" \
				-e "s/@@[^@]*@@//" -e "/^$/d" -e "s/\r$//" "${STRIPFILE2}"
			#Compare with patches with the same file name
			if [ -z "$(diff ${STRIPFILE1} ${STRIPFILE2})" ]; then
				echo "-> Delete Same Patches ${FILE1} ${FILE2}..."
				rm -f "${FILE1}" "${FILE2}"
			fi
		done < "/tmp/npjxxx"
	done < "/tmp/opjxxx"

}

#---------------------
# Function: movePatches
# Usage: move patches from old/new src folder to sub/add folder.
#---------------------
function movePatches(){

	rm -rf "${PATCHES_SUB}" 
	rm -rf "${PATCHES_ADD}"

	if [ -d "${FIRST_SYNC_FOLDER}/${PATCH_PATH}" ]; then 
		mv "${FIRST_SYNC_FOLDER}/${PATCH_PATH}" "${PATCHES_SUB}"
	fi

	if [ -d "${SECOND_SYNC_FOLDER}/${PATCH_PATH}" ]; then 
		mv "${SECOND_SYNC_FOLDER}/${PATCH_PATH}" "${PATCHES_ADD}" 
	fi

}

#---------------------
# Function: reOrderPatches
# Usage: for patches which is not from 0001, reorder them.
# Param: $1=patches folder
#--------------------
function reOrderPatches(){

	INDEX=1
	PROJECTPATH=""
	PATCHES_FOLDER="${1}"

	find "${PATCHES_FOLDER}" -name "*.patch" > "/tmp/plxxx"

	while read FILE
	do
		if [ "${FILE%/*}" != "${PROJECTPATH}" ];then
			INDEX=1
			PROJECTPATH="${FILE%/*}"
		fi
		FULLNAME=${FILE##*/}
		FILEINDEX=${FULLNAME%%-*}
		FILENAME=${FULLNAME#*-}
		#rename patch
		if [ "$(printf %04d ${INDEX})" != "${FILEINDEX}" ]; then
			NEW_FILENAME="$(printf %04d ${INDEX})-${FILENAME}"
			while [ -f "${FILE%/*}/${NEW_FILENAME}" ]
			do
				INDEX=$((INDEX + 1))
				NEW_FILENAME="$(printf %04d ${INDEX})-${FILENAME}"
			done
			mv "${FILE}" "${FILE%/*}/${NEW_FILENAME}"
		fi
		INDEX=$((INDEX + 1))
	done < "/tmp/plxxx"

}

#------------------------
# Function: deleteEmptyFolder
# Usage: delete any empty folder in sub/add folder
#------------------------
function deleteEmptyFolder(){
	find "${PATCHES_SUB}" -type d -exec rmdir -p --ignore-fail-on-non-empty {} \; 2>/dev/null
	find "${PATCHES_ADD}" -type d -exec rmdir -p --ignore-fail-on-non-empty {} \; 2>/dev/null
}

#------------------------
# Function: checkReturn
# Usage: check the return value of last command, if fail, already_fail set to 1. and exit
#-----------------------
function checkReturn(){

	if [ $? -ne 0 ];then
		echo "${RETURN_VALUE_FAIL} : ${1}"
		exit 1
	fi
}

#---------------------
# Function: summary
# Usage: display the result files summary
#--------------------
function summary(){

	echo ""
	echo "============ Summary ============="
	echo "-> Patches Folder: \"${OUTPUT_FOLDER}\""
	echo "-> Patches TAR Package: \"${OUTPUT_FOLDER}/delta_patches.tgz\""
	echo ""

	echo "${RETURN_VALUE_PASS}"
	exit 0

}

#-----------------------------
# Function: tarPatches
# Usage: tar the patches result into tar.gz
#-----------------------------
function tarPatches(){

	echo "-> Packaging Patches ..."
	PATCHES_ADD_RESULT="${OUTPUT_FOLDER}/patches_add.txt"
	PATCHES_SUB_RESULT="${OUTPUT_FOLDER}/patches_sub.txt"

	RESULT_NAME="delta_patches"

	cd "${PATCHES_SUB}"
	tree > "${PATCHES_SUB_RESULT}"
	cd "${PATCHES_ADD}"
	tree > "${PATCHES_ADD_RESULT}"

	cd "${OUTPUT_FOLDER}"

	tar czf ${RESULT_NAME}.tgz patches_sub/ patches_add/ patches_add.txt patches_sub.txt
	#----------------------------------------------------------
	
	cd ${WORKSPACE}

}


#-----------------
# Function: main
# Usage: where the script begin
#----------------
function main(){

	checkEnvironment $*
	clobber
	fetchLatestBranch
	getProjectsInfo
	genAllPatches ${FIRST_SYNC_FOLDER} ${SECOND_SYNC_FOLDER} ${FIRST_PROJECTS_LIST}
	genAllPatches ${SECOND_SYNC_FOLDER} ${FIRST_SYNC_FOLDER} ${SECOND_PROJECTS_LIST}
	diffPatches ${FIRST_SYNC_FOLDER} ${SECOND_SYNC_FOLDER}
	diffPatches ${SECOND_SYNC_FOLDER} ${FIRST_SYNC_FOLDER}
	movePatches
	reOrderPatches ${PATCHES_SUB}
	reOrderPatches ${PATCHES_ADD}
	deleteEmptyFolder
	tarPatches
	summary
}

main $*
