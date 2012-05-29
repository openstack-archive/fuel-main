import re
from django.core.exceptions import ValidationError
from django import forms
from django.forms.fields import Field, IntegerField, CharField, ChoiceField
from django.core.validators import RegexValidator
from nailgun.models import Environment, Node, Cookbook, Role


class CookbookForm(forms.ModelForm):
    class Meta:
        model = Cookbook


class EnvironmentForm(forms.Form):
    name = CharField(max_length=100, required=False)


def validate_node_metadata(value):
    if value is not None:
        if isinstance(value, dict):
            for field in ('block_device', 'interfaces', 'cpu', 'memory'):
                if not field in value:
                    raise ValidationError("Node metadata '%s' \
                            field is required" % field)
        else:
            raise ValidationError('Node metadata must be a dictionary')


def validate_node_roles(value):
    if not isinstance(value, list) or \
        not all(map(lambda i: isinstance(i, int), value)):
            raise ValidationError('Role list must be a list of integers')



validate_node_id = RegexValidator(regex=re.compile('^[\dA-F]{12}$'))


class NodeForm(forms.Form):
    metadata = Field(required=False, validators=[validate_node_metadata])
    status = ChoiceField(required=False, choices=Node.NODE_STATUSES)
    name = CharField(max_length=100, required=False)
    roles = Field(required=False, validators=[validate_node_roles])


class NodeUpdateForm(NodeForm):
    environment_id = IntegerField(required=False)


class NodeCreationForm(NodeUpdateForm):
    id = CharField(validators=[validate_node_id])
