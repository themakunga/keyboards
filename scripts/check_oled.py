"""Host checks for the actual OLED module; requires a C compiler."""
import os
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

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
# Pin the five rasterized font glyphs, including their order and pixel geometry.
icon_rows = [int(value, 16) for value in re.findall(r'0x([0-9A-F]+)', (root / 'icons.h').read_text())]
assert len(icon_rows) == 5 * 14 and all(value < 1 << 14 for value in icon_rows)
assert hashlib.sha256(b''.join(value.to_bytes(2, 'big') for value in icon_rows)).hexdigest() == '198b22c80512989fcf0cd615957a28e9e38cd28d3595c6c7e381d8ff666b60d4'


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
        assert keys[50:54] == ['C(KC_S)', 'KC_LALT', 'KC_LGUI', 'MO(1)']
        assert keys[56] == 'MO(2)'
        assert keys[55] == 'TD(TD_SPC_ENT)'
    else:
        assert keys[52] == keys[53] == keys[56] == 'KC_TRNS'
        assert keys[54:56] == ['KC_ENT', 'KC_ENT']
ns = {'svg': 'http://www.w3.org/2000/svg'}
svg = ET.parse(repo / 'docs/eva01-layout.svg')
for layer in range(3):
    for index, action, label in [(52, 'KC_LGUI', 'Mac'), (53, 'MO(1)', 'L2')]:
        key = action if layer == 0 else 'KC_TRNS'
        title = f'QMK {layer}, posición {index}: {key}; acción {action}'
        group = next(g for g in svg.findall('.//svg:g', ns)
                     if g.find('svg:title', ns) is not None and g.find('svg:title', ns).text == title)
        assert [t.text for t in group.findall('svg:text', ns)] == [label]
for layer in (1, 2):
    for index in (54, 55):
        title = f'QMK {layer}, posición {index}: KC_ENT; acción KC_ENT'
        group = next(g for g in svg.findall('.//svg:g', ns)
                     if g.find('svg:title', ns) is not None and g.find('svg:title', ns).text == title)
        assert [t.text for t in group.findall('svg:text', ns)] == ['Enter']
encoders = re.findall(r'ENCODER_CCW_CW\(((?:[^()]|\([^()]*\))*)\)', keymap)
assert [re.sub(r'\s+', '', value) for value in encoders] == [
    'S(KC_UP),S(KC_DOWN)', 'S(KC_LEFT),S(KC_RGHT)',
    'A(KC_UP),A(KC_DOWN)', 'A(KC_LEFT),A(KC_RGHT)',
    'KC_VOLD,KC_VOLU', 'KC_BRMD,KC_BRMU',
]
for family, name in [('sofle', 'eva01'), ('corne', 'eva02')]:
    keymap_path = repo / f'keyboards/{family}/v2/keymaps/themakunga_{name}'
    code = (keymap_path / 'keymap.c').read_text()
    assert 'return OLED_ROTATION_270;' in code
    for callback in ['eva_oled_init();',
                     'eva_oled_housekeeping();', 'return eva_oled_render();']:
        assert callback in code
    assert 'USER_NAME := eva' in (keymap_path / 'rules.mk').read_text()
assert 'SRC += eva_oled.c' in (root / 'rules.mk').read_text()
assert 'luna.c' in (root / 'rules.mk').read_text()
luna_bytes = bytes(int(value, 16) for value in re.findall(r'0x([0-9a-f]+)', (root / 'luna.c').read_text()))
assert len(luna_bytes) == 960
assert hashlib.sha256(luna_bytes).hexdigest() == '42225ff829e5023d6fdcdc9d1ca82e4b06031510097ba23df79e2efc8965e543'
assert '#define SPLIT_TRANSACTION_IDS_USER EVA_OLED_SYNC' in (root / 'config.h').read_text()
assert 'VIA_ENABLE = no' in (keymap_root / 'rules.mk').read_text()
assert '#define EVA_OLED_SPLIT_STATUS' in (keymap_root / 'config.h').read_text()
assert 'EVA_OLED_SPLIT_STATUS' not in (repo / 'keyboards/corne/v2/keymaps/themakunga_eva02/config.h').read_text()

