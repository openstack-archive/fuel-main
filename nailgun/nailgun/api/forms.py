import re

import simplejson as json
from django.core.exceptions import ValidationError
from django import forms
from django.forms.fields import Field, IntegerField, CharField, ChoiceField, \
                                BooleanField
from django.core.validators import RegexValidator

from nailgun.models import Cluster
from nailgun.models import Node
from nailgun.models import Role
from nailgun.models import Release
from nailgun.models import Network
from nailgun.models import Point
from nailgun.models import Com

import nailgun.api.validators as vld

import logging


logger = logging.getLogger('forms')


class RoleFilterForm(forms.Form):
    node_id = Field(required=False, validators=[vld.validate_node_id])
    release_id = Field(required=False, validators=[])


class RoleCreateForm(forms.ModelForm):
    components = Field(validators=[], required=False)

    def clean_components(self):

        return [c.name for c in Com.objects.filter(
            name__in=self.data['components'],
            release=Release.objects.get(id=self.data['release'])
            )]

    class Meta:
        model = Role


class PointFilterForm(forms.Form):
    release = IntegerField(required=False)


class PointUpdateForm(forms.ModelForm):
    scheme = Field(validators=[])

    class Meta:
        model = Point
        exclude = ('name', 'release', 'provided_by', 'required_by')


class PointCreateForm(forms.ModelForm):
    scheme = Field(required=False, validators=[])

    class Meta:
        model = Point
        exclude = ('provided_by', 'required_by')


class ComFilterForm(forms.Form):
    release = IntegerField(required=False)


class ComCreateForm(forms.ModelForm):
    deploy = Field(validators=[])
    requires = Field(validators=[], required=False)
    provides = Field(validators=[], required=False)

    def clean_requires(self):

        return [p.name for p in Point.objects.filter(
            name__in=self.data['requires'],
            release=Release.objects.get(id=self.data['release'])
            )]

    def clean_provides(self):

        return [p.name for p in Point.objects.filter(
            name__in=self.data['provides'],
            release=Release.objects.get(id=self.data['release'])
            )]

    class Meta:
        model = Com
        exclude = ('roles')


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
    os_platform = CharField(max_length=150, required=False)
    roles = Field(required=False, validators=[vld.forbid_modifying_roles])
    new_roles = Field(required=False, validators=[vld.validate_node_roles])
    redeployment_needed = BooleanField(required=False)


class NodeCreationForm(NodeForm):
    id = CharField(validators=[vld.validate_node_id])


class NodeFilterForm(forms.Form):
    cluster_id = IntegerField(required=False)


class ReleaseCreationForm(forms.ModelForm):
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
