"""Check EVA02 hardware assumptions, usable layers and the documented layout."""
import json
import re
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

root = Path(__file__).resolve().parents[1]
board_path = root / 'keyboards/corne/v2'
board = json.loads((board_path / 'keyboard.json').read_text())
assert board['keyboard_name'] == 'Corne v2' and board['maintainer'] == 'themakunga'
assert board['development_board'] == 'promicro'
assert board['matrix_pins'] == {'cols': ['F4', 'F5', 'F6', 'F7', 'B1', 'B3'],
                               'rows': ['D4', 'C6', 'D7', 'E6']}
assert board['split']['serial']['pin'] == 'D2' and board['ws2812']['pin'] == 'D3'
assert board['rgb_matrix']['split_count'] == [27, 27]
positions = board['layouts']['LAYOUT_split_3x6_3']['layout']
assert len(positions) == len({tuple(key['matrix']) for key in positions}) == 42

source = (board_path / 'keymaps/themakunga_eva02/keymap.c').read_text()
blocks = re.findall(r'\[([012])\] = LAYOUT_split_3x6_3\((.*?)\n    \)', source, re.S)
assert [index for index, _ in blocks] == ['0', '1', '2']
layers = [[code.strip() for code in body.split(',')] for _, body in blocks]
assert all(len(layer) == 42 for layer in layers)
assert layers[0][12] == 'KC_LCTL'
assert layers[0][36:] == ['KC_LGUI', 'MO(1)', 'TD(TD_SPC_ENT)', 'KC_SPC', 'MO(2)', 'KC_LALT']
assert layers[1][36:] == ['KC_TRNS', 'KC_TRNS', 'KC_ENT', 'KC_TRNS', 'KC_TRNS', 'KC_TRNS']
assert layers[2][36:] == ['KC_TRNS', 'KC_TRNS', 'KC_TRNS', 'KC_ENT', 'KC_TRNS', 'KC_TRNS']
assert layers[1][1:11] == [f'KC_{n % 10}' for n in range(1, 11)]
assert layers[1][0] == 'KC_TAB'
assert {'KC_LEFT', 'KC_DOWN', 'KC_UP', 'KC_RGHT'} <= set(layers[2])
assert {f'KC_F{n}' for n in range(1, 13)} <= set(layers[2])
sofle = (root / 'keyboards/sofle/v2/keymaps/themakunga_eva01/keymap.c').read_text()
base = re.search(r'\[0\] = LAYOUT\((.*?)\n    \)', sofle, re.S).group(1)
base = [code.strip() for code in base.split(',')]
assert layers[0][1:11] == base[13:23]
assert layers[0][12:36] == base[24:42] + base[44:50]
assert 'ACTION_TAP_DANCE_DOUBLE(KC_SPC, KC_ENT)' in source
assert 'ko_make_basic(MOD_MASK_SHIFT, TD(TD_SPC_ENT), KC_ENT)' in source
assert 'return eva_oled_render();' in source
assert 'eva_oled_record(keycode, record);' in source
assert (board_path / 'keymaps/themakunga_eva02/keymap.c').is_file()
config = board_path / 'keymaps/themakunga_eva02/config.h'
macros = subprocess.run(['cc', '-E', '-dM', '-Werror', '-D', 'RGB_MATRIX_MAXIMUM_BRIGHTNESS=120',
                         '-x', 'c', '-'], input=f'#include "{config}"\n', text=True,
                        check=True, capture_output=True).stdout
assert '#define RGB_MATRIX_MAXIMUM_BRIGHTNESS 100\n' in macros

ns = {'svg': 'http://www.w3.org/2000/svg'}
svg = ET.parse(root / 'docs/eva02-layout.svg')
groups = [group for group in svg.findall('.//svg:g', ns) if group.find('svg:title', ns) is not None]
assert len(groups) == 126
for layer, codes in enumerate(layers):
    for index, (position, original) in enumerate(zip(positions, codes)):
        group = groups[layer * 42 + index]
        code = layers[0][index] if original == 'KC_TRNS' else original
        assert group.find('svg:title', ns).text == f'QMK {layer}, posición {index}: {original}; acción {code}'
        if index in (36, 38, 39):
            labels = {'KC_LGUI': ['Cmd'], 'TD(TD_SPC_ENT)': ['Space', '/ Enter'],
                      'KC_SPC': ['Space'], 'KC_ENT': ['Enter']}
            assert [label.text for label in group.findall('svg:text', ns)] == labels[code]
        key = group.find('svg:rect', ns)
        assert abs(float(key.attrib['x']) - (80 + position['x'] * 64)) < 0.01
        assert abs(float(key.attrib['y']) - (166 + layer * 410 + position['y'] * 64)) < 0.01
print('EVA02: hardware, layer access, EVA01 letter positions and 126 diagram keys verified.')
