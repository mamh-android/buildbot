#!/bin/bash
#
#repo forall -c rtvb_patches.sh list

removte_server=shgit

rev_current=$(git log -1 --pretty=format:%H)
branch_manifest=$REPO_RREV

if [[ $branch_manifest =~ ^[0-9a-z]+$ && ${#branch_manifest} -eq 40 ]]; then
    rev_manifest=$branch_manifest
else
    rev_manifest=$(git log -1 --pretty=format:%H $removte_server/$branch_manifest)
fi
#rev_manifest=$(repo info ./ | grep "Current revision" | awk -F"Current revision: " '{ print $2 }')

if [ "$rev_current" != "$rev_manifest" ]; then
    git log --pretty=format:%H ${rev_manifest}..${rev_current}
    echo " "
fi

