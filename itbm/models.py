import settings

from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext as _
from django.conf import settings
from django.template.defaultfilters import slugify
from django.db.models import Q
from django.db.models.signals import post_save

import forms as djforms

class HasTickets(object):
    def get_accepted_tickets(self):
        return self.tickets.filter(status__name='Accepted')
    def get_fixed_tickets(self):
        return self.tickets.filter(status__name='Fixed')
    def get_pending_tickets_for_consultant(self):
        return self.tickets.filter(status__waiting='consultant')
    def get_pending_tickets_for_client(self):
        return self.tickets.filter(status__waiting='client')
    def get_unpaid_tickets(self):
        return self.tickets.filter(paid=False)
    def get_total_time_spent(self):
        total = 0
        for ticket in self.tickets.all():
            if ticket.time_spent:
                total += ticket.time_spent
        return total
    def get_total_estimation_time(self):
        total = 0
        for ticket in self.tickets.all():
            if ticket.time_estimation:
                total += ticket.time_estimation
        return total
    def get_total_estimation_price(self):
        total = 0
        for ticket in self.tickets.all():
            if ticket.time_estimation:
                total += ticket.time_estimation * ticket.owner.get_profile().rates
        return total
    def get_unpaid_time_spent(self):
        total = 0
        for ticket in self.tickets.filter(paid=False):
            if ticket.time_spent:
                total += ticket.time_spent
        return total
    def get_unpaid_estimation_time(self):
        total = 0
        for ticket in self.tickets.filter(paid=False):
            if ticket.time_estimation:
                total += ticket.time_estimation
        return total
    def get_unpaid_estimation_price(self):
        total = 0
        for ticket in self.tickets.filter(paid=False):
            if ticket.time_estimation:
                total += ticket.time_estimation * ticket.owner.get_profile().rates
        return total
    def is_accepted(self):
        for ticket in self.tickets.all():
            if ticket.status.name == 'Accepted':
                return True

class Status(models.Model):
    WAIT_FOR=(
        (u'client to pay', _(u'Client to pay')),
        (u'client to work', _(u'Client to work')),
        (u'consultant to quote', _(u'Consultant to quote')),
        (u'consultant to work', _(u'Consultant to work')),
        (0, _(u'None')),
    )
    name = models.CharField(max_length=100, verbose_name=_(u'name'), unique=True)
    description = djforms.RstField(verbose_name=_(u'description'), null=True, blank=True)
    waiting = models.CharField(max_length=100, verbose_name=_(u'waiting'), choices=WAIT_FOR)
    def __unicode__(self):
        return self.name

class Project(models.Model, HasTickets):
    name = models.CharField(max_length=100, verbose_name=_(u'name'), unique=True)
    slug = models.CharField(max_length=100, verbose_name=_(u'slug'), unique=True)
    status = models.ForeignKey('Status', verbose_name=_(u'status'), null=True, blank=True)
    pub_date = models.DateField(verbose_name=_(u'date'), null=True, blank=True, auto_now=True)
    description = djforms.RstField(verbose_name=_(u'description'))
    provider = models.ForeignKey(User, verbose_name=_(u'provider'), null=True, blank=True, related_name='provides')
    owner = models.ForeignKey(User, verbose_name=_(u'lead'), null=True, blank=True, related_name='leads')
    client = models.ForeignKey(User, verbose_name=_(u'client'), null=True, blank=True, related_name='projects')
    public = models.BooleanField(verbose_name=_(u'public'))
    @property
    def tickets(self):
        qs = Ticket.objects.filter(
            Q(component__project=self)|
            Q(models__project=self)|
            Q(fields__model__project=self)|
            Q(relations__source_model__project=self)|
            Q(pages__project=self)
        )
        return qs
    def save(self, force_insert=False, force_update=False):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Project, self).save(force_insert=force_insert, force_update=force_update)
    def __unicode__(self):
        return self.name
    def get_absolute_url(self):
        return settings.ITBM_PREFIX + '/project/' + unicode(self.pk) + '/'
    def can_read(self, user):
        if user.is_staff:
            return True
        if self.public:
            return True
        if user == self.owner or user == self.client or user == self.provider:
            return True
        return False
    def can_edit(self, user):
        if user.is_staff:
            return True
        if user == self.owner or user == self.client or user == self.provider:
            return True
        return False       

