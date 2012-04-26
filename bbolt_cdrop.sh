#!/bin/sh
# 

IDIR=
PLATFORM=
PRODUCT=
RLS=
RC=
LIST=
RPKG_FOLDER="releasepackage"
PREBUILT_FOLDER="prebuilt_bin"
SRC_FOLDER="src"

help() {
    if [ -n "$1" ]; then
	echo "Error: $1"
	echo
    fi
    echo "Usage: bbolt_cdrop.sh <path> <platform> <product> <release> <rc> <list>"
    echo
    echo "bbolt_cdrop is used by buildbolt to publish code drop."
    echo
    exit -1
}



validate_parameters() {
    if [ $# -ne 6 ]; then
	help
    fi

    IDIR=$1
    echo $IDIR
    if [ ! -d "$IDIR" ]; then
	help "Please specify a valid input directory!"
    fi

    LIST=$6
    if [ ! -f "$LIST" ]; then
	help "Please specify a valid release list!"
    fi

    PLATFORM=$2
    PRODUCT=$3
    RLS=$4
    RC=$5
}

bbolt_copy() {

    CDROP_COPY_PATTERN="
    {
        if (NF < 2 || \$2 == \"\")
            \$2 = \$1;
        make_odir = \"dirname \"odir\"/\"\$2\"| xargs mkdir -p\"
        system(make_odir);
        system(\"cp -f \"idir\"/\"\$1\" \"odir\"/\"\$2);
    }
    "

    awk -v idir="$1" -v odir="$2" "$CDROP_COPY_PATTERN" $3
}

validate_parameters $*

ODIR=$IDIR"/"$RPKG_FOLDER"/"$RLS"_"$RC
RPKG_NAME=$PLATFORM"_Android_Platform_"$RLS
RLS_BIN=$RPKG_NAME"_prebuilt_bin"
RLS_SRC=$RPKG_NAME"_src"


if [ ! -d "$ODIR" ]; then
    mkdir -p $ODIR
fi

bbolt_copy $IDIR $ODIR $LIST

cd $ODIR

tar czf $RLS_BIN.tgz $PREBUILT_FOLDER
if [ -f "$RLS_BIN".tgz ]; then
  split -b 100M -d ./"$RLS_BIN".tgz ./"$RLS_BIN".
  rm -rf "$PREBUILT_FOLDER"
fi

tar czf $RLS_SRC.tgz $SRC_FOLDER
if [ -f "$RLS_SRC".tgz ]; then
  split -b 100M -d ./"$RLS_SRC".tgz ./"$RLS_SRC".
  rm -rf "$SRC_FOLDER"
fi
 
