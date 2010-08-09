#check if the required variables have been set.
$(call check-variables,BUILD_VARIANTS)
BOOT_SRC_DIR:=boot
BOOT_OUT_DIR:=$(BOOT_SRC_DIR)/out
UBOOT:=u-boot.bin
OBM_NTIM_1:=ntim_mmp2_nand_bbu_ddr.bin
OBM_DESC_1:=ntim_mmp2_emmc_ddr_elipda_512m.txt
OBM_NTLOADER_1:=MMP2_NTLOADER_3_2_15.bin
WTM_1:=WtmUnresetPJ4.bin
PARTITION_BIN:=partition.bin
PARTITION_DESC:=partition.txt
OBM_NTIM_2:=ntim_mmp2_nand_bbu_ddr.bin
OBM_DESC_2:=ntim_mmp2_nand_bbu_ddr_elipda_512m.txt
OBM_NTLOADER_2:=MMP2_NTLOADER_3_2_15.bin
WTM_2:=WtmUnresetPJ4.bin

#$1:build variant
define define-build-uboot-obm
#format: <file name>:[m|o]:[md5]
#m:means mandatory
#o:means optional
#md5: need to generate md5 sum
PUBLISHING_FILES+=$(1)/$(UBOOT):m:md5



.PHONY:build_uboot_obm_$(1)
build_uboot_obm_$(1):
	$$(log) "starting($(1)) to build uboot and obm"
	$$(hide)cd $$(SRC_DIR)/$$(BOOT_SRC_DIR) && \
	make all
	$$(hide)mkdir -p $$(OUTPUT_DIR)/$(1)
	$$(hide)mkdir -p $$(OUTPUT_DIR)/$(1)/nand
	$$(hide)mkdir -p $$(OUTPUT_DIR)/$(1)/emmc

	$$(log) "start to copy uboot and obm files"
	$$(hide)cp $$(SRC_DIR)/$$(BOOT_OUT_DIR)/u-boot.bin $$(OUTPUT_DIR)/$(1)
	$$(log) "  done."

endef

$(foreach bv, $(BUILD_VARIANTS), $(eval $(call define-build-uboot-obm,$(bv)) ) )

.PHONY:clean_uboot_obm
clean_uboot_obm:
	$(log) "cleaning uboot and obm..."
	$(hide)cd $(SRC_DIR)/$(BOOT_SRC_DIR) && \
	make clean
	$(log) "    done."