def project_list(user):
    # todo: support for groups
    qs = Project.objects.filter( Q(owner=user) | Q(client=user) | Q(provider=user) | Q(public=1))
    return qs

class Component(models.Model, HasTickets):
    TYPES=(
        ('Programming', _(u'Programming')),
        ('Design', _(u'Design')),
        ('SEO', _(u'Search engine optimisation')),
        ('Traning', _(u'Traning')),
        ('Hosting', _(u'Hosting')),
        ('Other', _(u'Other')),
    )
    name = models.CharField(max_length=100, verbose_name=_(u'name'), choices=TYPES)
    pub_date = models.DateField(verbose_name=_(u'date'), null=True, blank=True, auto_now=True)
    slug = models.CharField(max_length=100, verbose_name=_(u'slug'), null=True, blank=True)
    description = djforms.RstField(verbose_name=_(u'description'), null=True, blank=True)
    project = models.ForeignKey('Project', verbose_name=_(u'project'))
    owner = models.ForeignKey(User, verbose_name=_(u'consultant'), null=True, blank=True, related_name='project_components')
    def save(self, force_insert=False, force_update=False):
        if Component.objects.filter(project=self.project, name=self.name).count():
            return False

        if not self.slug:
            self.slug = slugify(self.name)

        obj = super(Component, self).save(force_insert=force_insert, force_update=force_update)
        return obj
    def __unicode__(self):
        return self.name
    def get_absolute_url(self):
        return settings.ITBM_PREFIX + '/component/%s' % self.pk
    def get_add_ticket_absolute_url(self):
        return '/projects/%s/tickets/add' % self.project.slug

class Ticket(models.Model):
    title = models.CharField(max_length=100, verbose_name=_(u'title'))
    component = models.ForeignKey('Component', verbose_name=_(u'component'), null=True, blank=True, related_name='tickets')
    reporter = models.ForeignKey(User, verbose_name=_(u'reported'), null=True, blank=True, related_name='reported_tickets')
    owner = models.ForeignKey(User, verbose_name=_(u'owner'), null=True, blank=True)
    pub_date = models.DateField(verbose_name=_(u'date'), null=True, blank=True, auto_now=True)
    time_estimation = models.FloatField(verbose_name=_(u'time estimation'), null=True, blank=True)
    time_spent = models.FloatField(verbose_name=_(u'time spent'), null=True, blank=True)
    last_day = models.DateField(verbose_name=_(u'end date'), null=True, blank=True)
    status = models.ForeignKey('Status', verbose_name=_(u'status'), null=True, blank=True, related_name='tickets')
    description = djforms.RstField(verbose_name=_(u'description'))
    paid = models.BooleanField(verbose_name=_(u'paid'))
    def save(self, force_insert=False, force_update=False):
        if not self.owner and self.component:
            self.owner = self.component.owner

        if not self.status:
            self.status = Status.objects.get(name='New')
        super(Ticket, self).save(force_insert=force_insert, force_update=force_update)
    def __unicode__(self):
        return '#%s: %s' % (self.pk, self.title)
    def get_absolute_url(self):
        return settings.ITBM_PREFIX + '/tickets/%s' % self.pk
    def get_price(self):
        if self.owner:
            return self.owner.get_profile().rates * self.time_spent
        else:
            return 0
    def get_estimation_price(self):
        if self.owner and self.time_estimation:
            return self.owner.get_profile().rates * self.time_estimation
        else:
            return 0
    @property
    def project(self):
        return self.component.project

