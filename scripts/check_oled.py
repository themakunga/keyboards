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
assert 'SRC += eva_oled.c' in (root / 'rules.mk').read_text()
assert 'SRC += luna.c' in (root / 'rules.mk').read_text()
luna_bytes = bytes(int(value, 16) for value in re.findall(r'0x([0-9a-f]+)', (root / 'luna.c').read_text()))
assert len(luna_bytes) == 960
assert hashlib.sha256(luna_bytes).hexdigest() == '42225ff829e5023d6fdcdc9d1ca82e4b06031510097ba23df79e2efc8965e543'
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
uint32_t now, layer_state = 1, default_layer_state = 1;
static uint8_t wpm;
static uint32_t activity;
static bool screen_on;
#define OLED_TIMEOUT 60000
static uint8_t mods, weak_mods;
static led_t leds;
host_driver_t *host_get_driver(void) { return installed_driver; }
void host_set_driver(host_driver_t *driver) { installed_driver = driver; }
led_t host_keyboard_led_state(void) { return leds; }
bool is_keyboard_master(void);
bool is_keyboard_left(void);
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
void oled_write(const char *text, bool inverted);
void oled_write_pixel(uint8_t x, uint8_t y, bool on);
void oled_write_raw_P(const char *data, uint16_t size);
'''
header += '\n'.join(f'#define {name} {value}' for name, value in known.items())
transactions = '''
#include <assert.h>
#include <string.h>
#include "luna.h"
static eva_pet_state_t sent_pet;
static unsigned sends;
static void (*receiver)(uint8_t, const void *, uint8_t, void *);
void transaction_register_rpc(int id, void (*fn)(uint8_t, const void *, uint8_t, void *)) {
    (void)id; receiver = fn;
}
bool transaction_rpc_send(int id, uint8_t size, const void *data) {
    (void)id; assert(size == sizeof(eva_pet_state_t)); memcpy(&sent_pet, data, size); ++sends; return false;
}
'''
test = r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "eva_oled.c"
#ifdef EVA_RIGHT
#include "luna.c"
#endif
#include "font_ascii.c"
static unsigned pixels, forwarded, mouse_calls;
static report_keyboard_t forwarded_report;
static uint8_t cursor_row, cursor_col;
static char lines[16][6];
static bool canvas[128][32];
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
    assert(x < 5 && y < 16); cursor_row = y; cursor_col = x;
}
void oled_write(const char *text, bool inverted) {
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
void oled_write_pixel(uint8_t x, uint8_t y, bool on) {
    assert(x < 32 && y < 128); canvas[y][x] = on; ++pixels;
}
void oled_write_raw_P(const char *data, uint16_t size) {
    assert(cursor_col == 0 && size % 32 == 0 && cursor_row*8 + size/4 <= 128);
    for (unsigned y = 0; y < size/4; ++y)
        for (unsigned x = 0; x < 32; ++x)
            canvas[cursor_row*8+y][x] = ((uint8_t)data[y/8*32+x] >> (y%8)) & 1;
}
#ifndef EVA_RIGHT
int main(void) {
    assert(is_keyboard_master() && is_keyboard_left());
    char name[6];
    label(KC_A, name); assert(!strcmp(name, "A"));
    label(KC_0, name); assert(!strcmp(name, "0"));
    label(KC_F12, name); assert(!strcmp(name, "F12"));
    label(0xFFFF, name); assert(!strcmp(name, "#FFFF"));
    eva_oled_init(); assert(!receiver);
    matrix_scan_user(); assert(!installed_driver);
    host_driver_t original = {.keyboard_leds = original_leds, .send_keyboard = original_send, .send_mouse = original_mouse};
    installed_driver = &original;
    matrix_scan_user(); assert(installed_driver != &original);
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
    assert(pet.jumps == 1 && !pet.space);
    report_keyboard_t space = {.keys = {KC_SPC}};
    installed_driver->send_keyboard(&space); assert(pet.space && pet.jumps == 2);
    installed_driver->send_keyboard(&space); assert(pet.jumps == 2);
    space.keys[0] = 0; installed_driver->send_keyboard(&space); assert(!pet.space);
    press(KC_A + ('Q'-'A'), MOD_MASK_GUI | MOD_MASK_CTRL);
    layer_state = 4; mods = MOD_MASK_CTRL; weak_mods = MOD_MASK_GUI; wpm = 41;
    eva_oled_housekeeping(); assert(state.layer == 2);
    assert(sends == 1 && sent_pet.wpm == 41 && sent_pet.mods == (MOD_MASK_CTRL | MOD_MASK_GUI));
    assert(sent_pet.jumps == 2 && !sent_pet.space && sent_pet.awake);
    eva_oled_housekeeping(); assert(sends == 1);
    now += 50; activity = OLED_TIMEOUT; leds.caps_lock = true;
    eva_oled_housekeeping(); assert(sends == 2 && !sent_pet.awake && sent_pet.caps);
    eva_oled_render(); assert(pixels);
    assert(!strcmp(lines[8], " MC  ") && !strcmp(lines[9], "  Q  "));
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
    assert(!strcmp(lines[8], "MACS "));
    puts("OK left: actual keyboard reports, forwarding, US text, chords, icons, layers, pet RPC");
    if (getenv("EVA_PREVIEW")) {
        state.mods = MOD_MASK_CTRL; state.last_mods = 0; strcpy(state.key, "Enter");
        eva_oled_render(); fwrite(canvas, 1, sizeof(canvas), stdout);
    }
}
#else
static void expect_frame(const char *image, uint8_t row) {
    for (unsigned y = 0; y < 128; ++y)
        for (unsigned x = 0; x < 32; ++x) {
            bool expected = y >= row*8u && y < row*8u+24u &&
                (((uint8_t)image[(y-row*8)/8*32+x] >> ((y-row*8)%8)) & 1);
            assert(canvas[y][x] == expected);
        }
}
int main(void) {
    assert(!is_keyboard_master() && !is_keyboard_left());
    eva_oled_init(); assert(receiver);
    eva_pet_state_t packet = {.awake = true};
    receiver(1, &packet, 0, NULL); assert(!pet.awake);
    receiver(sizeof(packet), &packet, 0, NULL);
    eva_oled_render(); assert(screen_on); expect_frame(sit[1], 7);
    now = 199; eva_oled_render(); expect_frame(sit[1], 7);
    now = 200; eva_oled_render(); expect_frame(sit[0], 7);
    const uint8_t speeds[] = {0, 10, 11, 40, 41, 255};
    const char *images[] = {sit[1], sit[0], walk[1], walk[0], run[1], run[0]};
    for (unsigned i = 0; i < sizeof(speeds); ++i) {
        now += 200; pet.wpm = speeds[i]; eva_oled_render(); expect_frame(images[i], 7);
    }
    now += 200; pet.mods = MOD_MASK_CTRL; eva_oled_render(); expect_frame(sneak[1], 7);
    now += 200; pet.caps = true; eva_oled_render(); expect_frame(bark[0], 7);
    now += 200; pet.caps = false; pet.mods = 0; pet.wpm = 0;
    pet.jumps = 255; eva_oled_render(); expect_frame(sit[1], 6);
    now += 200; pet.jumps = 0; eva_oled_render(); expect_frame(sit[0], 6);
    now += 200; eva_oled_render(); expect_frame(sit[1], 7);
    now += 200; pet.space = true; eva_oled_render(); expect_frame(sit[0], 6);
    now += 200; eva_oled_render(); expect_frame(sit[1], 6);
    now += 200; pet.space = false; eva_oled_render(); expect_frame(sit[0], 7);
    pet.awake = false; eva_oled_render(); assert(!screen_on);
    pet.awake = true; now += 200; eva_oled_render(); assert(screen_on);
    puts("OK right: exact Luna frames, WPM thresholds, Caps/Control priority, short/held Space, sleep, RPC");
    if (getenv("EVA_PREVIEW")) fwrite(canvas, 1, sizeof(canvas), stdout);
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
    for side in ('left', 'right'):
        binary = tmp / side
        subprocess.run([os.environ.get('CC', 'cc'), '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-DNO_ACTION_ONESHOT',
                        *(['-DEVA_RIGHT'] if side == 'right' else []),
                        '-DQMK_KEYBOARD_H="mock.h"', '-I', str(tmp), '-I', str(root),
                        str(tmp / 'test.c'), '-o', str(binary)], check=True)
        result = subprocess.run([str(binary)], capture_output=True)
        assert result.returncode == 0, result.stderr.decode()
        print(result.stdout.split(b'\n')[0].decode())
        if os.environ.get('EVA_PREVIEW'):
            Path(os.environ['EVA_PREVIEW'] + '-' + side + '.raw').write_bytes(result.stdout.split(b'\n', 1)[1])
