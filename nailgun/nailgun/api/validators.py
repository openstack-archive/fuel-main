import json
import re

import ipaddr
from piston.utils import FormValidationError, HttpStatusCode, rc
from piston.decorator import decorator

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from nailgun.models import Cluster, Node, Recipe, Role, Release, Network


# Handler decorator for JSON validation using forms
def validate_json(v_form):
    @decorator
    def wrap(f, self, request, *a, **kwa):
        content_type = request.content_type.split(';')[0]
        if content_type != "application/json":
            response = rc.BAD_REQUEST
            response.content = "Invalid content type, must be application/json"
            raise HttpStatusCode(response)

        try:
            parsed_body = json.loads(request.body)
        except:
            response = rc.BAD_REQUEST
            response.content = "Invalid JSON object"
            raise HttpStatusCode(response)

        if not isinstance(parsed_body, dict):
            response = rc.BAD_REQUEST
            response.content = "Dictionary expected"
            raise HttpStatusCode(response)

        form = v_form(parsed_body, request.FILES)

        if form.is_valid():
            setattr(request, 'form', form)
            return f(self, request, *a, **kwa)
        else:
            raise FormValidationError(form)
    return wrap


def validate_json_list(v_form):
    @decorator
    def wrap(f, self, request, *a, **kwa):
        content_type = request.content_type.split(';')[0]
        if content_type != "application/json":
            response = rc.BAD_REQUEST
            response.content = "Invalid content type, must be application/json"
            raise HttpStatusCode(response)

        try:
            parsed_body = json.loads(request.body)
        except:
            response = rc.BAD_REQUEST
            response.content = "Invalid JSON object"
            raise HttpStatusCode(response)

        if not isinstance(parsed_body, list):
            response = rc.BAD_REQUEST
            response.content = "List expected"
            raise HttpStatusCode(response)

        if not len(parsed_body):
            response = rc.BAD_REQUEST
            response.content = "No entries to update"
            raise HttpStatusCode(response)

        forms = []
        for entry in parsed_body:
            form = v_form(entry, request.FILES)
            if form.is_valid():
                forms.append(form)
            else:
                raise FormValidationError(form)
        setattr(request, 'forms', forms)
        return f(self, request, *a, **kwa)
    return wrap


"""
FORM DATA VALIDATORS
"""


def validate_recipe(value):
    if not re.match(r'^[^\]]+::([^\]]+)@[0-9]+(\.[0-9]+){1,2}$', value):
        raise ValidationError('Recipe should be in a \
"cookbook::recipe@version" format')


def validate_attribute(value):
    if not isinstance(value, dict):
        raise ValidationError('Attributes must be in a dictionary')


def validate_role_recipes(value):
    if value and isinstance(value, list):
        map(validate_recipe, value)
        for i in value:
            try:
                rec_exist = Recipe.objects.get(recipe=i)
            except Recipe.DoesNotExist:
                raise ValidationError('Recipe %s does not exist' % i)
    else:
        raise ValidationError('Invalid recipe list')


validate_node_id = RegexValidator(regex=re.compile('^[\dA-F]{12}$'))


def validate_node_ids(value):
    if isinstance(value, list):
        for node_id in value:
            validate_node_id(node_id)
    else:
        raise ValidationError('Node list must be a list of node IDs')


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
        raise ValidationError('Invalid roles list')
    if not all(map(lambda i: 'name' in i, data)):
        raise ValidationError('Role name is empty')
    for role in data:
        if 'recipes' not in role or not role['recipes']:
            raise ValidationError('Recipes list for role "%s" \
should not be empty' % role['name'])
        for recipe in role['recipes']:
            validate_recipe(recipe)
            try:
                rec_exists = Recipe.objects.get(recipe=recipe)
            except Recipe.DoesNotExist:
                raise ValidationError('Recipe %s doesn\'t exist' % recipe)


def forbid_modifying_roles(value):
    raise ValidationError('Role list cannot be modified directly')


def validate_networks_metadata(data):
    if not isinstance(data, list):
        raise ValidationError("There should be a list of network names")


def validate_network(data):
    try:
        a = ipaddr.IPv4Network(data)
    except:
        raise ValidationError("Invalid network format!")


def validate_ip(data):
    try:
        a = ipaddr.IPv4Address(data)
    except:
        raise ValidationError("Invalid IP address format!")
