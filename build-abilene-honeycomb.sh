export ABS_BOARD=abilene
export ABS_DROID_BRANCH=honeycomb
export ABS_PRODUCT_NAME=MMP3
export ABS_BUILDHOST_DEF=buildhost2.def
export ABS_DROID_VARIANT=userdebug
export PATH=/usr/lib/jvm/java-6-sun/bin/:$PATH
export ABS_UNIQUE_MANIFEST_BRANCH=1

core/autobuild.sh $*
