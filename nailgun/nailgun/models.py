from django.db import models
from django.contrib.auth.models import User
from jsonfield import JSONField
from api.fields import RecipeField


class Environment(models.Model):
    #user = models.ForeignKey(User, related_name='environments')
    name = models.CharField(max_length=100)


class Recipe(models.Model):
    recipe = RecipeField(max_length=100)


class Role(models.Model):
    name = models.CharField(max_length=50)
    recipes = models.ManyToManyField(Recipe, related_name="roles")


class Node(models.Model):
    NODE_STATUSES = (
        ('online', 'online'),
        ('offline', 'offline'),
        ('busy', 'busy'),
    )
    id = models.CharField(max_length=12, primary_key=True)
    environment = models.ForeignKey(Environment, related_name='nodes',
        null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=30, choices=NODE_STATUSES,
            default='online')
    metadata = JSONField()
    mac = models.CharField(max_length=17)
    ip = models.CharField(max_length=15)
    fqdn = models.CharField(max_length=255)
    roles = models.ManyToManyField(Role)


class Release(models.Model):
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=30)
    description = models.TextField()
    roles = models.ManyToManyField(Role, related_name='releases')

    class Meta:
        unique_together = ("name", "version")
