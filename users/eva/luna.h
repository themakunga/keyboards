#pragma once
#include <stdbool.h>
#include <stdint.h>

typedef struct {
    uint8_t wpm, mods, jumps;
    bool caps, space, awake;
} eva_pet_state_t;

void render_luna(const eva_pet_state_t *pet);
