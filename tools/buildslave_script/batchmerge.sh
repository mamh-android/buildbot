#!/bin/bash

if [ $# -ne 3 ] && [ $# -ne 1 ] && [ $# -ne 2 ]
then
	echo "Usage:"
	echo "	batchmerge <project_name> <branch_name> <topic>"
	echo "	batchmerge <topic>"
	echo "	batchmerge <\"topic\"|\"change\"> <topic_name|change-id> "
	echo
	echo "Example:"
	echo "	batchmerge ose/linux/mrvl-3.4 mrvl-3.4 iks_patch"
	echo "	batchmerge wifi_feature"
	echo "	batchmerge topic wifi_feature"
	exit 1
fi

alias gerrit='ssh -p 29418 shgit.marvell.com gerrit'
shopt -s expand_aliases

if [ $# -eq 3 ]
then
	git pull --rebase
	git push ssh://$USER@shgit.marvell.com:29418/$1 HEAD:refs/for/$2/$3
	gerrit query status:open project:$1 branch:$2 topic:$3 --current-patch-set |  egrep '^    revision' | cut -d:  -f2 > change.txt
fi

if [ $# -eq 1 ]
then
	gerrit query status:open topic:$1 --current-patch-set |  egrep '^    revision' | cut -d:  -f2 > change.txt
fi

if [ $# -eq 2 ]
then
	if [ "$1" == "topic" ]
	then
		gerrit query status:open topic:$2 --current-patch-set |  egrep '^    revision' | cut -d:  -f2 > change.txt
	fi

	if [ "$1" == "change" ]
	then
		gerrit query status:open change:$2 --current-patch-set |  egrep '^    revision' | cut -d:  -f2 > change.txt
	fi
fi

if [ -s change.txt ]
then
	cat change.txt | awk '{ line[NR]=$0 } END { for(i=NR; i>0; i--) print line[i] }'  > change_rev.txt
	for i in `cat change_rev.txt`; do gerrit review --code-review 2 --verified 1 --submit $i; done
else
	echo "Didn't find any patches"
fi
