"""Host checks for the actual OLED module; requires a C compiler."""
import os
import json
import re
import subprocess
import tempfile
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
keymap_root = repo / 'keyboards/sofle/v2/keymaps/themakunga_eva01'
root = repo / 'users/eva'
board = json.loads((keymap_root.parents[1] / 'keyboard.json').read_text())
assert board['keyboard_name'] == 'Sofle v2 RGB' and board['maintainer'] == 'themakunga'
assert board['development_board'] == 'promicro'
assert board['matrix_pins'] == {'cols': ['F6', 'F7', 'B1', 'B3', 'B2', 'B6'],
                               'rows': ['C6', 'D7', 'E6', 'B4', 'B5']}
assert len(board['layouts']['LAYOUT']['layout']) == 60
assert board['split']['serial']['pin'] == 'D2' and board['ws2812']['pin'] == 'D3'
assert board['rgb_matrix']['split_count'] == [36, 36]
source = (root / 'eva_oled.c').read_text()

keymap = (keymap_root / 'keymap.c').read_text()
blocks = re.findall(r'\[([012])\] = LAYOUT\((.*?)\n    \)', keymap, re.S)
assert len(blocks) == 3
presses = [('MS_BTN1', 'MS_BTN2'), ('KC_MUTE', 'KC_HOME'), ('KC_MUTE', 'G(C(KC_Q))')]
for index, body in blocks:
    keys = [key.strip() for key in body.split(',')]
    assert len(keys) == 60
    assert tuple(keys[42:44]) == presses[int(index)]
    if index == '0':
        assert keys[24] == 'KC_LCTL' and keys[36] == 'KC_LSFT' and keys[49] == 'KC_RSFT'
        assert keys[50:54] == ['C(KC_S)', 'KC_LALT', 'MO(1)', 'KC_LGUI']
        assert keys[56] == 'MO(2)'
        assert keys[55] == 'TD(TD_SPC_ENT)'
    else:
        assert keys[52] == keys[53] == keys[56] == 'KC_TRNS'
encoders = re.findall(r'ENCODER_CCW_CW\(((?:[^()]|\([^()]*\))*)\)', keymap)
assert [re.sub(r'\s+', '', value) for value in encoders] == [
    'S(KC_UP),S(KC_DOWN)', 'S(KC_LEFT),S(KC_RGHT)',
    'A(KC_UP),A(KC_DOWN)', 'A(KC_LEFT),A(KC_RGHT)',
    'KC_VOLD,KC_VOLU', 'KC_BRMD,KC_BRMU',
]
for family, name in [('sofle', 'eva01'), ('corne', 'eva02')]:
    keymap_path = repo / f'keyboards/{family}/v2/keymaps/themakunga_{name}'
    code = (keymap_path / 'keymap.c').read_text()
    assert 'return is_keyboard_left() ? OLED_ROTATION_0 : OLED_ROTATION_270;' in code
    for callback in ['eva_oled_init();', 'eva_oled_record(keycode, record);',
                     'eva_oled_housekeeping();', 'return eva_oled_render();']:
        assert callback in code
    assert 'USER_NAME := eva' in (keymap_path / 'rules.mk').read_text()
assert 'SRC += eva_oled.c bongo/bongo_cat.c' in (root / 'rules.mk').read_text()
assert '#define SPLIT_TRANSACTION_IDS_USER EVA_OLED_SYNC' in (root / 'config.h').read_text()
assert 'VIA_ENABLE = no' in (keymap_root / 'rules.mk').read_text()

known = {'KC_A': 4, 'KC_Z': 29, 'KC_1': 30, 'KC_0': 39, 'KC_F1': 58, 'KC_F12': 69}
for number, name in enumerate(sorted(set(re.findall(r'\b(?:KC|MS|RM)_\w+', source)) - known.keys()), 256):
    known[name] = number
