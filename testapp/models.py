from django.db import models

# Create your models here.

class Car(models.Model):
    name = models.CharField(max_length=100)
    brand = models.ForeignKey('Brand', verbose_name=u'brand', null=True, blank=True)
    comment = models.TextField(verbose_name=u'comment', null=True, blank=True)
    def __unicode__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=10, verbose_name=u'name', null=True, blank=True)
    def __unicode__(self):
        return 'brand '+self.name

class Whell(models.Model):
    car = models.ForeignKey('Car', related_name="weels")
    side = models.CharField(max_length=1)
    def __unicode__(self):
        return self.side

class Seat(models.Model):
    car = models.ForeignKey('Car', related_name="seats")
    foo = models.CharField(max_length=4, verbose_name='foo', null=True, blank=True)
    def __unicode__(self):
        return self.foo
