from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Event(models.Model):
    name=models.CharField(max_length=50)
    description=models.TextField()
    code=models.TextField(unique=True)
    participants=models.IntegerField()
    x_value=models.IntegerField(null=True)
    is_active = models.BooleanField(default=True)
    is_private = models.BooleanField(default=False)
    created_by=models.ForeignKey(User,on_delete=models.CASCADE)
    created_on=models.DateTimeField(auto_now_add=True)

class Levels(models.Model):
    event=models.ForeignKey(Event,on_delete=models.CASCADE)
    name=models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_by=models.ForeignKey(User,on_delete=models.CASCADE)
    created_on=models.DateTimeField(auto_now_add=True)

class Group(models.Model):
    level=models.ForeignKey(Levels,on_delete=models.CASCADE)
    name=models.CharField(max_length=50)
    capacity=models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_by=models.ForeignKey(User,on_delete=models.CASCADE)
    created_on=models.DateTimeField(auto_now_add=True)

class TimeMatrix(models.Model):
    group_from = models.ForeignKey(Group, related_name='from_group', on_delete=models.CASCADE)
    group_to = models.ForeignKey(Group, related_name='to_group', on_delete=models.CASCADE)
    travel_time = models.FloatField()  # Represents the travel time between the two groups (in seconds)

class Particpant(models.Model):
    name=models.CharField(max_length=255)
    event=models.ForeignKey(Event,on_delete=models.CASCADE)
    created_on=models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_assigned = models.BooleanField(default=False)

