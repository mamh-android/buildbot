#!/bin/bash
maintainer=liling@marvell.com

generate_init_is_not_ready_email()
{
# --- Email (all stdout will be the email)
# Generate header
cat <<-EOF
From: $maintainer
To: $maintainer
Subject: gfx_test_autobuild.git is not downloaded successfully.
This is an automated email from the autobuild script. 

There must be something wrong when git clone the gfx_test_autobuild.git.

So exit test case auto build for this time. Please check.
	
The parameters of this auto build are: $buildDir, $target, $publish

---
EOF
}

send_init_is_not_ready_notification()
{
    generate_init_is_not_ready_email | /usr/sbin/sendmail -t $envelopesender
}


start_gfx_test_autobuild()
{
    #work directory
    #cd ~/aabs/gfx_build
    ## change
    #cd gfx_build

    if [ -d gfx_test_autobuild ]; then
        echo "Remove the gfx_test_autobuild folder"
        rm -rf gfx_test_autobuild
    fi

    ##change
    git clone ssh://shgit.marvell.com/git/qae/graphics/gfx_test_autobuild.git
    #cp -r /boot/pxa1088/qad/gfx_test_autobuild ./

    . gfx_test_autobuild/core.sh $* 
    ## change
    #. ~/aabs/gfx_build/gfx_test_autobuild/core.sh $*
}

if [ $? -ne 0 ]; then
    send_init_is_not_ready_notification
    exit 0
fi

if [ $1 == "Ture" ]; then
    echo "Start Gfx test auto build with $@"
    start_gfx_test_autobuild
    exit 0
else
    echo "Ignore the Gfx test auto build in this loop"
    exit 0
fi
