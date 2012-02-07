#!/bin/bash
platform=`awk '{if($1=="platform") print $2}' /home/buildfarm/buildbot_script/args.log`
product=`awk '{if($1=="product") print $2}' /home/buildfarm/buildbot_script/args.log`
release=`awk '{if($1=="last") print $2}' /home/buildfarm/buildbot_script/args.log`
if [ ! -n "${release}" ]; then
    source_path="/home/buildfarm/aabs/src.${platform}-${product}"
    target="${platform}-${product}"
else
    source_path="/home/buildfarm/aabs/src.${platform}-${product}.${release}"
    if [ ! -d $source_path ]; then
        source_path="/home/buildfarm/aabs/src.${platform}-${product}_${release}"
    fi
    target="${platform}-${product}:${release}"
fi
repoDir="~/aabs"
result_pkg="/autobuild"
~/ait_build/testAutobuild.sh ${repoDir} ${platform} ${source_path} ${result_pkg} $target
