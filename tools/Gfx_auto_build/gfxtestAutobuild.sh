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
	
	The parameters of this auto build are: $in_product, $buildDir, $result_pkg and $information.

	---
	EOF
}

send_init_is_not_ready_notification()
{
	generate_init_is_not_ready_email | /usr/sbin/sendmail -t $envelopesender
}

#work directory
cd ~/aabs/gfx_build
## change
#cd gfx_build

if [ -d gfx_test_autobuild ]
then
	rm -rf gfx_test_autobuild
fi

##change
git clone ssh://shgit.marvell.com/git/qae/graphics/gfx_test_autobuild.git
#cp -r /boot/pxa1088/qad/gfx_test_autobuild ./

if [ $? -ne 0 ]
then
	send_init_is_not_ready_notification
	exit 0
fi

#. gfx_test_autobuild/core.sh $* 
## change
. ~/aabs/gfx_build/gfx_test_autobuild/core.sh $*
