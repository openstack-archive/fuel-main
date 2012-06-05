import re
from django.db import models
from django import forms


class RecipeField(models.CharField):

    def __init__(self, *args, **kwargs):
        super(RecipeField, self).__init__(*args, **kwargs)


class RecipeListFormField(forms.CharField):

    def __init__(self, *args, **kwargs):
        super(RecipeListFormField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            return ()
        return tuple(re.split(r'@|::', value))
