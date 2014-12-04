#!/bin/bash
#
# Need environment variables:
# PUBLISH_SERVER

# Command usage:
#publishRls.sh -t <Tag_Name> -m <manifest xml>

export PUBLISH_SERVER=${PUBLISH_FILE:-/APSE_Release}

#script path
SCRIPT_PATH=$(dirname `readlink -f $0`)/core

case "$1" in
    "-t") TAG_NAME=$2
          echo "TAG_NAME= $2"
          ABS_DEVICE=${TAG_NAME%%_*}
          ABS_RLS=${TAG_NAME%.*}
          ABS_TAG=${TAG_NAME##*.}
          ;;
    *) echo "wrong parameter $1"; exit 1 ;;
esac
case "$3" in
    "-m") MANIFEST_XML=$4
    if [ -f $MANIFEST_XML ]; then
        echo "$MANIFEST_XML exists"
        MANIFEST_NAME=$(basename $4)
        BUILD_DIR=$(dirname $4)
    else
        echo "$4 doesn't exist"
        exit 1
    fi
    ;;
    *) echo "wrong parameter $3"; exit 1 ;;
esac

LAST_RLS=LAST_RLS.${ABS_RLS}
#Code comparing if LAST_RLS exist
if [ -f "${PUBLISH_SERVER}/${LAST_RLS}" ] && [ ! -d "${BUILD_DIR}/code-compare" ]; then
    mkdir ${BUILD_DIR}/code-compare
    sour=$(cat ${PUBLISH_SERVER}/${LAST_RLS} | tail -1 | awk -F"Based-On:" '{ print $2 }')
    dest=$MANIFEST_XML
    export OUTPUT_FOLDER=${BUILD_DIR}/code-compare
    $SCRIPT_PATH/genDeltaPatchDiffFiles.sh ${sour} ${dest}
fi

#Publishing the Release to Release_Server
#if device exist
if [ ! -d "${PUBLISH_SERVER}/${ABS_DEVICE}" ]; then
    echo create prebuildbin folder
    mkdir ${PUBLISH_SERVER}/${ABS_DEVICE}
fi

if [ -d "${PUBLISH_SERVER}/${ABS_DEVICE}/$(basename $BUILD_DIR)-${ABS_TAG}" ]; then
    echo ${PUBLISH_SERVER}/${ABS_DEVICE}/$(basename $BUILD_DIR)-${ABS_TAG} exists already
    echo Publishing Release failed
    exit 1
else
    echo Publishing Release Package: ${BUILD_DIR}
    echo ${BUILD_DIR} TO: ${PUBLISH_SERVER}/${ABS_DEVICE}/$(basename $BUILD_DIR)-${ABS_TAG}
    mkdir ${PUBLISH_SERVER}/${ABS_DEVICE}/$(basename $BUILD_DIR)-${ABS_TAG}
    cp -r ${BUILD_DIR}/* ${PUBLISH_SERVER}/${ABS_DEVICE}/$(basename $BUILD_DIR)-${ABS_TAG}
fi

#saving the build info to $LAST_RLS
echo >> ${PUBLISH_SERVER}/${LAST_RLS} &&
echo ==========$(date)========== >> ${PUBLISH_SERVER}/${LAST_RLS} &&
echo "Target:$TAG_NAME" >> ${PUBLISH_SERVER}/${LAST_RLS} &&
echo "Package:${PUBLISH_SERVER}/${ABS_DEVICE}/$(basename $BUILD_DIR)-${ABS_TAG}" >> ${PUBLISH_SERVER}/${LAST_RLS} &&
echo "Based-On:$MANIFEST_XML" >> ${PUBLISH_SERVER}/${LAST_RLS}

echo All done