class TicketCollection(models.Model, HasTickets):
    STATUS = (
        ('quote', _('quote').capitalize()),
        ('accepted quote', _('accepted quote').capitalize()),
        ('refused quote', _('refused quote').capitalize()),
        ('bill', _('bill').capitalize()),
        ('paid bill', _('paid bill').capitalize()),
    )
    name = models.CharField(max_length=100, verbose_name=_(u'name'), null=True, blank=True)
    tickets = models.ManyToManyField('Ticket', verbose_name=_(u'tickets'), related_name='collections')
    status = models.CharField(max_length=100, verbose_name=_(u'status'), default='quote', choices=STATUS)
    pub_date = models.DateField(verbose_name=_(u'creation date'), auto_now=True)
    public = models.BooleanField(verbose_name=_(u'public'))
    def get_absolute_url(self):
        if self.status in ('bill', 'paid bill'):
            return settings.ITBM_PREFIX + '/%s/%s' % (('bill'), self.pk)
        else:
            return settings.ITBM_PREFIX + '/%s/%s' % (('quote'), self.pk)
    def save(self, force_insert=False, force_update=False):
        if self.status == 'accepted quote':
            for ticket in self.tickets.all():
                ticket.status = Status.objects.get(name='Accepted')
                ticket.save()
                for collection in ticket.collections.all():
                    if not collection.pk == self.pk:
                        collection.status = 'refused quote'
                        collection.save()
        elif self.status == 'paid bill':
            for ticket in self.tickets.all():
                ticket.paid = True
                ticket.save()
        elif self.status == 'refused quote':
            for ticket in self.tickets.all():
                refuse = True
                for collection in ticket.collections.all():
                    if not collection.status == 'refused quote':
                        refuse = False
                if refuse:
                    ticket.status = Status.objects.get(name='Refused')
                    ticket.save()
        super(TicketCollection, self).save(force_insert, force_update)
    @property
    def project(self):
        project = Project.objects.filter(component__tickets__in=self.tickets.all()).distinct()
        return project[0]
    @property
    def models(self):
        inner_qs = Ticket.objects.filter(collections=self)
        qs = Model.objects.filter(tickets__in=inner_qs)
        return qs
    @property
    def pages(self):
        pages = []
        for ticket in self.tickets.all():
            for page in ticket.pages.all():
                pages.append(page)
        return pages
class UserProfile(models.Model):
    rates = models.IntegerField(verbose_name=_(u'rates'), null=True, blank=True)
    father = models.ForeignKey(User, verbose_name=_(u'father'), null=True, blank=True, related_name='children')
    user = models.ForeignKey(User, verbose_name=_(u'user'), unique=True)

def component_reassign(sender, **kwargs):
    instance = kwargs['instance']
    if isinstance(instance, Component) and instance.owner:
        for ticket in instance.tickets.filter(owner=None):
            ticket.owner = instance.owner
            ticket.save()

post_save.connect(component_reassign)

class Model(models.Model, HasTickets):
    project = models.ForeignKey('Project', verbose_name=_(u'project'), related_name='models')
    name = models.CharField(max_length=100, verbose_name=_(u'name'))
    label = models.CharField(max_length=100, verbose_name=_(u'label'))
    slug = models.CharField(max_length=100, verbose_name=_(u'slug'), null=True, blank=True)
    tickets = models.ManyToManyField('Ticket', verbose_name=_(u'tickets'), null=True, blank=True, related_name='models')
    def get_absolute_url(self):
        return settings.ITBM_PREFIX + '/model/%s/' % self.pk
    def save(self, force_insert=False, force_update=False):
        tmp = self.label.split(' ')
        self.name = ''
        for word in tmp:
            self.name += word.capitalize()
        if not self.slug:
            self.slug = slugify(self.name)

        create_tickets = False
        if not self.pk:
            create_tickets = True

        result = super(Model, self).save(force_insert=force_insert, force_update=force_update)

        if create_tickets:
            ticket = Ticket()
            ticket.title = '%s: %s' % (_(u'create model').capitalize(), self.name)
            ticket.component = self.project.component_set.get(name=u'Programming')
            ticket.status = Status.objects.get(name='New')
            ticket.time_estimation = .1
            ticket.description = ticket.title
            ticket.save()
            self.tickets.add(ticket)
        return result

    def __unicode__(self):
        return self.name

