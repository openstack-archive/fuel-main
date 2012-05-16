import os
from django import template
from django.contrib.staticfiles.finders import FileSystemFinder

TEMPLATE_EXTENSION = '.html'

register = template.Library()
finder = FileSystemFinder()

@register.simple_tag
def jst(template_name):
    template_filename = os.path.join('jst', template_name + TEMPLATE_EXTENSION)
    
    match = finder.find(template_filename)
    if not match:
        raise Exception("JS template '%s' not found" % template_filename)
    
    f = open(match, 'r')
    
    template_content = f.read()
    
    return "<script type=\"text/template\" id=\"tpl_%s\">\n%s\n</script>" % \
        (template_name, template_content)
