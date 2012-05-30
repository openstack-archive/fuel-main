import unittest
from . import scancodes

class TestScancodes(unittest.TestCase):

    def test_abc(self):
        codes = scancodes.from_string('abc')
        self.assertEqual('1e 9e 30 b0 2e ae', codes)

    def test_ABC(self):
        codes = scancodes.from_string('ABC')
        self.assertEqual('2a 1e aa 9e 2a 30 aa b0 2a 2e aa ae', codes)

    def test_specials(self):
        codes = scancodes.from_string('<Esc>a<Up>b')
        self.assertEqual('01 81 1e 9e 48 c8 30 b0', codes)

