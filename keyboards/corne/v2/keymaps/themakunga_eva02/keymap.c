// SPDX-License-Identifier: GPL-2.0-or-later
#include QMK_KEYBOARD_H
#include "eva_oled.h"

enum tap_dance_actions { TD_SPC_ENT };
tap_dance_action_t tap_dance_actions[] = {
    [TD_SPC_ENT] = ACTION_TAP_DANCE_DOUBLE(KC_SPC, KC_ENT),
};

const key_override_t sft_td_ent = ko_make_basic(MOD_MASK_SHIFT, TD(TD_SPC_ENT), KC_ENT);
const key_override_t *key_overrides[] = {&sft_td_ent, NULL};

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [0] = LAYOUT_split_3x6_3(
        KC_ESC,  KC_Q,    KC_W,    KC_E,    KC_R,    KC_T,    KC_Y,    KC_U,    KC_I,    KC_O,    KC_P,    KC_BSPC,
        KC_LCTL, KC_A,    KC_S,    KC_D,    KC_F,    KC_G,    KC_H,    KC_J,    KC_K,    KC_L,    KC_SCLN, KC_QUOT,
        KC_LSFT, KC_Z,    KC_X,    KC_C,    KC_V,    KC_B,    KC_N,    KC_M,    KC_COMM, KC_DOT,  KC_SLSH, KC_RSFT,
                                 KC_LGUI, MO(1),   TD(TD_SPC_ENT), KC_SPC, MO(2), KC_LALT
    ),
    [1] = LAYOUT_split_3x6_3(
        KC_TAB,  KC_1,    KC_2,    KC_3,    KC_4,    KC_5,    KC_6,    KC_7,    KC_8,    KC_9,    KC_0,    KC_DEL,
        KC_TRNS, KC_EXLM, KC_AT,   KC_HASH, KC_DLR,  KC_PERC, KC_LCBR, KC_RCBR, KC_UNDS, KC_PLUS, KC_COLN, KC_DQUO,
        KC_TRNS, KC_BSLS, KC_GRV,  KC_LBRC, KC_RBRC, KC_EQL,  KC_MINS, KC_PIPE, KC_LABK, KC_RABK, KC_QUES, KC_TRNS,
                                 KC_TRNS, KC_TRNS, KC_ENT,  KC_ENT,  KC_TRNS, KC_TRNS
    ),
    [2] = LAYOUT_split_3x6_3(
        KC_F11,  KC_F1,   KC_F2,   KC_F3,   KC_F4,   KC_F5,   KC_F6,   KC_F7,   KC_F8,   KC_F9,   KC_F10,  KC_F12,
        KC_TRNS, KC_VOLD, KC_VOLU, RM_VALD, RM_VALU, RM_TOGG, KC_LEFT, KC_DOWN, KC_UP,   KC_RGHT, KC_DEL,  KC_BSPC,
        KC_TRNS, RM_PREV, RM_NEXT, RM_HUED, RM_HUEU, KC_MPLY, KC_MPRV, KC_MNXT, KC_MUTE, KC_MSTP, G(C(KC_Q)), KC_TRNS,
                                 KC_TRNS, KC_TRNS, KC_ENT,  KC_ENT,  KC_TRNS, KC_TRNS
    ),
};

void keyboard_post_init_user(void) { eva_oled_init(); }

void housekeeping_task_user(void) { eva_oled_housekeeping(); }

oled_rotation_t oled_init_user(oled_rotation_t rotation) {
    (void)rotation;
    return OLED_ROTATION_270;
}

bool oled_task_user(void) { return eva_oled_render(); }
