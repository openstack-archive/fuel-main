import unittest
from devops import scancodes

class TestScancodes(unittest.TestCase):

    def test_abc(self):
        codes = scancodes.from_string('abc')
        self.assertEqual([(0x1e,), (0x30,), (0x2e,)], codes)

    def test_ABC(self):
        codes = scancodes.from_string('ABC')
        self.assertEqual([(0x2a, 0x1e), (0x2a, 0x30), (0x2a, 0x2e)], codes)

    def test_specials(self):
        codes = scancodes.from_string('<Esc>a<Up>b')
        self.assertEqual([(0x01,), (0x1e,), (0x48,), (0x30,)], codes)

    def test_newlines_are_ignored(self):
        codes = scancodes.from_string("a\nb")
        self.assertEqual([(0x1e,), (0x30,)], codes)

    def test_wait(self):
        codes = scancodes.from_string("a<Wait>b")
        self.assertEqual([(0x1e,), ('wait',), (0x30,)], codes)

