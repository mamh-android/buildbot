#!/bin/bash
cd ~/buildbot_script/buildbot/
. ../check_update.sh
platform=`awk '{if($1=="platform") print $2}' /home/buildfarm/buildbot_script/args.log`
product=`awk '{if($1=="product") print $2}' /home/buildfarm/buildbot_script/args.log`
release=`awk '{if($1=="last") print $2}' /home/buildfarm/buildbot_script/args.log`
last_build=`awk '{if($1=="last_build") print $2}' /home/buildfarm/buildbot_script/args.log`
line_value=`awk '{if(NR=='3') print $0}' ${last_build}`
echo $line_value
path=`echo ${line_value##*:}`
echo $path
folder=`echo ${path##*/}`
echo $folder
. /home/buildfarm/buildbot_script/buildbot/source_by_patch_test.sh $folder $platform
#. /home/wdong/buildbot-script/buildbot/delta_patch_test.sh $folder
cd $folder
