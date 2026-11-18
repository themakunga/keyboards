#pragma once
#include QMK_KEYBOARD_H

void eva_oled_init(void);
void eva_oled_record(uint16_t keycode, keyrecord_t *record);
void eva_oled_housekeeping(void);
bool eva_oled_render(void);
