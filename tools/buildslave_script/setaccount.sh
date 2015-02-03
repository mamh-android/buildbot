#!/bin/bash
#
#cat ~/.ssh/id_watcher.pub | ssh -p 29418 shgit.marvell.com gerrit set-account --add-ssh-key - watcher
#cat k | ssh -p 29418 shgit.marvell.com gerrit set-account --add-ssh-key - ATFAdim

ssh -p 29418 shgit.marvell.com gerrit set-account --full-name NA --delete-email wsun@marvell.com 1000254
