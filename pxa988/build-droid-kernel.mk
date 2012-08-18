#check if the required variables have been set.
$(call check-variables, ABS_SOC ABS_DROID_BRANCH ABS_DROID_VARIANT)

include $(ABS_SOC)/tools-list.mk

MY_SCRIPT_DIR:=$(TOP_DIR)/$(ABS_SOC)

DROID_TYPE:=release
DROID_VARIANT:=$(ABS_DROID_VARIANT)

KERNELSRC_TOPDIR:=kernel
DROID_OUT:=out/target/product

MAKE_EXT4FS := out/host/linux-x86/bin/make_ext4fs

define define-clean-droid-kernel-target
tw:=$$(subst :,  , $(1) )
product:=$$(word 1, $$(tw) )
device:=$$(word 2, $$(tw) )
.PHONY:clean_droid_kernel_$$(product)
clean_droid_kernel_$$(product): clean_droid_$$(product) clean_kernel_$$(product)

.PHONY:clean_droid_$$(product)
clean_droid_$$(product): private_product:=$$(product)
clean_droid_$$(product): private_device:=$$(device)
clean_droid_$$(product):
	$(log) "clean android ..."
	$(hide)cd $(SRC_DIR) && \
	source ./build/envsetup.sh &&
	chooseproduct $(private_product) && choosetype $(DROID_TYPE) && choosevariant $(DROID_VARIANT) && \
	make clean
	$(log) "    done"

.PHONY:clean_kernel_$$(product)
clean_kernel_$$(product): private_product:=$$(product)
clean_kernel_$$(product): private_device:=$$(device)
clean_kernel_$$(product):
	$(log) "clean kernel ..."
	$(hide)cd $(SRC_DIR)/$(KERNELSRC_TOPDIR) && make clean
	$(log) "    done"
endef

#we need first build the android, so we get the root dir 
# and then we build the kernel images with the root dir and get the package of corresponding modules
# and then we use those module package to build corresponding android package.

define define-build-droid-kernel-target
tw:=$$(subst :,  , $(1) )
product:=$$(word 1, $$(tw) )
device:=$$(word 2, $$(tw) )
.PHONY:build_droid_kernel_$$(product)
build_droid_kernel_$$(product): build_kernel_$$(product) build_droid_$$(product)
endef

MAKE_JOBS := 8
export KERNEL_TOOLCHAIN_PREFIX
export MAKE_JOBS

#$1:kernel_config
#$2:build variant
define define-build-kernel-target
tw:=$$(subst :,  , $(1) )
product:=$$(word 1, $$(tw) )
device:=$$(word 2, $$(tw) )
.PHONY: build_kernel_$$(product)

#make sure that PUBLISHING_FILES_XXX is a simply expanded variable
PUBLISHING_FILES+=$$(product)/uImage:m:md5
PUBLISHING_FILES+=$$(product)/uImage-mt:o:md5
PUBLISHING_FILES+=$$(product)/vmlinux:o:md5
PUBLISHING_FILES+=$$(product)/System.map:o:md5
build_kernel_$$(product): private_product:=$$(product)
build_kernel_$$(product): private_device:=$$(device)
build_kernel_$$(product): output_dir
	$(log) "[$$(private_product)]starting to build kernel ..."
	$(hide)cd $(SRC_DIR) && \
	source ./build/envsetup.sh && \
	chooseproduct $$(private_product) && choosetype $(DROID_TYPE) && choosevariant $(DROID_VARIANT) && \
	cd $(SRC_DIR)/$(KERNELSRC_TOPDIR) && \
	make kernel
	$(log) "[$$(private_product)]starting to build modules ..."
	$(hide)cd $(SRC_DIR) && \
	source ./build/envsetup.sh && \
	chooseproduct $$(private_product) && choosetype $(DROID_TYPE) && choosevariant $(DROID_VARIANT) && \
	cd $(SRC_DIR)/$(KERNELSRC_TOPDIR) && \
	make modules
	$(hide)mkdir -p $(OUTPUT_DIR)/$$(private_product)
	$(hide)cp $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/kernel/uImage $(OUTPUT_DIR)/$$(private_product)/
	$(hide)cp $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/kernel/uImage $(OUTPUT_DIR)/$$(private_product)/uImage-mt
	$(hide)cp $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/kernel/vmlinux $(OUTPUT_DIR)/$$(private_product)/
	$(hide)cp $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/kernel/System.map $(OUTPUT_DIR)/$$(private_product)/
	$(hide)if [ -d $(OUTPUT_DIR)/$$(private_product)/modules ]; then rm -fr $(OUTPUT_DIR)/$$(private_product)/modules; fi &&\
	mkdir -p $(OUTPUT_DIR)/$$(private_product)/modules
	$(hide)cp -af $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/kernel/modules  $(OUTPUT_DIR)/$$(private_product)/
	$(log) "  done."