known = {
    'KC_A': 4, 'KC_Z': 29, 'KC_1': 30, 'KC_0': 39, 'KC_ENT': 40, 'KC_ESC': 41,
    'KC_BSPC': 42, 'KC_TAB': 43, 'KC_SPC': 44, 'KC_MINS': 45, 'KC_EQL': 46,
    'KC_LBRC': 47, 'KC_RBRC': 48, 'KC_BSLS': 49, 'KC_SCLN': 51, 'KC_QUOT': 52,
    'KC_GRV': 53, 'KC_COMM': 54, 'KC_DOT': 55, 'KC_SLSH': 56, 'KC_F1': 58,
    'KC_F12': 69, 'KC_HOME': 74, 'KC_PGUP': 75, 'KC_DEL': 76, 'KC_END': 77,
    'KC_PGDN': 78, 'KC_RGHT': 79, 'KC_LEFT': 80, 'KC_DOWN': 81, 'KC_UP': 82,
    'KC_LCTL': 224,
}
assert set(re.findall(r'\bKC_\w+', source)) <= known.keys()
header = r'''
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#define PROGMEM
#define pgm_read_byte(p) (*(const unsigned char *)(p))
#define pgm_read_word(p) (*(const uint16_t *)(p))
#define strcpy_P strcpy
#define EVA_OLED_SYNC 1
#define MOD_MASK_GUI 0x88
#define MOD_MASK_CTRL 0x11
#define MOD_MASK_ALT 0x44
#define MOD_MASK_SHIFT 0x22
#define KEYBOARD_REPORT_KEYS 6
typedef struct { uint8_t mods, keys[KEYBOARD_REPORT_KEYS]; } report_keyboard_t;
typedef struct { bool caps_lock; } led_t;
typedef struct {
    uint8_t (*keyboard_leds)(void);
    void (*send_keyboard)(report_keyboard_t *);
    void (*send_mouse)(void);
} host_driver_t;
static host_driver_t *installed_driver;
uint32_t now, layer_state = 1, default_layer_state = 1;
static uint8_t wpm;
static uint32_t activity;
static bool screen_on;
#define TEST_WIDTH 32
#define TEST_HEIGHT 128
#define OLED_TIMEOUT 60000
static uint8_t mods, weak_mods;
static led_t leds;
host_driver_t *host_get_driver(void) { return installed_driver; }
void host_set_driver(host_driver_t *driver) { installed_driver = driver; }
led_t host_keyboard_led_state(void) { return leds; }
#ifdef EVA_RIGHT
static bool master = false;
static bool left = false;
#else
static bool master = true;
static bool left = true;
#endif
bool is_keyboard_master(void) { return master; }
bool is_keyboard_left(void) { return left; }
uint8_t get_current_wpm(void) { return wpm; }
uint32_t last_input_activity_elapsed(void) { return activity; }
uint32_t last_led_activity_elapsed(void) { return activity; }
void oled_off(void) { screen_on = false; }
void oled_on(void) { screen_on = true; }
uint32_t timer_read32(void) { return now; }
uint32_t timer_elapsed32(uint32_t start) { return now - start; }
uint8_t get_mods(void) { return mods; }
uint8_t get_weak_mods(void) { return weak_mods; }
uint8_t get_highest_layer(uint32_t value) {
    uint8_t result = 0;
    while (value >>= 1) ++result;
    return result;
}
void oled_set_cursor(uint8_t x, uint8_t y);
void oled_write_pixel(uint8_t x, uint8_t y, bool on);
void oled_write_raw_P(const char *data, uint16_t size);
void oled_write_raw_byte(char data, uint16_t index);
'''
header += '\n'.join(f'#define {name} {value}' for name, value in known.items())
transactions = '''
#include <assert.h>
#include <string.h>
#include "luna.h"
static uint8_t sent_packet[32], packet_size;
static unsigned sends;
static void (*receiver)(uint8_t, const void *, uint8_t, void *);
void transaction_register_rpc(int id, void (*fn)(uint8_t, const void *, uint8_t, void *)) {
    (void)id; receiver = fn;
}
bool transaction_rpc_send(int id, uint8_t size, const void *data) {
    (void)id; assert(size <= 32); memcpy(sent_packet, data, size); packet_size = size; ++sends; return false;
}
'''
test = r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "eva_oled.c"
#include "luna.c"
#include "font_ascii.c"
static unsigned pixels, forwarded, mouse_calls;
static report_keyboard_t forwarded_report;
static uint8_t cursor_row, cursor_col;
static bool canvas[TEST_HEIGHT][TEST_WIDTH];
void original_send(report_keyboard_t *report) { ++forwarded; forwarded_report = *report; }
void original_mouse(void) { ++mouse_calls; }
uint8_t original_leds(void) { return 2; }
void press(uint8_t key, uint8_t flags) {
    report_keyboard_t report = {.mods = flags, .keys = {key}};
    installed_driver->send_keyboard(&report);
    assert(!memcmp(&report, &forwarded_report, sizeof(report)));
    report.keys[0] = 0;
    installed_driver->send_keyboard(&report);
}
void oled_set_cursor(uint8_t x, uint8_t y) {
    assert(x < TEST_WIDTH / 6 && y < TEST_HEIGHT / 8); cursor_row = y; cursor_col = x;
}
void oled_write_pixel(uint8_t x, uint8_t y, bool on) {
    assert(x < TEST_WIDTH && y < TEST_HEIGHT); canvas[y][x] = on; ++pixels;
}
void oled_write_raw_P(const char *data, uint16_t size) {
    assert(cursor_col == 0 && size % 32 == 0 && cursor_row*8 + size/4 <= 128);
    for (unsigned y = 0; y < size/4; ++y)
        for (unsigned x = 0; x < 32; ++x)
            canvas[cursor_row*8+y][x] = ((uint8_t)data[y/8*32+x] >> (y%8)) & 1;
}

