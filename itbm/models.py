from django.db import models
from django.utils.translation import ugettext as _

class Ticket(models.Model):
    title = models.CharField(max_length=100, verbose_name=_(u'title'))
    deadline = models.DateField(verbose_name=_(u'deadline'))
    price = models.IntegerField(verbose_name=_(u'price'), null=True, blank=True)
    description = models.TextField(verbose_name=_(u'description'))
    def __unicode__(self):
        return '#%s: %s' % (self.pk, self.title)
