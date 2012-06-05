import re
import simplejson as json
from django.core.exceptions import ValidationError
from django import forms
from django.forms.fields import Field, IntegerField, CharField, ChoiceField
from django.core.validators import RegexValidator
from nailgun.models import Environment, Node, Cookbook, Role, Release


class CookbookForm(forms.ModelForm):
    class Meta:
        model = Cookbook


class RoleForm(forms.Form):
    name = CharField(max_length=50)
    cookbook_id = IntegerField()


class EnvironmentForm(forms.Form):
    name = CharField(max_length=100, required=False)


def validate_node_metadata(value):
    if value is not None:
        if isinstance(value, dict):
            for field in ('block_device', 'interfaces', 'cpu', 'memory'):
                # TODO(mihgen): We need more comprehensive checks here
                # For example, now, it's possible to store value[field] = []
                if not field in value or value[field] == "":
                    raise ValidationError("Node metadata '%s' \
                            field is required" % field)
        else:
            raise ValidationError('Node metadata must be a dictionary')


def validate_node_roles(value):
    if not isinstance(value, list) or \
        not all(map(lambda i: isinstance(i, int), value)):
            raise ValidationError('Role list must be a list of integers')


def validate_release_node_roles(data):
    if not data or not isinstance(data, list):
        raise ValidationError('Empty roles list')
    if not all(map(lambda i: 'name' in i, data)):
        raise ValidationError('Role name is empty')
    for role in data:
        for recipe in role['recipes']:
            if not re.match(r'\w+@[\w\.]+::\w+', recipe):
                raise ValidationError('Recipe should be in a \
cook_name@cook_version::recipe_name format')
            cookbook, version, recipe_name = re.split(r'@|::', recipe)
            try:
                cb_exists = Cookbook.objects.get(
                    name=cookbook,
                    version=version
                )
            except Cookbook.DoesNotExist:
                raise ValidationError('Cookbook %s doesn\'t exist' % cookbook)
            if recipe_name not in cb_exists.recipes:
                raise ValidationError('Recipe %s doesn\'t exist in %s' % (
                    recipe, cookbook)
                )


validate_node_id = RegexValidator(regex=re.compile('^[\dA-F]{12}$'))


class NodeUpdateForm(forms.Form):
    metadata = Field(required=False, validators=[validate_node_metadata])
    status = ChoiceField(required=False, choices=Node.NODE_STATUSES)
    name = CharField(max_length=100, required=False)
    fqdn = CharField(max_length=255, required=False)
    ip = CharField(max_length=15, required=False)
    mac = CharField(max_length=17, required=False)
    roles = Field(required=False, validators=[validate_node_roles])
    environment_id = IntegerField(required=False)


class NodeCreationForm(NodeUpdateForm):
    id = CharField(validators=[validate_node_id])


class ReleaseCreationForm(forms.ModelForm):
    roles = Field(validators=[validate_release_node_roles])

    class Meta:
        model = Release

    def clean(self):
        name, version = self.cleaned_data['name'], self.cleaned_data['version']
        try:
            release = Release.objects.get(name=name, version=version)
            raise ValidationError('Release already exists')
        except Release.DoesNotExist:
            pass
        return self.cleaned_data
