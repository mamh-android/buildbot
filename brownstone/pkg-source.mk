INTERNAL_PROJECTS +=boot/obm/.git
INTERNAL_PROJECTS +=boot/obm/binaries/Wtm_rel_mmp2.bin

KERNEL_BASE_COMMIT:=$(KERNEL_2_6_32_BASE_COMMIT)
UBOOT_BASE_COMMIT:=$(UBOOT_2009RC1_BASE_COMMIT)

ifeq ($(ANDROID_VERSION),gingerbread)
	DROID_BASE:=android-2.3.4_r1
	KERNEL_BASE_COMMIT:=$(KERNEL_2_6_35_BASE_COMMIT)
	UBOOT_BASE_COMMIT:=$(UBOOT_201009_BASE_COMMIT)
else
ifeq ($(ANDROID_VERSION),honeycomb)
	DROID_BASE:=shgit/honeycomb-mr2
	KERNEL_BASE_COMMIT:=$(KERNEL_2_6_35_BASE_COMMIT)
	UBOOT_BASE_COMMIT:=$(UBOOT_201009_BASE_COMMIT)
endif
endif

#format: <file name>:[m|o]:[md5]
#m:means mandatory
#o:means optional
#md5: need to generate md5 sum
PUBLISHING_FILES+=$(ANDROID_VERSION)_RN.pdf:o

publish_RN:
	$(hide)cp $(BOARD)/$(ANDROID_VERSION)_RN.pdf $(OUTPUT_DIR)

pkgsrc: publish_RN
