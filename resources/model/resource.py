from django.utils.translation import ugettext_lazy as _
from django.db.models import fields as django_fields
from django.db.models import related as django_related

from jpic.resources.base import ResourceBase
from jpic import voodoo

class ModelResource(ResourceBase):
    def validate(self):
        if self._has('model_class'):
            self._get_or_set('name', self.model_class._meta.verbose_name)
            self._get_or_set('urlname', self.model_class._meta.module_name)
        super(ModelResource, self).validate()

    def get_model_class(self):
        """  Return the "model class" used for the contents to display. """
        if self.model_object:
            return self.model_object.__class__

    def get_model_id(self):
        """
        Returns the id of the requested content, if any.
        Checks self.kwargs by default.
        """
        if 'model_id' in self.kwargs:
            return self.kwargs['model_id']
        return None

    def get_model_field_names(self):
        """ Return all field names for content class. """
        return self.model_class._meta.get_all_field_names()

    def get_model_field_objects(self):
        """ Field instances for model_field_names. """
        return self.field_names_to_objects(self.model_field_names)

    def get_local_field_names(self):
        """
        Returns a list field names that are defined in the content class
        itself and are not auto fields.
        """
        names = []
        for field in self.model_class._meta.fields:
            if not isinstance(field, (django_fields.AutoField, django_related.RelatedObject)):
                names.append(field.name)
        
        for field in self.model_class._meta.many_to_many:
            names.append(field.name)

        return names

    def get_local_field_objects(self):
        """ Objects of local_field_names. """
        return self.field_names_to_objects(self.local_field_names)

    def get_model_object(self):
        if 'model_class' in self._security_stack:
            raise Exception('No way to figure model_object, model_class')

        if self.model_id:
            return self.model_class.objects.get(pk=self.model_id)

        # prepopulate where possible
        if self.fields_initial_values:
            return self.model_class(**self.fields_initial_values)
        return self.model_class()
    
    def set_model_object(self, model_object):
        self.model_object = model_object
        self.model_class = model_object.__class__
        self.model_id = model_object.pk

    def get_fields_initial_values(self):
        """
        Parse the request and finds key/values matching self.model_class
        attribute.
        """
        from_get = {}
        for key, value in self.request.GET.items():
            if key in self.model_class._meta.get_all_field_names():
                from_get[key.encode()] = value
        return from_get
    
    def get_virtual_fields(self):
        """
        Returns a list of virtual field names, virtual fields are doable by
        setting 'related_name' in a FK pointing to self.model_class.
        """
        virtual_fields = []
        for name, field in self.model_field_objects.items():
            if isinstance(field, related.RelatedObject) \
                and not isinstance(field, fields.AutoField):
                virtual_fields.append(field_name)
        return virtual_fields

    def get_inline_relation_field(self):
        if not self.inline:
            raise NotAsInline()

        for name, field in self.inline.model_field_objects.items():
            if not hasattr(field, 'field'):
                continue
            field = field.field
            if not hasattr(field, 'rel') or not hasattr(field.rel, 'to'):
                continue
            if field.rel.to == self.inline.model_class:
                return field
    
    def get_fk_fields(self):
        fields = []
        for field in self.model_class._meta.fields:
            if isinstance(field, related.ForeignKey):
                fields.append(field)
        return fields

    def details(self):
        self.add_to_context('model_object')
        self.add_to_context('model_field_names')
        self.add_to_context('model_field_objects')
    details = voodoo.setopt(details, urlname='details', urlregex=r'^(?P<model_id>.+)/$', verbose_name=_('details'))

    def get_reverse_fk_field_names(self):
        names = []
        for name in self.model_class._meta.get_all_field_names():
            field = self.model_class._meta.get_field_by_name(name)[0]
            if isinstance(field, django_related.RelatedObject) and isinstance(field, django_related.ForeignKey):
                names.append(name)
        return names

    def get_reverse_fk_field_objects(self):
        return self.field_names_to_objects(self.reverse_fk_field_names)

    def field_names_to_objects(self, names):
        objects = {}
        for name in names:
            objects[name] = self.model_class._meta.get_field_by_name(name)[0]
        return objects

    def get_required_field_names(self):
        required = []
        for name, field in self.model_field_objects.items():
            if not hasattr(field, 'blank'):
                continue
            if not field.blank and not field.null:
                required.append(name)
        return required

    def get_actions_names(self):
        names = super(ModelResource, self).get_actions_names()
        names.append('details')
        names.append('list')
        return names
