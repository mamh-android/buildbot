export ABS_BOARD=dkbtd
export ABS_DROID_BRANCH=ics
export ABS_PRODUCT_NAME=dkbtd
export PATH=/usr/lib/jvm/java-6-sun/bin/:$PATH
export ABS_BUILDHOST_DEF=buildhost2.def
export ABS_DROID_VARIANT=eng
export ABS_MANIFEST_BRANCH="$ABS_BOARD-$ABS_DROID_BRANCH"
export ABS_UNIQUE_MANIFEST_BRANCH=1

core/autobuild.sh $*