void oled_write_raw_byte(char data, uint16_t index) {
    assert(index < 512);
    for (uint8_t bit = 0; bit < 8; ++bit)
        canvas[index / TEST_WIDTH * 8 + bit][index % TEST_WIDTH] = !!((uint8_t)data & (1 << bit));
}
static void expect_text(uint8_t row, const char *text, uint8_t left) {
    for (uint8_t x = 0; x < 32; ++x)
        for (uint8_t y = 0; y < 8; ++y) {
            uint8_t column = 0;
            if (x >= left && x < left + 6 * strlen(text)) {
                uint8_t offset = x - left;
                column = font[(text[offset / 6] - 32) * 6 + offset % 6];
            }
            uint8_t top = row * 8;
#ifdef EVA_OLED_SPLIT_STATUS
            if (is_keyboard_left()) top += 22;
#endif
            assert(canvas[top+y][x] == !!(column & (1 << y)));
        }
}
#ifdef EVA_RIGHT
#ifdef EVA_OLED_SPLIT_STATUS
#define PET_ROW 3
#else
#define PET_ROW 4
#endif
static void expect_frame(const char *image, uint8_t row) {
    for (unsigned y = (PET_ROW - 1) * 8; y < (PET_ROW + 3) * 8; ++y)
        for (unsigned x = 0; x < 32; ++x) {
            bool expected = y >= row*8u && y < row*8u+24u &&
                (((uint8_t)image[(y-row*8)/8*32+x] >> ((y-row*8)%8)) & 1);
            assert(canvas[y][x] == expected);
        }
}
#endif
#ifdef EVA_OLED_SPLIT_STATUS
static void expect_centered(void) {
    unsigned left = 32, right = 0, top = 128, bottom = 0;
    for (unsigned y = 0; y < 128; ++y)
        for (unsigned x = 0; x < 32; ++x)
            if (canvas[y][x]) {
                if (x < left) left = x;
                if (x > right) right = x;
                if (y < top) top = y;
                if (y > bottom) bottom = y;
            }
    assert(top < 128 && abs((int)top - (127 - (int)bottom)) <= 1);
    assert(abs((int)left - (31 - (int)right)) <= 1);
}
#endif
static void check_layout(void) {
    state.pet.awake = true;
#ifdef EVA_OLED_SPLIT_STATUS
    if (!left) {
        strcpy(state.key[0], "Space"); strcpy(state.key[1], "Enter"); strcpy(state.key[2], "Q");
        state.last_mods[0] = 0; state.last_mods[1] = 0; state.last_mods[2] = MOD_MASK_GUI;
        eva_oled_render();
        expect_text(7, "", 16); expect_text(8, "Space", 1);
        expect_text(9, "", 16); expect_text(10, "Enter", 1);
        expect_text(11, "M", 13); expect_text(12, "Q", 13);
        for (uint8_t y = 0; y < 16; ++y)
            for (uint8_t x = 0; x < 32; ++x) assert(!canvas[y][x]);
        expect_centered();
        return;
    }
    const char *names[4][2] = {{"base", ""}, {"sym", "bol"}, {"func", "tions"}, {"opera", "tions"}}; // cspell:ignore tions
    for (uint8_t sample = 0; sample < 32; ++sample) {
        uint8_t mask = sample < 16 ? sample : 31 - sample;
        state.layers = mask; state.layer = get_highest_layer(mask); eva_oled_render();
        assert(screen_on);
        for (uint8_t i = 0; i < 4; ++i) {
            assert(canvas[43 - 4*i][15] == (i == state.layer));
            assert(canvas[40 - 4*i][1] && canvas[40 - 4*i][29]);
        }
        for (uint8_t line = 0; line < 2; ++line) {
            const char *name = names[state.layer][line];
            expect_text(3 + line, name, (32 - 6 * strlen(name)) / 2);
        }
        for (uint8_t y = 22; y < 46; ++y)
            assert(!canvas[y][0] && !canvas[y][30] && !canvas[y][31]);
        master = false; eva_oled_render(); master = true;
    }
    state.pet.awake = false; eva_oled_render(); assert(!screen_on);
    state.pet.awake = true; eva_oled_render(); assert(screen_on);
#else
    const uint8_t digits[3][5] = {{2, 6, 2, 2, 7}, {6, 1, 2, 4, 7}, {6, 1, 2, 1, 6}};
    for (uint8_t layer = 0; layer < 3; ++layer) {
        state.layer = layer; eva_oled_render();
        for (uint8_t y = 0; y < EVA_ICON_SIZE; ++y)
            for (uint8_t x = 0; x < EVA_ICON_SIZE; ++x)
                assert(canvas[4+y][4+x] == !!(eva_icons[EVA_LAYERS][y] & (1 << (13-x))));
        for (uint8_t y = 0; y < 5; ++y)
            for (uint8_t x = 0; x < 3; ++x)
                assert(canvas[8+y][24+x] == !!(digits[layer][y] & (1 << (2-x))));
    }
#endif
    const uint8_t masks[] = {MOD_MASK_GUI, MOD_MASK_ALT, MOD_MASK_CTRL, MOD_MASK_SHIFT};
    for (unsigned mods = 0; mods < 256; ++mods) {
        state.pet.mods = mods; eva_oled_render();
        for (uint8_t i = 0; i < 4; ++i) {
#ifdef EVA_OLED_SPLIT_STATUS
            uint8_t left = 16 * (i % 2), top = 70 + 17 * (i / 2);
            const uint8_t size = 16;
            for (uint8_t y = 1; y < 15; ++y)
                for (uint8_t x = 1; x < 15; ++x)
                    if ((x == 1 || x == 14) != (y == 1 || y == 14))
                        assert(canvas[top+y][left+x] == !!(mods & masks[i]));
#else
            uint8_t left = 18 * (i % 2), top = 60 + 20 * (i / 2);
            const uint8_t size = 14;
#endif
            for (uint8_t y = 0; y < size; ++y) {
                for (uint8_t x = 0; x < size; ++x) {
                    bool corner = ((y == 0 || y == size-1) && (x < 2 || x > size-3)) ||
                                  ((y == 1 || y == size-2) && (x == 0 || x == size-1));
                    bool border = y == 0 || y == size-1 || x == 0 || x == size-1 ||
                                  ((y == 1 || y == size-2) && (x == 1 || x == size-2));
                    bool glyph = false;
#ifdef EVA_OLED_SPLIT_STATUS
                    if (x >= 2 && x < 14 && y >= 2 && y < 14)
                        glyph = !!(eva_icons[i][y-1] & (1 << (14-x)));
#else
                    if (x >= 3 && x < 11 && y >= 3 && y < 11)
                        glyph = !!(eva_icons[i][1 + ((y-3)*12+6)/8] &
                                   (1 << (12-((x-3)*12+6)/8)));
#endif
                    glyph ^= !!(mods & masks[i]);
                    assert(canvas[top+y][left+x] == (!corner && (border || glyph)));
                }
            }
        }
#ifdef EVA_OLED_SPLIT_STATUS
        for (uint8_t x = 0; x < 32; ++x) assert(!canvas[86][x]);
#else
        for (uint8_t y = 60; y < 94; ++y)
            for (uint8_t x = 14; x < 18; ++x) assert(!canvas[y][x]);
        for (uint8_t y = 74; y < 80; ++y)
            for (uint8_t x = 0; x < 32; ++x) assert(!canvas[y][x]);
#endif
    }
#ifndef EVA_OLED_SPLIT_STATUS
    strcpy(state.key[1], "Enter"); strcpy(state.key[2], "Q");
    state.last_mods[1] = 0; state.last_mods[2] = MOD_MASK_GUI;
    eva_oled_render();
    expect_text(12, "", 16); expect_text(13, "Enter", 1);
    expect_text(14, "M", 13); expect_text(15, "Q", 13);
    state.last_mods[2] = 0; strcpy(state.key[2], "a"); eva_oled_render();
    expect_text(14, "", 16); expect_text(15, "a", 13);
    assert(pixels);
#endif
#ifdef EVA_OLED_SPLIT_STATUS
    expect_centered();
#endif
}
static bool preview(void) {
    if (!getenv("EVA_PREVIEW")) return false;
    puts("PREVIEW");
    state.pet.awake = true;
    strcpy(state.key[0], "Space"); strcpy(state.key[1], "Enter"); strcpy(state.key[2], "a");
#ifdef EVA_OLED_SPLIT_STATUS
    uint8_t count = 4;
#else
    uint8_t count = 3;
#endif
    for (uint8_t i = 0; i < count; ++i) {
        state.layers = i == 3 ? 15 : 1 | (1 << i);
        state.layer = i; state.pet.mods = i ? MOD_MASK_GUI | MOD_MASK_SHIFT : 0;
        eva_oled_render(); fwrite(canvas, 1, sizeof(canvas), stdout);
    }
    return true;
}
#ifndef EVA_RIGHT
int main(void) {
    if (preview()) return 0;
    assert(is_keyboard_master() && is_keyboard_left());
    char name[6];
    label(KC_A, name); assert(!strcmp(name, "A"));
    label(KC_0, name); assert(!strcmp(name, "0"));
    label(KC_F12, name); assert(!strcmp(name, "F12"));
    label(0xFFFF, name); assert(!strcmp(name, "#FFFF"));
    eva_oled_init(); assert(receiver);
    matrix_scan_user(); assert(!installed_driver);
    host_driver_t original = {.keyboard_leds = original_leds, .send_keyboard = original_send, .send_mouse = original_mouse};
    installed_driver = &original;
    matrix_scan_user(); assert(installed_driver != &original);
    assert(installed_driver->keyboard_leds() == 2);
    installed_driver->send_mouse(); assert(mouse_calls == 1);
    matrix_scan_user();
    now = 100; press(KC_A, 0); assert(!strcmp(state.key[2], "a"));
    assert(forwarded == 2);
    press(KC_A, MOD_MASK_SHIFT); assert(!strcmp(state.key[2], "A") && !state.last_mods[2]);
    leds.caps_lock = true;
    press(KC_A, 0); assert(!strcmp(state.key[2], "A"));
    press(KC_A, MOD_MASK_SHIFT); assert(!strcmp(state.key[2], "a"));
    leds.caps_lock = false;
    press(KC_1 + 1, MOD_MASK_SHIFT); assert(!strcmp(state.key[2], "@"));
    press(KC_LBRC, MOD_MASK_SHIFT); assert(!strcmp(state.key[2], "{"));
    press(KC_COMM, MOD_MASK_SHIFT); assert(!strcmp(state.key[2], "<"));
    press(KC_DOT, MOD_MASK_SHIFT); assert(!strcmp(state.key[2], ">"));
    press(KC_SLSH, MOD_MASK_SHIFT); assert(!strcmp(state.key[2], "?"));
    press(KC_SPC, 0); assert(!strcmp(state.key[2], "Space"));
    press(KC_ENT, 0); assert(!strcmp(state.key[2], "Enter") && !strcmp(state.key[1], "Space"));
    press(KC_UP, 0); assert(!strcmp(state.key[2], "Up") && !strcmp(state.key[1], "Enter"));
    assert(!strcmp(state.key[0], "Space"));
    report_keyboard_t held = {.mods = MOD_MASK_CTRL, .keys = {KC_A}};
    installed_driver->send_keyboard(&held);
    assert(!strcmp(state.key[2], "A") && state.last_mods[2] == MOD_MASK_CTRL);
    held.mods = 0; installed_driver->send_keyboard(&held);
    assert(!strcmp(state.key[2], "A") && state.last_mods[2] == MOD_MASK_CTRL);
    held.keys[0] = 0; installed_driver->send_keyboard(&held);
    press(KC_A + ('Q'-'A'), MOD_MASK_GUI | MOD_MASK_CTRL);
    assert(!strcmp(state.key[2], "Q") && state.last_mods[2] == (MOD_MASK_GUI | MOD_MASK_CTRL));
    report_keyboard_t release = {0};
    installed_driver->send_keyboard(&release);
    release.mods = MOD_MASK_SHIFT;
    installed_driver->send_keyboard(&release);
    assert(!strcmp(state.key[2], "Q") && state.last_mods[2] == (MOD_MASK_GUI | MOD_MASK_CTRL));
    release.keys[0] = 1; installed_driver->send_keyboard(&release);
    assert(!strcmp(state.key[2], "Q"));
    assert(state.pet.jumps == 1 && !state.pet.space);
    report_keyboard_t space = {.keys = {KC_SPC}};
    installed_driver->send_keyboard(&space); assert(state.pet.space && state.pet.jumps == 2);
    installed_driver->send_keyboard(&space); assert(state.pet.jumps == 2);
    space.keys[0] = 0; installed_driver->send_keyboard(&space); assert(!state.pet.space);
    press(KC_A + ('Q'-'A'), MOD_MASK_GUI | MOD_MASK_CTRL);
    layer_state = 4; mods = MOD_MASK_CTRL; weak_mods = MOD_MASK_GUI; wpm = 41;
    eva_oled_housekeeping(); assert(state.layer == 2 && state.layers == 5);
    display_state_t sent; memcpy(&sent, sent_packet, sizeof(sent));
    assert(packet_size == sizeof(state));
    assert(sends == 1 && sent.pet.wpm == 41 && sent.pet.mods == (MOD_MASK_CTRL | MOD_MASK_GUI));
    assert(sent.pet.jumps == 2 && !sent.pet.space && sent.pet.awake);
    eva_oled_housekeeping(); assert(sends == 1);
    now += 50; activity = OLED_TIMEOUT; leds.caps_lock = true;
    eva_oled_housekeeping(); memcpy(&sent, sent_packet, sizeof(sent));
    assert(sends == 2 && !sent.pet.awake && sent.pet.caps);
    assert(!memcmp(sent.key, state.key, sizeof(state.key)));
    display_state_t saved = state; saved.layer = 0;
    receiver(sizeof(saved), &saved, 0, NULL); assert(state.layer == 2);
    report_keyboard_t pair = {.keys = {KC_A, KC_1}};
    installed_driver->send_keyboard(&pair);
    assert(!strcmp(state.key[1], "A") && !strcmp(state.key[2], "1"));
    assert(!strcmp(state.key[0], "Q") && state.last_mods[0] == (MOD_MASK_GUI | MOD_MASK_CTRL));
    installed_driver->send_keyboard(&pair);
    assert(!strcmp(state.key[1], "A") && !strcmp(state.key[2], "1"));
    assert(!strcmp(state.key[0], "Q"));

    state.pet.awake = true;
    check_layout();
    puts("OK master: final USB output, ordered three-key history, forwarding, shared layout and RPC");
}
#else
int main(void) {
    if (preview()) return 0;
    assert(!is_keyboard_master());
    eva_oled_init(); assert(receiver);
    matrix_scan_user(); assert(!installed_driver);
    display_state_t packet = {.pet = {.awake = true}, .layer = 2,
                              .layers = 5, .last_mods = {0, 0, MOD_MASK_GUI}, .key = {"Space", "Enter", "Q"}};
    receiver(1, &packet, 0, NULL); assert(!state.pet.awake);
    for (uint8_t i = 0; i < 3; ++i) {
        packet.key[i][5] = 'x';
        receiver(sizeof(packet), &packet, 0, NULL); assert(!state.pet.awake);
        packet.key[i][5] = 0;
    }
    receiver(sizeof(packet), &packet, 0, NULL); assert(!memcmp(&state, &packet, sizeof(state)));
    eva_oled_housekeeping(); assert(!sends && !memcmp(&state, &packet, sizeof(state)));
    check_layout();
    now = 0; state.pet.mods = 0;
    eva_oled_render(); expect_frame(sit[1], PET_ROW);
    now = 199; eva_oled_render(); expect_frame(sit[1], PET_ROW);
    now = 200; eva_oled_render(); expect_frame(sit[0], PET_ROW);
    const uint8_t speeds[] = {0, 10, 11, 40, 41, 255};
    const char *images[] = {sit[1], sit[0], walk[1], walk[0], run[1], run[0]};
    for (unsigned i = 0; i < sizeof(speeds); ++i) {
        now += 200; state.pet.wpm = speeds[i]; eva_oled_render(); expect_frame(images[i], PET_ROW);
    }
    now += 200; state.pet.mods = MOD_MASK_CTRL; eva_oled_render(); expect_frame(sneak[1], PET_ROW);
    now += 200; state.pet.caps = true; eva_oled_render(); expect_frame(bark[0], PET_ROW);
    now += 200; state.pet.caps = false; state.pet.mods = 0; state.pet.wpm = 0;
    state.pet.jumps = 255; eva_oled_render(); expect_frame(sit[1], PET_ROW - 1);
    now += 200; state.pet.jumps = 0; eva_oled_render(); expect_frame(sit[0], PET_ROW - 1);
    now += 200; eva_oled_render(); expect_frame(sit[1], PET_ROW);
    now += 200; state.pet.space = true; eva_oled_render(); expect_frame(sit[0], PET_ROW - 1);
    now += 200; eva_oled_render(); expect_frame(sit[1], PET_ROW - 1);
    now += 200; state.pet.space = false; eva_oled_render(); expect_frame(sit[0], PET_ROW);
    left = false;
    state.pet.awake = false; eva_oled_render(); assert(!screen_on);
    state.pet.awake = true; now += 200; eva_oled_render(); assert(screen_on);
    puts("OK peripheral: complete state, physical-side layout, Luna frames, WPM, jumps and sleep");
}
#endif

