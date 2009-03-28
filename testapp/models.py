from django.db import models

# Create your models here.

class Car(models.Model):
    name = models.CharField(max_length=100)

class Whell(models.Model):
    car = models.ForeignKey('Car', related_name="weels")
    side = models.CharField(max_length=1)
