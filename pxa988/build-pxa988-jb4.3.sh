export ABS_SOC=pxa988
export ABS_DROID_BRANCH=jb4.3
export PATH=/usr/lib/jvm/java-6-sun/bin/:$PATH
if [ -z "ABS_BUILDHOST_DEF" ]; then
    ABS_BUILDHOST_DEF=buildhost.def
fi
export ABS_BUILDHOST_DEF

export ABS_UNIQUE_MANIFEST_BRANCH=1

export ABS_BUILD_DEVICES="pxa988t7_def:pxa988t7 pxa1088t7_def:pxa1088t7"