'''
with tempfile.TemporaryDirectory() as directory:
    tmp = Path(directory)
    (tmp / 'mock.h').write_text(header)
    (tmp / 'host.h').write_text('#pragma once\n')
    (tmp / 'transactions.h').write_text(transactions)
    (tmp / 'progmem.h').write_text('#pragma once\n')
    (tmp / 'test.c').write_text(test)
    for board, side in [('eva01', 'left'), ('eva01', 'right'), ('eva02', 'left'), ('eva02', 'right')]:
        binary = tmp / f'{board}-{side}'
        subprocess.run([os.environ.get('CC', 'cc'), '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-DNO_ACTION_ONESHOT',
                        *(['-DEVA_RIGHT'] if side == 'right' else []),
                        *(['-DEVA_OLED_SPLIT_STATUS'] if board == 'eva01' else []),
                        '-DQMK_KEYBOARD_H="mock.h"', '-I', str(tmp), '-I', str(root),
                        str(tmp / 'test.c'), '-o', str(binary)], check=True)
        result = subprocess.run([str(binary)], capture_output=True, env={k: v for k, v in os.environ.items() if k != 'EVA_PREVIEW'})
        assert result.returncode == 0, result.stderr.decode()
        print(f'{board}: ' + result.stdout.split(b'\n')[0].decode())
        if os.environ.get('EVA_PREVIEW'):
            preview_result = subprocess.run([str(binary)], capture_output=True, check=True)
            Path(os.environ['EVA_PREVIEW'] + '-' + board + '-' + side + '.raw').write_bytes(preview_result.stdout.split(b'\n', 1)[1])