header = '''
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#define PROGMEM
#define pgm_read_byte(p) (*(const unsigned char *)(p))
#define pgm_read_word(p) (*(const uint16_t *)(p))
#define MO(n) (0x5000 + (n))
#define EVA_OLED_SYNC 1
#define MOD_MASK_GUI 0x88
#define MOD_MASK_CTRL 0x11
#define MOD_MASK_ALT 0x44
#define MOD_MASK_SHIFT 0x22
typedef struct { struct { bool pressed; } event; } keyrecord_t;
static uint32_t now, layer_state = 1, default_layer_state = 1;
static bool master = true, left = false;
static uint8_t mods, weak_mods;
static bool is_keyboard_master(void) { return master; }
static bool is_keyboard_left(void) { return left; }
static uint32_t timer_read32(void) { return now; }
static uint32_t timer_elapsed32(uint32_t start) { return now - start; }
static uint8_t get_mods(void) { return mods; }
static uint8_t get_weak_mods(void) { return weak_mods; }
static uint8_t get_highest_layer(uint32_t value) {
    uint8_t result = 0;
    while (value >>= 1) ++result;
    return result;
}
static void oled_set_cursor(uint8_t x, uint8_t y);
static void oled_write(const char *text, bool inverted);
static void oled_write_pixel(uint8_t x, uint8_t y, bool on);
static void oled_write_raw_P(const char *data, uint16_t size);
'''
header += '\n'.join(f'#define {name} {value}' for name, value in known.items())
transactions = '''
static unsigned sends;
static void (*receiver)(uint8_t, const void *, uint8_t, void *);
static void transaction_register_rpc(int id, void (*fn)(uint8_t, const void *, uint8_t, void *)) {
    (void)id; receiver = fn;
}
static bool transaction_rpc_send(int id, uint8_t size, const void *data) {
    (void)id; (void)size; (void)data; ++sends; return false;
}
'''
test = r'''
#include <assert.h>
#include <stdio.h>
#include "eva_oled.c"
#include "bongo/bongo_cat.c"
#include "font_ascii.c"
static unsigned pixels;
static uint8_t cursor_row, cursor_col;
static char lines[16][6];
static bool inverse[16][6];
static bool canvas[128][32];
static void oled_set_cursor(uint8_t x, uint8_t y) {
    assert(x < 5 && y < 16); cursor_row = y; cursor_col = x;
}
static void oled_write(const char *text, bool inverted) {
    assert(cursor_col + strlen(text) <= 5);
    while (*text) {
        assert(*text >= 32 && *text <= 126);
        lines[cursor_row][cursor_col] = *text;
        inverse[cursor_row][cursor_col] = inverted;
        for (uint8_t x = 0; x < 6; ++x)
            for (uint8_t y = 0; y < 8; ++y)
                canvas[cursor_row*8+y][cursor_col*6+x] =
                    !!(font[(*text-32)*6+x] & (1 << y)) ^ inverted;
        ++cursor_col;
        ++text;
    }
}
static void oled_write_pixel(uint8_t x, uint8_t y, bool on) {
    assert(x < 32 && y < 128); canvas[y][x] = on; ++pixels;
}
static void oled_write_raw_P(const char *data, uint16_t size) {
    assert(cursor_col == 0 && cursor_row == 0 && size == 96);
    for (unsigned y = 0; y < 24; ++y)
        for (unsigned x = 0; x < 32; ++x)
            canvas[y][x] = ((uint8_t)data[y/8*32+x] >> (y%8)) & 1;
}
int main(void) {
    char name[6];
    label(KC_AT, name); assert(!strcmp(name, "@"));
    label(MS_BTN2, name); assert(!strcmp(name, "RClk"));
    label(RM_NEXT, name); assert(!strcmp(name, "FX+"));
    label(KC_A, name); assert(!strcmp(name, "A"));
    label(KC_0, name); assert(!strcmp(name, "0"));
    label(KC_F12, name); assert(!strcmp(name, "F12"));
    label(0xFFFF, name); assert(!strcmp(name, "#FFFF"));
    eva_oled_init(); assert(receiver);
    keyrecord_t event = {.event.pressed = true};
    now = 100; eva_oled_record(KC_A, &event);
    eva_oled_record(KC_AT, &event);
    eva_oled_record(KC_HOME, &event);
    assert(!strcmp(state.keys[0], "Home") && !strcmp(state.keys[2], "A"));
    event.event.pressed = false; eva_oled_record(KC_Z, &event);
    assert(!strcmp(state.keys[0], "Home"));
    layer_state = 4; mods = MOD_MASK_CTRL; weak_mods = MOD_MASK_GUI;
    eva_oled_housekeeping(); assert(state.layer == 2 && state.frame != 0);
    assert(sends == 1);
    eva_oled_housekeeping(); assert(sends == 1);
    now += 50; eva_oled_housekeeping(); assert(sends == 2);
    now += 220; eva_oled_housekeeping(); assert(state.frame == 0);
    eva_oled_render(); assert(pixels);
    assert(!strcmp(lines[4], "Home ") && !strcmp(lines[5], "@    ") && !strcmp(lines[6], "A    "));
    unsigned previous = pixels; left = true; eva_oled_render(); assert(pixels == previous);
    left = false; master = false; event.event.pressed = true;
    eva_oled_record(KC_Z, &event); assert(!strcmp(state.keys[0], "Home"));
    display_state_t packet = {.layer = 1, .frame = 2, .keys = {"B"}};
    receiver(1, &packet, 0, NULL); assert(state.layer == 2);
    receiver(sizeof(packet), &packet, 0, NULL); assert(state.layer == 1);
    eva_oled_render(); assert(!strcmp(lines[4], "B    "));
    assert(!strcmp(lines[5], "     ") && !strcmp(lines[6], "     "));
    for (uint8_t layer = 0; layer < 3; ++layer) {
        state.layer = layer;
        eva_oled_render();
        for (uint8_t plane = 0; plane < 3; ++plane) {
            assert(canvas[62+4*plane][10] && canvas[62+4*plane][21]);
            assert(canvas[62+4*plane][16] == (layer == 2-plane));
            assert(!canvas[60+4*plane][16]);
        }
    }
    assert(sizeof(waiting_frame) == 96);
    assert(memcmp(animation_frames[0], animation_frames[1], 96));
    const char *frames[] = {waiting_frame, animation_frames[0], animation_frames[1], ready_frame};
    for (uint8_t frame = 0; frame < 4; ++frame) {
        state.frame = frame;
        eva_oled_render();
        // The complete portrait sprite survives the status overlays.
        for (unsigned y = 0; y < 24; ++y)
            for (unsigned x = 0; x < 32; ++x)
                assert(canvas[y][x] == (((uint8_t)frames[frame][y/8*32+x] >> (y%8)) & 1));
    }
    const uint8_t masks[] = {MOD_MASK_CTRL, MOD_MASK_GUI, MOD_MASK_ALT, MOD_MASK_SHIFT};
    // Both sides of every modifier and all combinations invert only their own icons.
    for (unsigned mods = 0; mods < 256; ++mods) {
        state.mods = mods;
        eva_oled_render();
        for (uint8_t i = 0; i < 4; ++i)
            for (uint8_t y = 0; y < 12; ++y)
                for (uint8_t x = 0; x < 12; ++x)
                    assert(canvas[76+13*i+y][10+x] ==
                        (!!(modifier_icons[i][y] & (1 << (11-x))) ^ !!(mods & masks[i])));
    }
    puts("OK: labels, history, modifiers, layer, portrait sprite, pixel bounds, RPC, retry throttle");
}
'''
with tempfile.TemporaryDirectory() as directory:
    tmp = Path(directory)
    (tmp / 'mock.h').write_text(header)
    (tmp / 'transactions.h').write_text(transactions)
    (tmp / 'progmem.h').write_text('#pragma once\n')
    (tmp / 'test.c').write_text(test)
    binary = tmp / 'test'
    subprocess.run([os.environ.get('CC', 'cc'), '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-DNO_ACTION_ONESHOT', '-DQMK_KEYBOARD_H="mock.h"', '-I', str(tmp), '-I', str(root),
                    str(tmp / 'test.c'), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
