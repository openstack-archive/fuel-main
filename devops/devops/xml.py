from lxml import etree

class Element:
    def __init__(self, element):
        self.element = element
        self.tag = self.element.tag
        self.text = self.element.text

    def __getitem__(self, name, default=None):
        return self.element.get(name, default)

    def __setitem__(self, name, value):
        return self.element.set(name, value)

    def find_all(self, xpath):
        "find_all(xpath) - returns list of elements matching given XPath"
        results = []
        for e in self.element.xpath(xpath):
            if hasattr(e, 'xpath'):
                # wrap element nodes with our class
                e = Element(e)
            else:
                e = str(e)
            results.append(e)
        return results

    def find(self, xpath):
        "find(xpath) - returns first element matching given XPath or None"
        elements = self.find_all(xpath)
        if len(elements) == 0:
            return None

        return elements[0]

def parse_file(path):
    "parse_file(path) - parse file contents as XML and return XML document object."
    with file(path) as f:
        return parse_stream(f)

def parse_stream(stream):
    "parse_stream(stream) - parse stream as XML and return XML document object."
    return parse_string(stream.read())

def parse_string(s):
    "parse_string(s) - parse string as XML and return XML document object."
    return Element(etree.fromstring(s))

