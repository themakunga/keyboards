#include "eva_oled.h"
#include "transactions.h"
#include "host.h"
#include "luna.h"
#include "icons.h"
#include <string.h>

// Final USB keyboard actions are transient display state, shared by both halves.
typedef struct {
    eva_pet_state_t pet;
    uint8_t layer, layers, last_mods[3];
    char key[3][6];
} display_state_t;
static display_state_t state;
_Static_assert(sizeof(state) <= 32, "Split RPC payload too large");
static uint32_t last_attempt;
static host_driver_t display_driver;
static void (*forward_keyboard)(report_keyboard_t *);
static report_keyboard_t previous_report;
static const uint8_t masks[] = {MOD_MASK_GUI, MOD_MASK_ALT, MOD_MASK_CTRL, MOD_MASK_SHIFT};

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
    if (!is_keyboard_master() && size == sizeof(state)) {
        const display_state_t *incoming = data;
        for (uint8_t i = 0; i < 3; ++i)
            if (incoming->key[i][5]) return;
        memcpy(&state, data, sizeof(state));
    }
}

void eva_oled_init(void) { transaction_register_rpc(EVA_OLED_SYNC, receive_state); }

// Observe final reports so tap dance, remaps and overrides show their actual output.
static void send_keyboard(report_keyboard_t *report) {
    forward_keyboard(report);
    state.pet.space = memchr(report->keys, KC_SPC, KEYBOARD_REPORT_KEYS) != NULL;
    for (uint8_t i = 0; i < KEYBOARD_REPORT_KEYS; ++i) {
        uint8_t keycode = report->keys[i];
        if (keycode < KC_A || keycode >= KC_LCTL || memchr(previous_report.keys, keycode, KEYBOARD_REPORT_KEYS)) continue;
        memmove(state.key, state.key + 1, 2 * sizeof(state.key[0]));
        memmove(state.last_mods, state.last_mods + 1, 2);
        label(keycode, state.key[2]);
        bool shifted = report->mods & MOD_MASK_SHIFT;
        bool shortcut = report->mods & (MOD_MASK_GUI | MOD_MASK_ALT | MOD_MASK_CTRL);
        state.last_mods[2] = shortcut ? report->mods : 0;
        if (keycode >= KC_A && keycode <= KC_Z) {
            if (!shortcut && !(shifted ^ host_keyboard_led_state().caps_lock)) state.key[2][0] += 'a' - 'A';
        } else {
            const char plain[] = "1234567890-=[]\\;'/.,`";
            const char upper[] = "!@#$%^&*()_+{}|:\"?><~";
            const char *match = strchr(plain, state.key[2][0]);
            if (shifted && state.key[2][1] == '\0' && match) state.key[2][0] = upper[match - plain];
        }
        if (keycode == KC_SPC) ++state.pet.jumps;
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
    state.layers = layer_state | default_layer_state;
    state.pet.mods = get_mods() | get_weak_mods();
#ifndef NO_ACTION_ONESHOT
    state.pet.mods |= get_oneshot_mods();
#endif
    state.pet.wpm = get_current_wpm();
    state.pet.caps = host_keyboard_led_state().caps_lock;
    state.pet.awake = last_input_activity_elapsed() < OLED_TIMEOUT || last_led_activity_elapsed() < OLED_TIMEOUT;
    // Throttle failures too, so a disconnected half cannot stall every scan.
    if (timer_elapsed32(last_attempt) >= 50) {
        last_attempt = timer_read32();
        transaction_rpc_send(EVA_OLED_SYNC, sizeof(state), &state);
    }
}

// Reuse the OLED driver's font so pixel-centered labels need no duplicate bitmap.
extern const unsigned char font[] PROGMEM;
static void text_at(uint8_t row, const char *text) {
    uint8_t width = 6 * strlen(text), left = (32 - width) / 2;
    for (uint8_t x = 0; x < 32; ++x) {
        uint8_t column = 0;
        if (x >= left && x < left + width) {
            uint8_t offset = x - left;
            column = pgm_read_byte(&font[(text[offset / 6] - 32) * 6 + offset % 6]);
        }
#ifdef EVA_OLED_SPLIT_STATUS
        if (is_keyboard_left()) {
            for (uint8_t y = 0; y < 8; ++y)
                oled_write_pixel(x, row * 8 + 22 + y, column & (1 << y));
        } else
#endif
            oled_write_raw_byte(column, row * 32 + x);
    }
}

#ifndef EVA_OLED_SPLIT_STATUS
static void icon_at(uint8_t left, uint8_t top, const uint16_t icon[EVA_ICON_SIZE], bool inverted) {
    for (uint8_t y = 0; y < EVA_ICON_SIZE; ++y) {
        uint16_t row = pgm_read_word(&icon[y]);
        for (uint8_t x = 0; x < EVA_ICON_SIZE; ++x)
            oled_write_pixel(left + x, top + y, !!(row & (1 << (EVA_ICON_SIZE - 1 - x))) ^ inverted);
    }
}
#endif

static void render_modifiers(void) {
    for (uint8_t i = 0; i < 4; ++i) {
#ifdef EVA_OLED_SPLIT_STATUS
        uint8_t left = 16 * (i % 2), top = 70 + 17 * (i / 2);
        const uint8_t size = 16, glyph_size = 12, padding = 2;
#else
        uint8_t left = 18 * (i % 2), top = 60 + 20 * (i / 2);
        const uint8_t size = 14, glyph_size = 8, padding = 3;
#endif
        for (uint8_t y = 0; y < size; ++y) {
            bool glyph_row = y >= padding && y < padding + glyph_size;
            uint16_t row = glyph_row ? pgm_read_word(&eva_icons[i][1 + ((y - padding) * 12 + glyph_size / 2) / glyph_size]) : 0;
            uint8_t inset = y == 0 || y == size - 1 ? 2 : y == 1 || y == size - 2 ? 1 : 0;
            for (uint8_t x = 0; x < size; ++x) {
                bool glyph = glyph_row && x >= padding && x < padding + glyph_size &&
                             (row & (1 << (12 - ((x - padding) * 12 + glyph_size / 2) / glyph_size)));
                bool on = glyph ^ !!(state.pet.mods & masks[i]);
                if (x < inset || x >= size - inset) on = false;
                else if (y == 0 || y == size - 1 || x == inset || x == size - 1 - inset) on = true;
                oled_write_pixel(left + x, top + y, on);
            }
        }
    }
}

static void render_history(uint8_t first, uint8_t row) {
    for (uint8_t key = first; key < 3; ++key) {
        char chord[5] = {0};
        uint8_t length = 0;
        for (uint8_t i = 0; i < 4; ++i)
            if (state.last_mods[key] & masks[i]) chord[length++] = "MACS"[i];
        text_at(row, chord);
        text_at(row + 1, state.key[key]);
        row += 2;
    }
}

bool eva_oled_render(void) {
    if (!state.pet.awake) {
        oled_off();
        return false;
    }
#ifdef EVA_OLED_SPLIT_STATUS
    if (is_keyboard_left()) {
        oled_on();
        uint8_t layer = state.layer > 3 ? 0 : state.layer;
        // Composite before writing so unchanged planes cannot starve later dirty blocks.
        for (uint8_t y = 0; y < 24; ++y)
            for (uint8_t x = 0; x < 32; ++x) {
                bool on = false;
                uint8_t distance = x > 15 ? x - 15 : 15 - x;
                for (uint8_t i = 0; i < 4; ++i) {
                    int8_t plane_y = y - 14 + 4 * i;
                    if (plane_y < 0 || plane_y >= 9) continue;
                    uint8_t span = 2 + 3 * (plane_y < 5 ? plane_y : 8 - plane_y);
                    if (distance <= span) on = distance + 3 > span || i == layer;
                }
                oled_write_pixel(x, 22 + y, on);
            }
        static const char PROGMEM names[4][2][6] = {{"base", ""}, {"sym", "bol"}, {"func", "tions"}, {"opera", "tions"}}; // cspell:ignore tions
        for (uint8_t line = 0; line < 2; ++line) {
            char name[6];
            strcpy_P(name, names[layer][line]);
            text_at(3 + line, name);
        }
        render_modifiers();
    } else {
        render_luna(&state.pet);
        render_history(0, 7);
    }
#else
    icon_at(4, 4, eva_icons[EVA_LAYERS], false);
    static const uint8_t PROGMEM numbers[3][5] = {{2, 6, 2, 2, 7}, {6, 1, 2, 4, 7}, {6, 1, 2, 1, 6}};
    uint8_t layer = state.layer > 2 ? 2 : state.layer;
    for (uint8_t y = 0; y < 5; ++y)
        for (uint8_t x = 0; x < 3; ++x)
            oled_write_pixel(24 + x, 8 + y, pgm_read_byte(&numbers[layer][y]) & (1 << (2 - x)));
    render_luna(&state.pet);
    render_modifiers();
    render_history(1, 12);
#endif
    return false;
}
