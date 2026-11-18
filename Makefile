.DEFAULT_GOAL := help

KEYBOARDS := eva01 eva02
ACTION := $(filter build flash slash,$(MAKECMDGOALS))
KEYBOARD := $(word 2,$(MAKECMDGOALS))

ifneq ($(ACTION),)
ifneq ($(words $(MAKECMDGOALS)),2)
$(error Usage: make <build|flash|slash> <eva01|eva02>)
endif
ifneq ($(firstword $(MAKECMDGOALS)),$(ACTION))
$(error Put the action first: make <build|flash|slash> <eva01|eva02>)
endif
ifneq ($(filter $(KEYBOARD),$(KEYBOARDS)),$(KEYBOARD))
$(error Unknown keyboard '$(KEYBOARD)'; choose $(KEYBOARDS))
endif

.PHONY: $(KEYBOARDS)
$(KEYBOARDS):

endif

.PHONY: help build flash slash
help:
	@printf '%s\n' 'Usage: make <command> <keyboard>' '' \
	  'Commands:' \
	  '  build eva01    Compile eva01 firmware' \
	  '  flash eva01    Compile and flash eva01 firmware' \
	  '  slash eva01    Alias for flash' \
	  '  help           Show this help (default)' '' \
	  'Keyboards: $(KEYBOARDS)' \
	  'Requires an existing QMK environment and the setup documented in README.md.'

build:
	qmk compile -kb themakunga/$(KEYBOARD) -km nicolas

flash:
	qmk flash -kb themakunga/$(KEYBOARD) -km nicolas

slash: flash