class Field(models.Model, HasTickets):
    TYPES=(
        ('char', _('short text')),
        ('text', _('long text')),
        ('date', _('date')),
        ('dateTime', _('date and time')),
        ('file', _('file')),
        ('image', _('image')),
        ('email', _('email')),
        ('float', _('float')),
        ('map', _('map')),
        ('bool', _('bool')),
        ('int', _('int')),
    )
    model = models.ForeignKey('Model', verbose_name=_(u'model'), related_name='fields')
    name = models.CharField(max_length=100, verbose_name=_(u'name'))
    label = models.CharField(max_length=100, verbose_name=_(u'label'), null=True, blank=True)
    slug = models.CharField(max_length=100, verbose_name=_(u'slug'), null=True, blank=True)
    type = models.CharField(max_length=100, verbose_name=_(u'type'), choices=TYPES)
    description = djforms.RstField(verbose_name=_(u'description'), null=True, blank=True)
    tickets = models.ManyToManyField('Ticket', verbose_name=_(u'tickets'), null=True, blank=True, related_name='fields')
    def get_absolute_url(self):
        return '%sfields/%s/' % (self.model.get_absolute_url(), self.slug)
    def save(self, force_insert=False, force_update=False):
        tmp = self.label.split(' ')
        self.name = []
        for word in tmp:
            self.name.append(word.lower())
        self.name = '_'.join(self.name)

        if not self.slug:
            self.slug = slugify(self.name)

        # 'Field' instance needs to have a primary key value before a many-to-many relationship can be used
        #count = Field.objects.filter(model=self.model, slug=self.slug).count()
        #if count:
        #    return False

        create_tickets = False
        if not self.pk: 
            create_tickets = True

        result = super(Field, self).save(force_insert=force_insert, force_update=force_update)
        
        if create_tickets:
             ticket = Ticket()
             ticket.title = '%s: %s' % (_(u'create field').capitalize(), self.name)
             ticket.component = self.model.project.component_set.get(name='Programming')
             ticket.status = Status.objects.get(name='New')
             ticket.time_estimation = .1
             ticket.description = ticket.title
             ticket.save()
             self.tickets.add(ticket)

             for ticket in self.model.tickets.all():
                self.tickets.add(ticket)
        return result
    def __unicode__(self):
        return '%s (%s)' % (self.name, self.get_type_display())

class Relation(models.Model, HasTickets):
    TYPES = (
        ('11', _('1 to 1')),
        ('0n', _('1 to n')),
        ('nm', _('n to m')),
    )
    source_model = models.ForeignKey('Model', verbose_name=_(u'source'), related_name='source_of')
    source_property = models.CharField(max_length=100, verbose_name=_(u'source property name'), null=True, blank=True)
    destination_model = models.ForeignKey('Model', verbose_name=_(u'destination'), related_name='destination_of')
    destination_property = models.CharField(max_length=100, verbose_name=_(u'destination property name'), null=True, blank=True)
    slug = models.CharField(max_length=100, verbose_name=_(u'100'), null=True, blank=True)
    type = models.CharField(max_length=100, verbose_name=_(u'type'), choices=TYPES)
    tickets = models.ManyToManyField('Ticket', verbose_name=_(u'tickets'), null=True, blank=True, related_name='relations')
    def __unicode__(self):
        return '%s.%s to %s.%s' % (self.source_model, self.source_property, self.destination_model, self.destination_property)
    def get_absolute_url(self):
        return self.source_model.project.get_absolute_url() + 'relations/' + self.slug + '/'
    def save(self, force_insert=False, force_update=False):
        if not self.destination_property:
            self.destination_property = '%ss' % self.source_model.slug
        if not self.source_property:
            self.source_property = '%ss' % self.destination_model.slug
        if not self.slug:
            self.slug = slugify(unicode(self))
        super(Relation, self).save(force_insert=force_insert, force_update=force_update)

class Page(models.Model, HasTickets):
    project = models.ForeignKey('Project', verbose_name=_(u'project'), related_name='pages')
    title = models.CharField(max_length=100, verbose_name=_(u'title'))
    slug = models.CharField(max_length=100, verbose_name=_(u'slug'), null=True, blank=True)
    url = models.CharField(max_length=100, verbose_name=_(u'url address'))
    description = djforms.RstField(verbose_name=_(u'description'))
    action = djforms.RstField(verbose_name=_(u'action'))
    tickets = models.ManyToManyField('Ticket', verbose_name=_(u'tickets'), null=True, blank=True, related_name='pages')
    def __unicode__(self):
        return '%s' % (self.title)
    def get_absolute_url(self):
        return '%s/pages/%s/' % (self.project.get_absolute_url(), self.slug)
    def save(self, force_insert=False, force_update=False):
        create_tickets = False
        if not self.pk:
            create_tickets = True

        if not self.slug:
            self.slug = slugify(self.title)

        obj = super(Page, self).save(force_insert=force_insert, force_update=force_update)

        if create_tickets and self.project.component_set.count():
            for component in self.project.component_set.all():
                self.create_ticket(component)
        return obj
    def create_ticket(self, component):
        if not self.pk:
            return False
        if not isinstance(component, Component):
            return False

        t = Ticket(component=component)
        t.title ='Page: ' + self.title
        t.description = self.description
        t.save() 
        t.pages.add(self)

        print t.pages.all()
