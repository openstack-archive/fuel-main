
# Based on http://www.win.tue.nl/~aeb/linux/kbd/scancodes-1.html
# Scancodes < 0x80 - key presses, > 0x80 - key releases
SCANCODES = {
    '1': '02 82',
    '2': '03 83',
    '3': '04 84',
    '4': '05 85',
    '5': '06 86',
    '6': '07 87',
    '7': '08 88',
    '8': '09 89',
    '9': '0a 8a',
    '0': '0b 8b',
    '-': '0c 8c',
    '=': '0d 8d',

    'q': '10 90',
    'w': '11 91',
    'e': '12 92',
    'r': '13 93',
    't': '14 94',
    'y': '15 95',
    'u': '16 96',
    'i': '17 97',
    'o': '18 98',
    'p': '19 99',

    'Q': '2a 10 aa 90',
    'W': '2a 11 aa 91',
    'E': '2a 12 aa 92',
    'R': '2a 13 aa 93',
    'T': '2a 14 aa 94',
    'Y': '2a 15 aa 95',
    'U': '2a 16 aa 96',
    'I': '2a 17 aa 97',
    'O': '2a 18 aa 98',
    'P': '2a 19 aa 99',

    'a': '1e 9e',
    's': '1f 9f',
    'd': '20 a0',
    'f': '21 a1',
    'g': '22 a2',
    'h': '23 a3',
    'j': '24 a4',
    'k': '25 a5',
    'l': '26 a6',

    'A': '2a 1e aa 9e',
    'S': '2a 1f aa 9f',
    'D': '2a 20 aa a0',
    'F': '2a 21 aa a1',
    'G': '2a 22 aa a2',
    'H': '2a 23 aa a3',
    'J': '2a 24 aa a4',
    'K': '2a 25 aa a5',
    'L': '2a 26 aa a6',

    ';': '27 a7',
    '"': '2a 28 aa a8',
    '\'': '28 a8',

    '\\': '2b ab',
    '|': '2a 2b aa 8b',

    '[': '1a 9a',
    ']': '1b 9b',
    '<': '2a 33 aa b3',
    '>': '2a 34 aa b4',
    '?': '2a 35 aa b5',
    '$': '2a 05 aa 85',
    '+': '2a 0d aa 8d',

    'z': '2c ac',
    'x': '2d ad',
    'c': '2e ae',
    'v': '2f af',
    'b': '30 b0',
    'n': '31 b1',
    'm': '32 b2',

    'Z': '2a 2c aa ac',
    'X': '2a 2d aa ad',
    'C': '2a 2e aa ae',
    'V': '2a 2f aa af',
    'B': '2a 30 aa b0',
    'N': '2a 31 aa b1',
    'M': '2a 32 aa b2',

    ',': '33 b3',
    '.': '34 b4',
    '/': '35 b5',
    ':': '2a 27 aa a7',
    '%': '2a 06 aa 86',
    '_': '2a 0c aa 8c',
    '&': '2a 08 aa 88',
    '(': '2a 0a aa 8a',
    ')': '2a 0b aa 8b',

    ' ': '39 b9'
}

SPECIALS = {
    '<Enter>': '1c 9c',
    '<Return>': '1c 9c',
    '<Backspace>': '0e 8e',
    '<Spacebar>': '39 b9',
    '<Esc>': '01 81',
    '<Tab>': '0f 8f',
    '<KillX>': '1d 38 0e',
    '<Wait>': 'wait',

    '<PageUp>': '49 c9',
    '<PageDown>': '51 d1',
    '<Home>': '47 c7',
    '<End>': '4f cf',
    '<Insert>': '52 d2',
    '<Delete>': '53 d3',
    '<Left>': '4b cb',
    '<Right>': '4d cd',
    '<Up>': '48 c8',
    '<Down>': '50 d0',

    '<F1>': '3b',
    '<F2>': '3c',
    '<F3>': '3d',
    '<F4>': '3e',
    '<F5>': '3f',
    '<F6>': '40',
    '<F7>': '41',
    '<F8>': '42',
    '<F9>': '43',
    '<F10>': '44'
}

def from_string(s):
    "from_string(s) - Convert string of chars into string of corresponding scancodes."
    scancodes = ''

    while len(s) > 0:
        if s[0] == '<' and s.find('>') > 0:
            special_end = s.find('>')+1
            special = s[0:special_end]
            special_scancodes = SPECIALS.get(special)
            if special_scancodes:
                scancodes += special_scancodes + ' '

            s = s[special_end:]
        else:
            key = s[0]
            key_scancodes = SCANCODES.get(key)
            if key_scancodes:
                scancodes += key_scancodes + ' '

            s = s[1:]

    return scancodes.strip()

