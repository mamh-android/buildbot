#!/bin/bash
#
list=$(ssh -p 29418 shgit.marvell.com gerrit ls-groups)

rm /tmp/me;
for i in $list;do
echo ====== $i ====== >> /tmp/me;
ssh -p 29418 shgit.marvell.com gerrit ls-members $i | tee -a /tmp/me;
done

gerrit_permission(){
for i in $(cat l); do
    git fetch ssh://shgit.marvell.com/$i refs/meta/config && git reset --hard FETCH_HEAD;
    if grep -q Permission_parent/All-android *;then
      echo ===
      echo yes
      echo ===
    else
      echo ===
      echo no
      echo $i
      cat config
      echo ===
    fi
done
}
