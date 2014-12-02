#!/bin/bash
#
# Need environment variables:
# PUBLISH_FILE
# PUBLISH_SERVER

# Command usage:
#genPreBuildBin.sh -t <Tag_Name> -m <manifest xml>

export PUBLISH_FILE=${PUBLISH_FILE:-flash}
export PUBLISH_FILE=${PUBLISH_FILE:-//sh1sbak004/APSE/}

#script path
SCRIPT_PATH=$(dirname `readlink -f $0`)/core

case "$1" in
    "-t") TAG_NAME=$2
          echo "TAG_NAME= $2"
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

tar_device() {
    dev=$1
    mkdir $BUILD_DIR/prebuildbin/$(basename $dev)
    tar_file=$BUILD_DIR/prebuildbin/$(basename $dev)/$TAG_NAME\_Android_Platform_prebuilt_bin.tgz
    cd $BUILD_DIR && tar czf $tar_file $(basename $dev)/$PUBLISH_FILE
    split -b 170M -d $tar_file $tar_file
    cd $BUILD_DIR && md5sum prebuildbin/$(basename $dev)/$TAG_NAME\_Android_Platform_prebuilt_bin.tgz > $BUILD_DIR/prebuildbin/$(basename $dev)/checksum.md5
}

#if prebuildbin exist
if [ -d "$BUILD_DIR/prebuildbin" ]; then
    echo $BUILD_DIR/prebuildbin exists already
    exit 1
else
    echo create prebuildbin folder
    mkdir $BUILD_DIR/prebuildbin
fi

device_list=$(ls -d $BUILD_DIR/pxa*)

#if PUBLISH_FILE exist
for i in $device_list; do
    if [ ! -d "$i/$PUBLISH_FILE" ]; then
        echo $i/$PUBLISH_FILE not exists
        exit 1
    fi
done

for i in $device_list; do
    echo Start tar $i ...
    tar_device $i
done

echo All done
