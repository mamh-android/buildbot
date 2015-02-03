#!/bin/bash
#
list=$(ssh -p 29418 shgit.marvell.com gerrit ls-groups)

rm /tmp/me;
for i in $list;do
echo ====== $i ====== >> /tmp/me;
ssh -p 29418 shgit.marvell.com gerrit ls-members $i | tee -a /tmp/me;
done
