from django.db import models
from django.contrib.auth.models import User
from jsonfield import JSONField
from api.fields import RecipeField


class Recipe(models.Model):
    recipe = RecipeField(max_length=100)
    # FIXME(mihgen): depends should be recipe objects
    depends = models.CharField(max_length=100, blank=True)


class Role(models.Model):
    name = models.CharField(max_length=50)
    recipes = models.ManyToManyField(Recipe, related_name="roles")


class Release(models.Model):
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=30)
    description = models.TextField(null=True, blank=True)
    roles = models.ManyToManyField(Role, related_name='releases')

    class Meta:
        unique_together = ("name", "version")


class Cluster(models.Model):
    name = models.CharField(max_length=100)
    release = models.ForeignKey(Release, related_name='clusters')


class Node(models.Model):
    NODE_STATUSES = (
        ('offline', 'offline'),
        ('ready', 'ready'),
        ('deploying', 'deploying'),
        ('error', 'error'),
    )
    id = models.CharField(max_length=12, primary_key=True)
    cluster = models.ForeignKey(Cluster, related_name='nodes',
        null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=30, choices=NODE_STATUSES,
            default='online')
    metadata = JSONField()
    mac = models.CharField(max_length=17)
    ip = models.CharField(max_length=15)
    fqdn = models.CharField(max_length=255)
    roles = models.ManyToManyField(Role, related_name='nodes')
    new_roles = models.ManyToManyField(Role, related_name='+')
    redeployment_needed = models.BooleanField(default=False)
