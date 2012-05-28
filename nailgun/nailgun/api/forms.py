from django.core.exceptions import ValidationError
from django import forms
from django.forms.fields import Field, IntegerField, CharField, ChoiceField
from nailgun.models import Environment, Node, Cookbook, Role


class EnvironmentForm(forms.ModelForm):
    class Meta:
        model = Environment


class CookbookForm(forms.ModelForm):
    class Meta:
        model = Cookbook


def validate_node_metadata(value):
    if value is not None:
        if isinstance(value, dict):
            for field in ('block_device', 'interfaces', 'cpu', 'memory'):
                if not field in value:
                    raise ValidationError("Node metadata '%s' \
                            field is required" % field)
        else:
            raise ValidationError('Node metadata must be a dictionary')


class NodeForm(forms.Form):
    metadata = Field(required=False, validators=[validate_node_metadata])
    status = ChoiceField(required=False, choices=Node.NODE_STATUSES)
    name = CharField(max_length=100, required=False)


class NodeUpdateForm(NodeForm):
    environment_id = IntegerField(required=False)


class NodeCreationForm(NodeUpdateForm):
    id = CharField(max_length=12)
