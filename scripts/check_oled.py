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
        assert keys[50:54] == ['C(KC_S)', 'KC_LALT', 'MO(1)', 'KC_LGUI']
        assert keys[56] == 'MO(2)'
        assert keys[55] == 'TD(TD_SPC_ENT)'
    else:
        assert keys[52] == keys[53] == keys[56] == 'KC_TRNS'
        assert keys[54:56] == ['KC_ENT', 'KC_ENT']
ns = {'svg': 'http://www.w3.org/2000/svg'}
svg = ET.parse(repo / 'docs/eva01-layout.svg')
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
assert 'SRC += eva_oled.c bongo/bongo_cat.c' in (root / 'rules.mk').read_text()
assert '#define SPLIT_TRANSACTION_IDS_USER EVA_OLED_SYNC' in (root / 'config.h').read_text()
assert 'VIA_ENABLE = no' in (keymap_root / 'rules.mk').read_text()

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
static uint32_t now, layer_state = 1, default_layer_state = 1;
static bool master = true;
static uint8_t mods, weak_mods;
static led_t leds;
static host_driver_t *host_get_driver(void) { return installed_driver; }
static void host_set_driver(host_driver_t *driver) { installed_driver = driver; }
static led_t host_keyboard_led_state(void) { return leds; }
static bool is_keyboard_master(void) { return master; }
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
static unsigned pixels, forwarded, mouse_calls;
static report_keyboard_t forwarded_report;
static uint8_t cursor_row, cursor_col;
static char lines[16][6];
static bool canvas[128][32];
static void original_send(report_keyboard_t *report) { ++forwarded; forwarded_report = *report; }
static void original_mouse(void) { ++mouse_calls; }
static uint8_t original_leds(void) { return 2; }
static void press(uint8_t key, uint8_t flags) {
    report_keyboard_t report = {.mods = flags, .keys = {key}};
    installed_driver->send_keyboard(&report);
    assert(!memcmp(&report, &forwarded_report, sizeof(report)));
    report.keys[0] = 0;
    installed_driver->send_keyboard(&report);
}
static void oled_set_cursor(uint8_t x, uint8_t y) {
    assert(x < 5 && y < 16); cursor_row = y; cursor_col = x;
}
static void oled_write(const char *text, bool inverted) {
    assert(cursor_col + strlen(text) <= 5);
    while (*text) {
        assert(*text >= 32 && *text <= 126);
        lines[cursor_row][cursor_col] = *text;
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
    assert(cursor_col == 0 && cursor_row == 8 && size == 96);
    for (unsigned y = 0; y < 24; ++y)
        for (unsigned x = 0; x < 32; ++x)
            canvas[64+y][x] = ((uint8_t)data[y/8*32+x] >> (y%8)) & 1;
}
int main(void) {
    char name[6];
    label(KC_A, name); assert(!strcmp(name, "A"));
    label(KC_0, name); assert(!strcmp(name, "0"));
    label(KC_F12, name); assert(!strcmp(name, "F12"));
    label(0xFFFF, name); assert(!strcmp(name, "#FFFF"));
    eva_oled_init(); assert(receiver);
    matrix_scan_user(); assert(!installed_driver);
    host_driver_t original = {.keyboard_leds = original_leds, .send_keyboard = original_send, .send_mouse = original_mouse};
    installed_driver = &original;
    master = false; matrix_scan_user(); assert(installed_driver == &original);
    master = true; matrix_scan_user(); assert(installed_driver != &original);
    assert(installed_driver->keyboard_leds() == 2);
    installed_driver->send_mouse(); assert(mouse_calls == 1);
    matrix_scan_user();
    now = 100; press(KC_A, 0); assert(!strcmp(state.key, "a"));
    assert(forwarded == 2);
    press(KC_A, MOD_MASK_SHIFT); assert(!strcmp(state.key, "A") && !state.last_mods);
    leds.caps_lock = true;
    press(KC_A, 0); assert(!strcmp(state.key, "A"));
    press(KC_A, MOD_MASK_SHIFT); assert(!strcmp(state.key, "a"));
    leds.caps_lock = false;
    press(KC_1 + 1, MOD_MASK_SHIFT); assert(!strcmp(state.key, "@"));
    press(KC_LBRC, MOD_MASK_SHIFT); assert(!strcmp(state.key, "{"));
    press(KC_COMM, MOD_MASK_SHIFT); assert(!strcmp(state.key, "<"));
    press(KC_DOT, MOD_MASK_SHIFT); assert(!strcmp(state.key, ">"));
    press(KC_SLSH, MOD_MASK_SHIFT); assert(!strcmp(state.key, "?"));
    press(KC_SPC, 0); assert(!strcmp(state.key, "Space"));
    press(KC_ENT, 0); assert(!strcmp(state.key, "Enter"));
    press(KC_UP, 0); assert(!strcmp(state.key, "Up"));
    report_keyboard_t held = {.mods = MOD_MASK_CTRL, .keys = {KC_A}};
    installed_driver->send_keyboard(&held);
    assert(!strcmp(state.key, "A") && state.last_mods == MOD_MASK_CTRL);
    held.mods = 0; installed_driver->send_keyboard(&held);
    assert(!strcmp(state.key, "A") && state.last_mods == MOD_MASK_CTRL);
    held.keys[0] = 0; installed_driver->send_keyboard(&held);
    press(KC_A + ('Q'-'A'), MOD_MASK_GUI | MOD_MASK_CTRL);
    assert(!strcmp(state.key, "Q") && state.last_mods == (MOD_MASK_GUI | MOD_MASK_CTRL));
    report_keyboard_t release = {0};
    installed_driver->send_keyboard(&release);
    release.mods = MOD_MASK_SHIFT;
    installed_driver->send_keyboard(&release);
    assert(!strcmp(state.key, "Q") && state.last_mods == (MOD_MASK_GUI | MOD_MASK_CTRL));
    release.keys[0] = 1; installed_driver->send_keyboard(&release);
    assert(!strcmp(state.key, "Q"));
    layer_state = 4; mods = MOD_MASK_CTRL; weak_mods = MOD_MASK_GUI;
    eva_oled_housekeeping(); assert(state.layer == 2 && state.frame != 0);
    assert(sends == 1);
    eva_oled_housekeeping(); assert(sends == 1);
    now += 50; eva_oled_housekeeping(); assert(sends == 2);
    now += 220; eva_oled_housekeeping(); assert(state.frame == 0);
    eva_oled_render(); assert(pixels);
    assert(!strcmp(lines[12], " MC  ") && !strcmp(lines[13], "  Q  "));
    unsigned previous = pixels; master = false; eva_oled_render(); assert(pixels > previous);
    display_state_t packet = {.layer = 1, .frame = 2, .key = "B"};
    receiver(1, &packet, 0, NULL); assert(state.layer == 2);
    receiver(sizeof(packet), &packet, 0, NULL); assert(state.layer == 1);
    eva_oled_render(); assert(!strcmp(lines[13], "  B  "));
    assert(!strcmp(lines[12], "     "));
    memset(packet.key, 'X', sizeof(packet.key));
    receiver(sizeof(packet), &packet, 0, NULL); assert(state.key[5] == 0);
    eva_oled_render(); assert(!strcmp(lines[13], "XXXXX"));
    const uint8_t digits[3][5] = {{2, 6, 2, 2, 7}, {6, 1, 2, 4, 7}, {6, 1, 2, 1, 6}};
    for (uint8_t layer = 0; layer < 3; ++layer) {
        state.layer = layer;
        eva_oled_render();
        for (uint8_t y = 0; y < EVA_ICON_SIZE; ++y)
            for (uint8_t x = 0; x < EVA_ICON_SIZE; ++x)
                assert(canvas[4+y][4+x] == !!(eva_icons[EVA_LAYERS][y] & (1 << (13-x))));
        for (uint8_t y = 0; y < 5; ++y)
            for (uint8_t x = 0; x < 3; ++x)
                assert(canvas[8+y][24+x] == !!(digits[layer][y] & (1 << (2-x))));
    }
    assert(sizeof(waiting_frame) == 96);
    assert(memcmp(animation_frames[0], animation_frames[1], 96));
    const char *frames[] = {waiting_frame, animation_frames[0], animation_frames[1], ready_frame};
    for (uint8_t frame = 0; frame < 4; ++frame) {
        state.frame = frame;
        eva_oled_render();
        for (unsigned y = 0; y < 24; ++y)
            for (unsigned x = 0; x < 32; ++x)
                assert(canvas[64+y][x] == (((uint8_t)frames[frame][y/8*32+x] >> (y%8)) & 1));
    }
    const uint8_t masks[] = {MOD_MASK_GUI, MOD_MASK_ALT, MOD_MASK_CTRL, MOD_MASK_SHIFT};
    for (unsigned mods = 0; mods < 256; ++mods) {
        state.mods = mods;
        state.last_mods = mods;
        eva_oled_render();
        for (uint8_t i = 0; i < 4; ++i)
            for (uint8_t y = 0; y < EVA_ICON_SIZE; ++y)
                for (uint8_t x = 0; x < EVA_ICON_SIZE; ++x)
                    assert(canvas[24+16*(i/2)+y][1+16*(i%2)+x] ==
                        (!!(eva_icons[i][y] & (1 << (13-x))) ^ !!(mods & masks[i])));
    }
    assert(!strcmp(lines[12], "MACS "));
    puts("OK: actual keyboard reports, forwarding, US text, chords, 2x2 icons, layers, animation, RPC");
}
'''
with tempfile.TemporaryDirectory() as directory:
    tmp = Path(directory)
    (tmp / 'mock.h').write_text(header)
    (tmp / 'host.h').write_text('#pragma once\n')
    (tmp / 'transactions.h').write_text(transactions)
    (tmp / 'progmem.h').write_text('#pragma once\n')
    (tmp / 'test.c').write_text(test)
    binary = tmp / 'test'
    subprocess.run([os.environ.get('CC', 'cc'), '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-DNO_ACTION_ONESHOT', '-DQMK_KEYBOARD_H="mock.h"', '-I', str(tmp), '-I', str(root),
                    str(tmp / 'test.c'), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
