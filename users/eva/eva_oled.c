#include "eva_oled.h"
#include "transactions.h"
#include "host.h"
#include "bongo/bongo_cat.h"
#include "icons.h"
#include <string.h>

// Both OLEDs: portrait 32x128, QMK 6x8 text and rasterized Nerd Font icons.
// Only the last transmitted keyboard action is transient display state.
typedef struct {
    uint8_t layer, mods, frame, last_mods;
    char key[6];
} display_state_t;
static display_state_t state;
static uint32_t last_press, last_attempt;
static bool typing;
static uint8_t stroke;
static host_driver_t display_driver;
static void (*forward_keyboard)(report_keyboard_t *);
static report_keyboard_t previous_report;
_Static_assert(sizeof(display_state_t) <= 32, "Split RPC payload too large");

static void label(uint16_t keycode, char out[6]) {
    memset(out, 0, 6);
    if (keycode >= KC_A && keycode <= KC_Z) {
        out[0] = 'A' + keycode - KC_A;
        return;
    }
    if (keycode >= KC_1 && keycode <= KC_0) {
        out[0] = "1234567890"[keycode - KC_1];
        return;
    }
    if (keycode >= KC_F1 && keycode <= KC_F12) {
        uint8_t number = keycode - KC_F1 + 1;
        out[0] = 'F';
        out[1] = number < 10 ? '0' + number : '1';
        if (number >= 10) out[2] = '0' + number % 10;
        return;
    }
    switch (keycode) {
        case KC_ESC: strcpy(out, "Esc"); break;
        case KC_TAB: strcpy(out, "Tab"); break;
        case KC_ENT: strcpy(out, "Enter"); break;
        case KC_SPC: strcpy(out, "Space"); break;
        case KC_BSPC: strcpy(out, "Bksp"); break;
        case KC_DEL: strcpy(out, "Del"); break;
        case KC_HOME: strcpy(out, "Home"); break;
        case KC_END: strcpy(out, "End"); break;
        case KC_PGUP: strcpy(out, "PgUp"); break;
        case KC_PGDN: strcpy(out, "PgDn"); break;
        case KC_LEFT: strcpy(out, "Left"); break;
        case KC_RGHT: strcpy(out, "Right"); break;
        case KC_UP: strcpy(out, "Up"); break;
        case KC_DOWN: strcpy(out, "Down"); break;
        case KC_MINS: strcpy(out, "-"); break;
        case KC_EQL: strcpy(out, "="); break;
        case KC_LBRC: strcpy(out, "["); break;
        case KC_RBRC: strcpy(out, "]"); break;
        case KC_BSLS: strcpy(out, "\\"); break;
        case KC_SCLN: strcpy(out, ";"); break;
        case KC_QUOT: strcpy(out, "'"); break;
        case KC_GRV: strcpy(out, "`"); break;
        case KC_COMM: strcpy(out, ","); break;
        case KC_DOT: strcpy(out, "."); break;
        case KC_SLSH: strcpy(out, "/"); break;
        default: {
            // Custom keycodes still have an unambiguous visible identity.
            const char hex[] = "0123456789ABCDEF";
            out[0] = '#';
            for (uint8_t i = 0; i < 4; ++i) out[i + 1] = hex[(keycode >> (12 - 4 * i)) & 15];
        }
    }
}

static void receive_state(uint8_t size, const void *data, uint8_t out_size, void *out) {
    (void)out_size;
    (void)out;
    if (size != sizeof(state)) return;
    memcpy(&state, data, sizeof(state));
    state.key[5] = '\0';
}

void eva_oled_init(void) {
    transaction_register_rpc(EVA_OLED_SYNC, receive_state);
}

