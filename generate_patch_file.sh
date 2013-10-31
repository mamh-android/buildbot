#!/bin/bash
set -o pipefail
sour=$1
dest=$2

REFERENCE_FOLDER="$3"

REPO_GIT="ssh://shgit.marvell.com/git/android/tools/repo.git"

MANIFEST_GIT="ssh://shgit.marvell.com/git/android/platform/manifest.git"

REPO_MIRROR=/mnt/mirror/default

DATE=$(date +%Y-%m-%d-%H-%M-%S)

OUTPUT_FOLDER=/autobuild/code-compare/${DATE}
OUTPUT_FILE=${OUTPUT_FOLDER}/patch_list.diff

update_tag()
{
	repo forall -c "git tag -f $1 2>/dev/null" && \
	repo list > $2
}

echo_out()
{
    echo "$*" >> ${OUTPUT_FILE}
}

#. ~/buildbot_script/buildbot/core/check_update.sh
#cd ~/buildbot_script/
#. ~/buildbot_script/buildbot/core/genDeltaPatchDiffFiles.sh ${sour} ${dest}
cd ~/buildbot_script
mkdir workdir
cd workdir
cp ${sour} ./m1.xml
cp ${dest} ./m2.xml


#################### sync code and make tag ########################################
repo init -u ${MANIFEST_GIT} --reference ${REPO_MIRROR}

cp ./m1.xml .repo/manifests && cp ./m2.xml .repo/manifests && \
repo init -m m1.xml && \
repo sync && \
update_tag tag1 list1 && \
repo init -m m2.xml && \
repo sync && \
update_tag tag2 list2

##################### do compare ##################################################
echo_out --- ${sour}
echo_out +++ ${dest}
echo_out
echo_out Added/Removed projects:
echo_out =======================
echo_out

/usr/bin/diff -u list1 list2 |perl -nle "if (/^[-+][^-+]/) { s/^\+/+   /; s/^-/-   /; print }" |LC_ALL=C sort >> ${OUTPUT_FILE}

echo_out
echo_out Changes in each project:
echo_out ========================
echo_out

repo forall -p -c git log --left-right --cherry-pick --date=short --pretty='%m || %h ||  %s (%an) (%cd)' tag1...tag2| \
    sed -r "s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]//g" |  # ansi2txt \
    perl -ple 's/^>/+/; s/^</-/' >> ${OUTPUT_FILE}    # Convert > to + and < to -


############# start to generate patch #############################
while read -r line
do
   if [ -n "$line" ]; then
    cleanLine=${line%% *}
    if [ $cleanLine = "project" ]; then
         projectName=${line#project *}
         pkgFolder="${OUTPUT_FOLDER}/patch-package/$projectName"
             mkdir -p $pkgFolder
             cd $projectName
             git format-patch -o $pkgFolder tag1...tag2
         cd -
    fi
   fi
done < ${OUTPUT_FILE}
cd ${OUTPUT_FOLDER}/patch-package && \
tree  > "./patch-structure.txt" && cd ../ && \
tar zcvf patch-package.tgz "patch-package"
rm -rf "./patch-package"
