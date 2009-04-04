from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.conf import settings

class Project(models.Model):
    name = models.CharField(max_length=100, verbose_name=_(u'name'), null=True, blank=True)
    def __unicode__(self):
        return self.name

WORKFLOW=(
    (u'client to pay', _(u'Client to pay')),
    (u'client to work', _(u'Client to work')),
    (u'consultant to quote', _(u'Consultant to quote')),
    (u'consultant to work', _(u'Consultant to work')),
    (0, _(u'None')),
)

class Quote(models.Model):
    name = models.CharField(max_length=100, verbose_name=_(u'name'))
    tickets = models.ManyToManyField('Ticket', verbose_name=_(u'tickets'), related_name='quotes')
    creation_date = models.DateField(verbose_name=_(u'creation date'), null=True, blank=True)
    workflow_status = models.CharField(max_length=100, verbose_name=_(u'status'), default=u'consultant to quote', choices=WORKFLOW)
    def __unicode__(self):
        return self.name

class Ticket(models.Model):
    title = models.CharField(max_length=100, verbose_name=_(u'title'))
    deadline = models.DateField(verbose_name=_(u'deadline'))
    owner = models.ForeignKey(User, verbose_name=_(u'owner'), null=True, blank=True, related_name='owned_tickets', limit_choices_to = {'groups__name__exact': settings.CONSULTANTS_GROUP})
    creator = models.ForeignKey(User, verbose_name=_(u'reporter'), null=True, blank=True, related_name='created_tickets')
    creation_date = models.DateField(verbose_name=_(u'creation date'), null=True, blank=True)
    price = models.IntegerField(verbose_name=_(u'price'), null=True, blank=True)
    description = models.TextField(verbose_name=_(u'description'))
    components = models.ManyToManyField('Component', verbose_name=_(u'component'), null=True, blank=True, related_name='tickets')
    workflow_status = models.CharField(max_length=100, verbose_name=_(u'status'), default=u'consultant to quote', choices=WORKFLOW)
    def __unicode__(self):
        return '#%s: %s' % (self.pk, self.title)

class UserProfile(models.Model):
    user = models.ForeignKey(User, verbose_name=_(u'user'), related_name='profile')
    current_ticket = models.ForeignKey('Ticket', verbose_name=_(u'current ticket'), null=True, blank=True, related_name='worked_on_by')
    def __unicode__(self):
        return unicode(self.user)

class ComponentType(models.Model):
    name = models.CharField(max_length=100, verbose_name=_(u'name'))
    description = models.TextField(verbose_name=_(u'description'), null=True, blank=True)
    def __unicode__(self):
        return self.name

class Component(models.Model):
    type = models.ForeignKey('ComponentType', verbose_name=_(u'type'), related_name='components')
    project = models.ForeignKey('Project', verbose_name=_(u'project'), related_name='components')
    def __unicode__(self):
        return "%s (project %s)" % (self.type, self.project)

class Foo(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    def __unicode__(self):
        return self.name
