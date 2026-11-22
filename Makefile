.DEFAULT_GOAL := help

QMK_HOME ?= $(HOME)/qmk_firmware

KEYBOARDS := eva01 eva02
BOARD_eva01 := sofle/v2
BOARD_eva02 := corne/v2
ACTION := $(filter build flash,$(MAKECMDGOALS))
KEYBOARD := $(word 2,$(MAKECMDGOALS))

ifneq ($(ACTION),)
ifneq ($(words $(MAKECMDGOALS)),2)
$(error Usage: make <build|flash> <eva01|eva02>)
endif
ifneq ($(firstword $(MAKECMDGOALS)),$(ACTION))
$(error Put the action first: make <build|flash> <eva01|eva02>)
endif
ifneq ($(filter $(KEYBOARD),$(KEYBOARDS)),$(KEYBOARD))
$(error Unknown keyboard '$(KEYBOARD)'; choose $(KEYBOARDS))
endif

.PHONY: $(KEYBOARDS)
$(KEYBOARDS):

endif

ifneq ($(filter setup update,$(MAKECMDGOALS)),)
ifneq ($(words $(MAKECMDGOALS)),1)
$(error Usage: make setup or make update)
endif
endif

.PHONY: help setup update build flash
help:
	@printf '%s\n' 'Usage: make <command> [keyboard]' '' \
	  'Commands:' \
	  '  setup              Prepare QMK checkout and configure userspace' \
	  '  update             Refresh local keyboard links in QMK' \
	  '  build eva01        Compile the shared firmware' \
	  '  flash eva01        Compile and flash the connected half' \
	  '  help               Show this help (default)' '' \
	  'Keyboards: $(KEYBOARDS)' \
	  'Each keyboard uses one image for both halves; run flash once per connected half.' \
	  'Requires QMK CLI and Git; setup creates a missing firmware checkout.' \
	  'Override the checkout with QMK_HOME=/path/to/qmk_firmware.'

setup:
	QMK_HOME="$(QMK_HOME)" sh scripts/setup-qmk.sh
	qmk config user.qmk_home="$(QMK_HOME)"
	qmk config user.overlay_dir="$(CURDIR)"
	qmk userspace-doctor

update:
	QMK_HOME="$(QMK_HOME)" sh scripts/link-keyboards.sh

build:
	qmk compile -kb $(BOARD_$(KEYBOARD)) -km themakunga_$(KEYBOARD)

flash:
	qmk flash -kb $(BOARD_$(KEYBOARD)) -km themakunga_$(KEYBOARD)
