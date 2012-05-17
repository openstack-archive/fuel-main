from django import forms
from nailgun.models import Environment, Node, Role

class EnvironmentForm(forms.ModelForm):
    class Meta:
        model = Environment
