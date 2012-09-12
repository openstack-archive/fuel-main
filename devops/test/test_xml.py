from devops import xml
import unittest


class TestXml(unittest.TestCase):
    def test_parsing_returns_root_element(self):
        d = xml.parse_string("<a><b /></a>")
        self.assertIsNotNone(d)
        self.assertEquals('a', d.tag)

    def test_finding_descendants(self):
        d = xml.parse_string("<a><b><c><d /></c></b></a>")
        e = d.find('b/c')
        self.assertIsNotNone(e)
        self.assertEquals('c', e.tag)

    def test_finding_attribute_values(self):
        d = xml.parse_string("<a><b><c name='foo'></c></b></a>")
        self.assertEquals('foo', d.find('b/c/@name'))

    def test_finding_all_descendants(self):
        d = xml.parse_string("<a><b><c name='foo'></c></b><b /></a>")
        nodes = d.find_all('b')
        self.assertEquals(2, len(nodes))
        self.assertEquals('b', nodes[0].tag)
        self.assertEquals('b', nodes[1].tag)

    def test_finding_absolute_values(self):
        d = xml.parse_string("<a><b><c name='foo'></c></b><b /></a>")
        nodes = d.find_all('/a/b')
        self.assertEquals(2, len(nodes))

    def test_getting_node_text(self):
        d = xml.parse_string("<a><b>foo</b></a>")
        e = d.find('b')
        self.assertEquals('foo', e.text)

    def test_finding_node_text(self):
        d = xml.parse_string("<a><b>foo</b></a>")
        self.assertEquals('foo', d.find('b/text()'))
