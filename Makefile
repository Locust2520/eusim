# EU Simulator — BlocksDS build
NAME          := EU_Simulator
GAME_TITLE    := EU Simulator
GAME_SUBTITLE := Le stage de ta vie
GAME_AUTHOR   := Parodie non officielle
GAME_ICON     := assets/icon.bmp
SOURCEDIRS    := source
INCLUDEDIRS   := include
NITROFSDIR    := nitrofs
CFLAGS        := -Wno-format-truncation -Wno-unused-function
ARM7ELF       = $(BLOCKSDS)/sys/arm7/main_core/arm7_dswifi_maxmod.elf
LIBS          := -ldswifi9 -lnds9
LIBDIRS       += $(BLOCKSDS)/libs/dswifi
ifeq ($(QUICK),1)
CFLAGS        += -DQUICKSTART -DSCEN=$(SCEN)
ifneq ($(QLANG),)
CFLAGS        += -DQLANG=\"$(QLANG)\"
endif
NAME          := eusim_quick
CFLAGS        += $(QEXTRA)
endif
include $(BLOCKSDS)/sys/default_makefiles/rom_arm9/Makefile
