#!/bin/bash
#

for i in $(cat l);do
    echo === $i ===
    ssh -p 29418 shgit.marvell.com gerrit set-members -a $i LPRE_R
done
