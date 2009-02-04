from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class Ticket(models.Model):
    title = models.CharField(max_length=100, verbose_name=_(u'title'))
    deadline = models.DateField(verbose_name=_(u'deadline'))
    price = models.IntegerField(verbose_name=_(u'price'), null=True, blank=True)
    description = models.TextField(verbose_name=_(u'description'))
    def __unicode__(self):
        return '#%s: %s' % (self.pk, self.title)

class Foo(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    def __unicode__(self):
        return self.name