endef

##!!## build rootfs for android, make -j4 android, copy root, copy ramdisk/userdata/system.img to outdir XXX
#$1:build variant
define define-build-droid-target
tw:=$$(subst :,  , $(1) )
product:=$$(word 1, $$(tw) )
device:=$$(word 2, $$(tw) )
.PHONY: build_droid_$$(product)
build_droid_$$(product): private_product:=$$(product)
build_droid_$$(product): private_device:=$$(device)
build_droid_$$(product): build_kernel_$$(product)
	$(log) "[$$(private_product)] building android source code ..."
	$(hide)cd $(SRC_DIR) && \
	source ./build/envsetup.sh && \
	chooseproduct $$(private_product) && choosetype $(DROID_TYPE) && choosevariant $(DROID_VARIANT) && \
	make -j8 && \
	tar zcf $(OUTPUT_DIR)/$$(private_product)/modules.tgz -C $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/kernel modules && \
	tar zcf $(OUTPUT_DIR)/$$(private_product)/symbols_system.tgz -C $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/ symbols && \
	cd vendor/marvell/generic/security && \
	git reset --hard HEAD && git checkout shgit/security-1_0 && mm -B && \
	cd $(SRC_DIR)/vendor/marvell/generic/security/wtpsp/drv/src && \
	make KDIR=$(SRC_DIR)/kernel/kernel ARCH=arm CROSS_COMPILE=arm-eabi- M=$(PWD) && cp -a geu.ko $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/system/lib/modules && \
	cd $(SRC_DIR)/$(DROID_OUT)/$$(private_device) && \
	tar zcvf $(OUTPUT_DIR)/$$(private_product)/security.tgz system/lib/libparseTim.so system/lib/libwtpsp.so system/lib/libwtpsp_ss.so system/lib/modules/geu.ko && \
	cd $(SRC_DIR)

	$(hide)if [ -d $(OUTPUT_DIR)/$$(private_product)/root ]; then rm -fr $(OUTPUT_DIR)/$$(private_product)/root; fi
	$(hide)echo "  copy root directory ..." 
	$(hide)mkdir -p $(OUTPUT_DIR)/$$(private_product)
	$(hide)cp -p -r $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/root $(OUTPUT_DIR)/$$(private_product)
	$(hide)cp -p -r $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/ramdisk.img $(OUTPUT_DIR)/$$(private_product)
	$(hide)cp -p -r $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/ramdisk.img $(OUTPUT_DIR)/$$(private_product)/ramdisk-recovery.img
	$(hide)cp -p -r $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/userdata.img $(OUTPUT_DIR)/$$(private_product)
	$(hide)cp -p -r $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/system.img $(OUTPUT_DIR)/$$(private_product)
	$(hide)cp -p -r $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/system/build.prop $(OUTPUT_DIR)/$$(private_product)
	$(hide)cp -p -r $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/telephony/* $(OUTPUT_DIR)/$$(private_product)/
	$(hide)if [ -e $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/radio.img ]; then cp -p -r $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/radio.img $(OUTPUT_DIR)/$$(private_product)/; fi
	$(log) "  done"

	$(log) "[$$(private_product)] rebuilding android source code with eng for tools ..."
	$(hide)cd $(SRC_DIR) && \
	source ./build/envsetup.sh && \
	chooseproduct $$(private_product) && choosetype $(DROID_TYPE) && choosevariant eng && \
	 make -j8

	$(hide)if [ -d $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/tools ]; then rm -fr $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/tools; fi
	$(hide)echo "  copy and make tools image ..."
	$(hide)mkdir -p $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/tools/bin
	$(hide)cd $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/symbols/system && \
	cp -af $(TOOLS_LIST) $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/tools/bin
	$(hide)$(SRC_DIR)/$(MAKE_EXT4FS) -s -l 65536k -b 1024 -L tool $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/tools.img $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/tools
	$(hide)cp -p -r $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/tools.img $(OUTPUT_DIR)/$$(private_product)/
	tar zcvf $(OUTPUT_DIR)/$$(private_product)/tools.tgz -C $(SRC_DIR)/$(DROID_OUT)/$$(private_device) tools

##!!## first time publish: all for two
PUBLISHING_FILES+=$$(product)/userdata.img:m:md5
PUBLISHING_FILES+=$$(product)/system.img:m:md5
PUBLISHING_FILES+=$$(product)/ramdisk.img:m:md5
PUBLISHING_FILES+=$$(product)/symbols_system.tgz:o:md5
PUBLISHING_FILES+=$$(product)/ramdisk-recovery.img:o:md5
PUBLISHING_FILES+=$$(product)/build.prop:o:md5
PUBLISHING_FILES+=$$(product)/modules.tgz:o:md5
PUBLISHING_FILES+=$$(product)/tools.img:o:md5
PUBLISHING_FILES+=$$(product)/tools.tgz:o:md5
PUBLISHING_FILES+=$$(product)/security.tgz:o:md5

PUBLISHING_FILES+=$$(product)/pxafs.img:o:md5
PUBLISHING_FILES+=$$(product)/pxa_symbols.tgz:o:md5
PUBLISHING_FILES+=$$(product)/radio.img:o:md5

PUBLISHING_FILES+=$$(product)/WK_CP_2CHIP_SPRW_NVM.mdb:o:md5
PUBLISHING_FILES+=$$(product)/WK_CP_2CHIP_SPRW_DIAG.mdb:o:md5
PUBLISHING_FILES+=$$(product)/Boerne_DIAG.mdb.txt:o:md5
PUBLISHING_FILES+=$$(product)/ReliableData.bin:o:md5
ifeq ($(product),pxa988dkb_def)
PUBLISHING_FILES+=$$(product)/Arbel_DIGRF3_NVM.mdb:o:md5
PUBLISHING_FILES+=$$(product)/Arbel_DIGRF3.bin:o:md5
PUBLISHING_FILES+=$$(product)/Arbel_DIGRF3_DIAG.mdb:o:md5
PUBLISHING_FILES+=$$(product)/Arbel_DKB_SKWS.bin:o:md5
PUBLISHING_FILES+=$$(product)/Arbel_DKB_SKWS_NVM.mdb:o:md5
PUBLISHING_FILES+=$$(product)/Arbel_DKB_SKWS_DIAG.mdb:o:md5
PUBLISHING_FILES+=$$(product)/TTD_M06_AI_A0_Flash.bin:o:md5
PUBLISHING_FILES+=$$(product)/TTD_M06_AI_A1_Flash.bin:o:md5
PUBLISHING_FILES+=$$(product)/TTD_M06_AI_Y0_Flash.bin:o:md5
PUBLISHING_FILES+=$$(product)/WK_CP_2CHIP_SPRW.bin:o:md5
PUBLISHING_FILES+=$$(product)/WK_M08_AI_Y1_removelo_Y0_Flash.bin:o:md5
endif
endef

define define-build-droid-otapackage
tw:=$$(subst :,  , $(1) )
product:=$$(word 1, $$(tw) )
device:=$$(word 2, $$(tw) )
.PHONY: build_droid_otapackage_$$(product)
build_droid_otapackage_$$(product): private_product:=$$(product)
build_droid_otapackage_$$(product): private_device:=$$(device)
build_droid_otapackage_$$(product): build_uboot_obm_$$(product)
	$(log) "[$$(private_product)] building android OTA package ..."
	$(hide)cd $(SRC_DIR) && \
	source ./build/envsetup.sh && \
	chooseproduct $$(private_product) && choosetype $(DROID_TYPE) && choosevariant $(DROID_VARIANT) && \
	make mrvlotapackage -j$(MAKE_JOBS)
	$(hide)echo "  copy OTA package ..."
	$(hide)cp -p -r $(SRC_DIR)/$(DROID_OUT)/$$(private_device)/$$(private_product)-ota-mrvl.zip $(OUTPUT_DIR)/$$(private_product)
	$(log) "  done for OTA package build."
PUBLISHING_FILES+=$$(product)/$$(product)-ota-mrvl.zip:o:md5
endef

$(foreach bv,$(ABS_BUILD_DEVICES), $(eval $(call define-build-droid-kernel-target,$(bv)) )\
				$(eval $(call define-build-kernel-target,$(bv)) ) \
				$(eval $(call define-build-droid-target,$(bv)) ) \
				$(eval $(call define-clean-droid-kernel-target,$(bv)) ) \
)
