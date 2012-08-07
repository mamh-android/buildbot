#sh upload_in_rls.sh -t orchid-v1 -m 0504.xml -b rls_mk2_ics_beta
#sh upload_in_rls.sh -t rls_pxa920_ics_beta3_sp1_rc2 -m 0529_920_ics_beta3.xml -b rls_pxa920_ics_beta3
#sh upload_in_rls.sh -t rls_pxa920_ics_beta3_sp1_rc4 -m manifest_pxa920_ics_beta3_sp1_rc2_modified.xml -b rls_pxa920_ics_beta3
export SYNC_GIT_WORKING_DIR=$(pwd)/in_work
export REMOTE_MNAME=localhost
export DEST_ROOT=/test/
export REFERENCE_URL="--reference=~/workspace/mmp3-ics-mirror"
export REPO_URL="--repo-url=ssh://shgit.marvell.com/git/android/tools/repo"
sh /home/hzhuang1/workspace/script/upload_in_rls.sh -t rls_pxa920_ics_beta3_sp1_rc7 -m /home/hzhuang1/workspace/manifest_pxa920_ics_beta3_sp1_rc2_modified.xml -b rls_pxa920_ics_beta3
RET=$?
if [ $RET -ne 0 ]; then
        echo "failed on fetching code from manifest branch"
        echo "return value:" $RET
        exit 1
fi

