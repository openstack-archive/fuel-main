import re

import simplejson as json
from django.core.exceptions import ValidationError
from django import forms
from django.forms.fields import Field, IntegerField, CharField, ChoiceField, \
                                BooleanField
from django.core.validators import RegexValidator

from nailgun.models import Cluster, Node, Recipe, Role, Release, Network, \
        Attribute
import nailgun.api.validators as vld


class RecipeForm(forms.ModelForm):
    depends = Field(required=False)

    class Meta:
        model = Recipe

    def clean(self):
        return self.cleaned_data

    def clean_depends(self):
        for depend in self.cleaned_data['depends']:
            vld.validate_recipe(depend)
        return self.cleaned_data['depends']

    def clean_attribute(self):
        return self.cleaned_data['attribute']

    def clean_recipe(self):
        vld.validate_recipe(self.cleaned_data['recipe'])
        return self.cleaned_data['recipe']


class RoleForm(forms.ModelForm):
    recipes = Field(validators=[vld.validate_role_recipes])

    class Meta:
        model = Role


class AttributeForm(forms.ModelForm):
    attribute = Field(validators=[vld.validate_attribute])

    class Meta:
        model = Attribute


class RoleFilterForm(forms.Form):
    node_id = Field(required=False, validators=[vld.validate_node_id])


class ClusterForm(forms.Form):
    name = CharField(max_length=100, required=False)
    nodes = Field(required=False, validators=[vld.validate_node_ids])
    task = Field(required=False, validators=[vld.forbid_modifying_tasks])


class ClusterCreationForm(forms.ModelForm):
    nodes = Field(required=False, validators=[vld.validate_node_ids])
    task = Field(required=False, validators=[vld.forbid_modifying_tasks])

    class Meta:
        model = Cluster


class NodeForm(forms.Form):
    metadata = Field(required=False, validators=[vld.validate_node_metadata])
    status = ChoiceField(required=False, choices=Node.NODE_STATUSES)
    name = CharField(max_length=100, required=False)
    fqdn = CharField(max_length=255, required=False)
    ip = CharField(max_length=15, required=False)
    mac = CharField(max_length=17, required=False)
    manufacturer = CharField(max_length=50, required=False)
    platform_name = CharField(max_length=150, required=False)
    roles = Field(required=False, validators=[vld.forbid_modifying_roles])
    new_roles = Field(required=False, validators=[vld.validate_node_roles])
    redeployment_needed = BooleanField(required=False)


class NodeCreationForm(NodeForm):
    id = CharField(validators=[vld.validate_node_id])


class NodeFilterForm(forms.Form):
    cluster_id = IntegerField(required=False)


class ReleaseCreationForm(forms.ModelForm):
    roles = Field(validators=[vld.validate_release_node_roles])
    networks_metadata = Field(validators=[vld.validate_networks_metadata])

    class Meta:
        model = Release

    def clean(self):
        return self.cleaned_data


class NetworkCreationForm(forms.ModelForm):
    release = CharField()
    network = CharField(validators=[vld.validate_network])
    range_l = CharField(validators=[vld.validate_ip])
    range_h = CharField(validators=[vld.validate_ip])
    gateway = CharField(validators=[vld.validate_ip])

    class Meta:
        model = Network

    def clean_release(self):
        release_id = self.cleaned_data["release"]
        if not release_id:
            raise ValidationError("Release id not specified!")
        try:
            r = Release.objects.get(id=release_id)
        except Release.DoesNotExist:
            raise ValidationError("Invalid release id!")

        #self.instance.release = r
        return r
