SRC += eva_oled.c
ifeq ($(EVA_SIDE),right)
OPT_DEFS += -DEVA_RIGHT
SRC += luna.c
else
WPM_ENABLE = yes
endif
