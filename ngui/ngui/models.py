from django.db import models
from django.contrib.auth.models import User
from jsonfield import JSONField

class Environment(models.Model):
    
    #user = models.ForeignKey(User, related_name='environments')
    name = models.CharField(max_length=255)

class Node(models.Model):
    
    environment = models.ForeignKey(Environment, related_name='nodes')
    name = models.CharField(max_length=255, primary_key=True)
    metadata = JSONField()
