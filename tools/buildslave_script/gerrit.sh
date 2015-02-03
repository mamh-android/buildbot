#!/bin/sh

# 1. Init version, Tony Teng
# 2. Add changeid check, get user name from git user.email
#    Weichuan Yan, 2011-01-06

usage()
{
	echo "$(echo $0 | awk -F/ {'print $NF'})  <branch name>"
}

if [ $# -ne 1 ]; then
	usage
	exit 1;
else    
	branch="$1"
fi

cimsg="$(echo `git show | head -n 64`)"
changeid="$(echo ${cimsg} | awk '{print match($0, "Change-Id:")}')" 
if [ ${changeid} = "0" ]; then
	echo "No Change-Id in commit message!"
	echo "Get commit-msg by \"scp -p -P 29418 shgit.marvell.com:hooks/commit-msg .git/hooks/\"."
	echo "Git commit again."
	exit 1;
fi

remote="$(git remote -v)"
if [ $? -ne 0 ]; then
	echo "No git project in current directory!"
	exit 1;
fi

project=$(echo $remote | awk '{print $2}' | sed -e "s#.*/git/##g")
if [ -z ${project} ]; then
	echo "No git project in remote server!"
	exit 1;
fi

user=$(git config --get user.email | awk -F@ '{print $1}')
if [ -z ${user} ]; then
	echo "No git user, add your git email by \"git config --global user.email xxx@marvell.com\"."
	exit 1;
fi

cmd="git push ssh://shgu@shgit.marvell.com:29418/${project}  HEAD:refs/for/${branch}"

echo $cmd
echo -n "Push the patch? [y/n]: "
read ans
case "${ans}" in
	"y"|"Y")	
		$(${cmd})
		if [ $? -ne 0 ]; then
			echo "Error!"
			exit 1;
		fi
		echo "Done!"	
		;;    
	*)	
		echo "Abort!"
		;;
esac

exit 0
