#!/bin/bash
#
#repo forall -c rtvb_patches.sh list

removte_server=shgit

rev_current=$(git log -1 --pretty=format:%H)
branch_manifest=$REPO_RREV
rev_manifest=$(git log -1 --pretty=format:%H $removte_server/$branch_manifest)
#rev_manifest=$(repo info ./ | grep "Current revision" | awk -F"Current revision: " '{ print $2 }')

#echo -----------------------------------------------

if [ "$rev_current" != "$rev_manifest" ]; then
    #echo "${REPO_PATH}: no change"
#else
    #echo "${REPO_PATH}:"
    git log --pretty=format:%H ${rev_manifest}..${rev_current}
    echo " "
fi

