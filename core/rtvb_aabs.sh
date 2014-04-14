#!/bin/bash

# export ABS_SOURCE_DIR and ABS_PUBLISH_DIR to trigger a real time virtual build
export ABS_REAL_TIME_VIRTUAL_BUILD=true
export ABS_SOURCE_DIR=$1
export ABS_PUBLISH_DIR=$2

~/aabs/tools/build_platforms.sh $3
