#!/bin/bash
#

for i in $(cat list);do
    #ssh -p 29418 shgit.marvell.com gerrit set-project $i --submit-type REBASE_IF_NECESSARY --change-id true --content-merge false
    ssh -p 29418 shgit.marvell.com gerrit set-project-parent --parent Permission_parent/All-lpre $i
done
