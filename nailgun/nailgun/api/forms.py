import re

import simplejson as json
from django.core.exceptions import ValidationError
from django import forms
from django.forms.fields import Field, IntegerField, CharField, ChoiceField
from django.core.validators import RegexValidator

from nailgun.models import Cluster, Node, Recipe, Role, Release


class RecipeForm(forms.ModelForm):

    class Meta:
        model = Recipe


def validate_role_recipes(value):
    if value and isinstance(value, list):
        if not any([re.match(r'^[^\]]+::([^\]]+)@[0-9]+(\.[0-9]+){1,2}$', i) \
                for i in value]):
            raise ValidationError('Recipe should be in \
cookbook::recipe@version format')
        for i in value:
            try:
                rec_exist = Recipe.objects.get(recipe=i)
            except Recipe.DoesNotExist:
                raise ValidationError('Recipe %s does not exist' % i)
    else:
        raise ValidationError('Invalid recipe list')


class RoleForm(forms.ModelForm):
    recipes = Field(validators=[validate_role_recipes])

    class Meta:
        model = Role


class ClusterForm(forms.Form):
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
            if not re.match(r'^[^\]]+::([^\]]+)@[0-9]+(\.[0-9]+){1,2}$', \
                    recipe):
                raise ValidationError('Recipe should be in a \
cook_name::recipe_name@cook_version format')
            try:
                rec_exists = Recipe.objects.get(recipe=recipe)
            except Recipe.DoesNotExist:
                raise ValidationError('Recipe %s doesn\'t exist' % recipe)


validate_node_id = RegexValidator(regex=re.compile('^[\dA-F]{12}$'))


class NodeUpdateForm(forms.Form):
    metadata = Field(required=False, validators=[validate_node_metadata])
    status = ChoiceField(required=False, choices=Node.NODE_STATUSES)
    name = CharField(max_length=100, required=False)
    fqdn = CharField(max_length=255, required=False)
    ip = CharField(max_length=15, required=False)
    mac = CharField(max_length=17, required=False)
    roles = Field(required=False, validators=[validate_node_roles])
    cluster_id = IntegerField(required=False)


class NodeCreationForm(NodeUpdateForm):
    id = CharField(validators=[validate_node_id])


class ReleaseCreationForm(forms.ModelForm):
    roles = Field(validators=[validate_release_node_roles])

    class Meta:
        model = Release

    def clean(self):
        return self.cleaned_data
