#!/bin/bash

. build/envsetup.sh
lunch $1-$2
make -j48
ret=$?
if [ ! $ret == 0 ];then
    echo Make failed
    exit 1
fi
echo Make Done
exit 0