// Observe final reports so tap dance, remaps and overrides show their actual output.
static void send_keyboard(report_keyboard_t *report) {
    forward_keyboard(report);
    for (uint8_t i = 0; i < KEYBOARD_REPORT_KEYS; ++i) {
        uint8_t keycode = report->keys[i];
        if (keycode < KC_A || keycode >= KC_LCTL || memchr(previous_report.keys, keycode, KEYBOARD_REPORT_KEYS)) continue;
        label(keycode, state.key);
        bool shifted = report->mods & MOD_MASK_SHIFT;
        bool shortcut = report->mods & (MOD_MASK_GUI | MOD_MASK_ALT | MOD_MASK_CTRL);
        state.last_mods = shortcut ? report->mods : 0;
        if (keycode >= KC_A && keycode <= KC_Z) {
            if (!shortcut && !(shifted ^ host_keyboard_led_state().caps_lock)) state.key[0] += 'a' - 'A';
        } else {
            const char plain[] = "1234567890-=[]\\;'/.,`";
            const char upper[] = "!@#$%^&*()_+{}|:\"?><~";
            const char *match = strchr(plain, state.key[0]);
            if (shifted && state.key[1] == '\0' && match) state.key[0] = upper[match - plain];
        }
        last_press = timer_read32();
        typing = true;
        stroke ^= 1;
    }
    previous_report = *report;
}

void matrix_scan_user(void) {
    if (!is_keyboard_master() || forward_keyboard) return;
    host_driver_t *driver = host_get_driver();
    if (!driver || !driver->send_keyboard) return;
    display_driver = *driver;
    forward_keyboard = driver->send_keyboard;
    display_driver.send_keyboard = send_keyboard;
    host_set_driver(&display_driver);
}

void eva_oled_housekeeping(void) {
    if (!is_keyboard_master()) return;
    state.layer = get_highest_layer(layer_state | default_layer_state);
    state.mods = get_mods() | get_weak_mods();
#ifndef NO_ACTION_ONESHOT
    state.mods |= get_oneshot_mods();
#endif
    if (typing && timer_elapsed32(last_press) >= 220) typing = false;
    state.frame = typing ? 1 + stroke : 0;
    // Throttle failures too, so a disconnected half cannot stall every scan.
    if (timer_elapsed32(last_attempt) >= 50) {
        last_attempt = timer_read32();
        transaction_rpc_send(EVA_OLED_SYNC, sizeof(state), &state);
    }
}

static void text_at(uint8_t row, const char *text, bool inverted) {
    oled_set_cursor(0, row);
    uint8_t padding = (5 - strlen(text)) / 2;
    for (uint8_t i = 0; i < padding; ++i) oled_write(" ", inverted);
    oled_write(text, inverted);
    for (uint8_t i = padding + strlen(text); i < 5; ++i) oled_write(" ", inverted);
}

static void icon_at(uint8_t left, uint8_t top, const uint16_t icon[EVA_ICON_SIZE], bool inverted) {
    for (uint8_t y = 0; y < EVA_ICON_SIZE; ++y) {
        uint16_t row = pgm_read_word(&icon[y]);
        for (uint8_t x = 0; x < EVA_ICON_SIZE; ++x)
            oled_write_pixel(left + x, top + y, !!(row & (1 << (EVA_ICON_SIZE - 1 - x))) ^ inverted);
    }
}

bool eva_oled_render(void) {
    icon_at(4, 4, eva_icons[EVA_LAYERS], false);
    // User-facing layers are 1..3; the number keeps the same glyph unambiguous.
    static const uint8_t PROGMEM numbers[3][5] = {{2, 6, 2, 2, 7}, {6, 1, 2, 4, 7}, {6, 1, 2, 1, 6}};
    uint8_t layer = state.layer > 2 ? 2 : state.layer;
    for (uint8_t y = 0; y < 5; ++y)
        for (uint8_t x = 0; x < 3; ++x)
            oled_write_pixel(24 + x, 8 + y, pgm_read_byte(&numbers[layer][y]) & (1 << (2 - x)));
    const uint8_t masks[] = {MOD_MASK_GUI, MOD_MASK_ALT, MOD_MASK_CTRL, MOD_MASK_SHIFT};
    for (uint8_t i = 0; i < 4; ++i)
        icon_at(1 + 16 * (i % 2), 24 + 16 * (i / 2), eva_icons[i], state.mods & masks[i]);
    render_bongo_cat(state.frame);
    char chord[5] = {0};
    uint8_t length = 0;
    for (uint8_t i = 0; i < 4; ++i)
        if (state.last_mods & masks[i]) chord[length++] = "MACS"[i];
    text_at(12, chord, false);
    text_at(13, state.key, false);
    return false;
}
