class ModelFormResource(ModelResource):
    actions = ('create', 'list', 'edit', 'details', 'delete')
    def delete(self):
        raise NotImplemented()
    delete = setopt(delete, urlname='delete', urlregex=r'^delete/(?P<model_id>.+)/$', verbose_name=u'éffacer')

    # {{{ menu, get_action_url
    def get_menu_items(self):
        items = {}
        if self.is_running:
            if self.action_name == 'edit':
                items[self.edit.verbose_name] = self.get_action_url('details',  kwargs={'model_id': self.model_id})
            if self.action_name == 'details':
                items[self.edit.verbose_name] = self.get_action_url('edit',  kwargs={'model_id': self.model_id})
        
        items[self.list.verbose_name] = self.get_action_url('list')
        items[self.create.verbose_name] = self.get_action_url('create')

        return items
    # }}}
    def get_use(self):
        """
        Lise of "use flags".
        """
        return (
            'adminform_object',
            'adminformset_objects',
        )

    def forms(self):
        """
        Forms view, used by edit and create.
        """
        if self.request.method == 'POST':
            form_valid = False
            formsets_valid = False

            if self.form_object.is_valid():
                form_valid = True
                self.save_form()

                # set to true before elimination tests
                formsets_valid = True
                for formset in self.formset_objects.values():
                    if not formset.is_valid():
                        formsets_valid = False

            if form_valid and formsets_valid:
                self.save_formsets()
                return http.HttpResponseRedirect(self.get_action_url('details',kwargs={'model_id': self.model_id}))
            elif form_valid:
                return http.HttpResponseRedirect(self.get_action_url('edit',kwargs={'model_id': self.model_id}))

        # admin js deps (like jquery for jsites)
        if 'adminform_object' in self.use \
            or 'adminformset_objects' in self.use:
            core = settings.ADMIN_MEDIA_PREFIX+'js/core.js'
            i18n = settings.JSITES_MEDIA_PREFIX+'js/admin.jsi18n.js'
            self.media.add_js([core, i18n])

        # don't leave out any form/formset object media
        self.media += self.form_object.media
        for formset_object in self.formset_objects.values():
            self.media += formset_object.media

        # allow template overload per resource-urlname/action
        self.template = [
            'jsites/%s/forms.html' % self.urlname,
            'jsites/forms.html',
        ]

        # figure context
        if not 'adminform_object' in self.use:
            self.add_to_context('form_object')
        else:
            self.add_to_context('adminform_object')
        if not 'adminformset_objects' in self.use:
            self.add_to_context('formset_objects')
        else:
            self.add_to_context('admin_formset_objects')
        self.add_to_context('merge_formset_objects')

    def get_merge_formset_objects(self):
        """
        This is a formset registry like formset_objects, but it removes
        any formset_object that should be usable with the model_object
        Form, instead of having its own "tab".
        """
        merge_formset_objects = {} # new registry, like formset_objects

        for name in self.field_names_for_merge_formsets:
            # remove the formset from the regular registry and 
            # append it to this other registry
            merge_formset_objects[name] = self.formset_objects.pop(name)

            # also make sure there isn't any adminformset_object for it
            if 'adminformset_objects' in self.use:
                self.admin_formset_objects.pop(name)

        return merge_formset_objects

    def get_adminform_object(self):
        """
        Instanciate an AdminForm for this form object etc ...
        Actually, we use our own set of helpers to support formsets
        as well.
        """
        adminform_object = Form(self.form_object,
            self.merge_formset_objects, self.fieldsets,
            self.prepopulated_fields)
        return adminform_object

    def get_prepopulated_fields(self):
        """
        Dict of fieldname -> value to use if the content object is
        not yet saved.
        """
        return {}

    def get_flat_fieldsets(self):
        """
        Returns a list of field names from an admin fieldsets structure.
        """
        return flatten_fieldsets(self.fieldsets)

    def get_fieldsets(self):
        """
        Return a fieldsets tuple of configurations for admin.helpers.Fieldset
        Actually, it is possible to use fields from a formset that was created
        for a field in self.field_names_for_merge_formsets.

        By default, it makes one fieldset out of all of self.form_field_names
        and self.merge_formset_objects, with self.formfields_per_line.
        Also, it omits the id field.
        """
        names = self.form_field_names

        # add field names of any formset to merge
        for formset in self.merge_formset_objects.values():
            names += formset.forms[0].fields.keys()
        
        fieldset = [self.model_class._meta.verbose_name, {'fields': []}]
        line = []
        for name in names:
            if name == 'id':
                continue
            if len(line) >= self.formfields_per_line:
                fieldset[1]['fields'].append(line)
                line = []
            line.append(name)
        
        if line:
            fieldset[1]['fields'].append(line)
        
        #TODO cache fieldsets
        return (fieldset,)

    def get_formfields_per_line(self):
        """ Default number of form fields per line """
        return 3

    def edit(self):
        """ Action wrapping self.forms, requiring a model_id """
        return self.forms()
    edit = setopt(edit, urlname='edit', urlregex=r'^edit/(?P<model_id>.+)/$', verbose_name=u'modifier')

    def create(self):
        """ Action wrapping around self.forms, requiring no model_id """
        return self.forms()
    create = setopt(create, urlname='create', urlregex=r'^create/$', verbose_name=u'créer (nouveau)')

    def save_form(self):
        """ Saves self.form_object """
        #TODO implement __setattr__
        self.set_model_object(self.form_object.save())

    def get_form_class(self):
        """
        Returns a form class for self.model_class.

        Uses self.form_field_names, and self.formfield_for_dbfield
        as form field for db field callback.
        """
        cls = self.model_class.__name__ + 'Form'
        return modelform_factory(
            fields=self.form_field_names,
            model=self.model_class,
            formfield_callback=self.formfield_for_dbfield
        )

    def get_form_field_names(self):
        """ List of field names to use for self.form_class """
        return self.local_field_names

    def get_form_field_objects(self):
        """ List of field instances to use for self.form_class """
        return self.field_names_to_objects(self.form_field_names)

    def formfield_for_dbfield(self, dbfield):
        """
        Default formfield for db field callback to use in our form generators.
        """
        kwargs = {}
        if dbfield.name in self.wysiwyg_field_names:
            kwargs['widget'] = widgets.WysiwygWidget
        elif isinstance(dbfield, fields.DateField):
            kwargs['widget'] = admin_widgets.AdminDateWidget
        elif isinstance(dbfield, fields.DateTimeField):
            kwargs['widget'] = admin_widgets.AdminDateTimeWidget
        elif isinstance(dbfield, fields.TimeField):
            kwargs['widget'] = admin_widgets.AdminTimeWidget

        if self.action_name == 'list':
            kwargs['required'] = False

        formfield = dbfield.formfield(**kwargs)
        return formfield

    def get_wysiwyg_field_names(self):
        """
        List of field names to decorate with a wysiwyg in the ui

        Again aiming for sensible defaults, field named 'html',
        'body' or 'contents' are returned by default.
        """
        return ('html','body', 'contents')

    def get_form_object(self):
        """
        Returns a form object to edit self.model_object or create
        (instanciate and save) a self.model_class
        """
        if self.request.method == 'POST':
            form = self.form_class(self.request.POST, instance=self.model_object)
        else:
            form = self.form_class(instance=self.model_object)
        return form 

    def save_formsets(self):
        """ Saves all self.formset_objects """
        for formset_object in self.formset_objects.values():
            formset_object.save()

    def formset_objects_factory(self, admin):
        """
        Return a list of formset objects.

        The form() view passes both the form_object and formset_objects.
        To set up the formset another resource would get in his list
        formset_objects, overload get_formset_object().

        Uses self.field_names_for_formsets, and self.formset_object_factory
        for each formset_object to do.
        """
        objects = {}
        for name, field in self.field_objects_for_formsets.items():
            objects[name] = self.formset_object_factory(field, admin)
        return objects

    def formset_object_factory(self, prop, admin):
        # figure what model we want an inline from
        related = prop.model
        # rely on the parent to get the resource class we want
        resource_class = self.parent.get_resource_classes_for_model_class(related)
        # fire it as an inline of this resource, making sure we pass
        # the correct model_class: the related object we want
        kwargs = {
            'inline': self,
            'model_class': related,
            'inline_fk_name': prop.field.name
        }

        # make sure it won't give more than one formset_object in
        # this special case
        if prop.field.rel.related_name in self.field_names_for_formsets:
            kwargs['max_formsets_number'] = 1
            kwargs['formset_deletable'] = False

        resource_object = resource_class.instanciate(**kwargs)

        # get the object we want
        # run the getter: because this is a factory method,
        # and because else it won't know about the request!
        if admin:
            object = resource_object.get_admin_formset_object()
        else:
            object = resource_object.get_formset_object()
        return object

    def get_admin_inline_options(self):
        options = {}
        options["template"] = self.admin_inline_template
        options["prepopulated_fields"] = self.prepopulated_fields
        options["media"] = self.media
        options["verbose_name_plural"] = self.model_class._meta.verbose_name_plural
        options["verbose_name"] = self.model_class._meta.verbose_name
        # options["show_url"] = self.details_url,
        return options

    def get_admin_inline_options_mock(self):
        return self.admin_inline_options_mock_factory(**self.admin_inline_options)

    def admin_inline_options_mock_factory(self, **options):
        class InlineAdminFormSetOptionsMock(object):
            def __init__(self, **kwargs):
                for property, value in kwargs.items():
                    setattr(self, property, value)
        mock = InlineAdminFormSetOptionsMock(**options)
        return mock

    def get_admin_inline_template(self):
        return 'admin/edit_inline/tabular.html'

    def get_formset_fieldsets(self):
        return [(None, {'fields':self.inline_formset_field_names})]

    def get_admin_formset_object(self):
        object = helpers.InlineAdminFormSet(self.admin_inline_options_mock, self.formset_object, self.formset_fieldsets)
        
        if TEST: # run tests that will break in Werkzeug
            # what? the way we do fieldsets is retarded?
            # then use a node layout and send me the patch jamespic@gmail.com TYIA
            # omg i need a couch.
            for inline_admin_form in object:
                for fieldset in inline_admin_form:
                    for line in fieldset:
                        for field in line:
                            if field is None:
                                print "!None field found, that wouldn't work in the template"
                                print object, inline_admin_form, fieldset ,line, field
        
        return object

    def get_admin_formset_objects(self):
        return self.formset_objects_factory(True)

    def get_formset_objects(self):
        if 'adminformset_objects' in self.use:
            formsets = {}
            for field_name, admin_formset_object in self.admin_formset_objects.items():
                formsets[field_name] = admin_formset_object.formset
            return formsets
        else:
            return self.formset_objects_factory(False)

    def get_field_names_for_merge_formsets(self):
        """
        Return a list of field names which inline formsets should be part
        of the content object form.

        Its a template option.
        """
        return []

    def get_formset_object(self, kwargs = {}):
        """
        Return a formset object.

        The formset object uses self.inline.model_object as related object
        instance if the resource was instanciated with the "inline" argument.

        Uses self.formset_fields or self.inline_formset_fields, if called by an
        a resource as inline.
        """
        if self.inline:
            kwargs['instance'] = self.inline.model_object
            # Also copy the request, as we want the other resource
            # to handle his formset
            self.request = self.inline.request
        else:
            kwargs['instance'] = self.model_object
        
        if self.request.method == 'POST':
            formset = self.formset_class(self.request.POST, **kwargs)
        else:
            formset = self.formset_class(**kwargs)

        return formset 
    
    def get_formset_class(self):
        """
        Returns a formset class.

        The formset class uses self.inline.model_class as related class
        if the resource was instanciated with the "inline" argument.

        Uses self.formset_fields, or self.inline_formset_fields.
        """
        kwargs = {}
        if self.inline:
            kwargs['fields'] = self.inline_formset_field_names
            kwargs['extra']  = self.extra_formsets
            kwargs['can_delete'] = self.formset_deletable
            kwargs['can_order']  = self.orderable_formsets
            kwargs['max_num'] = self.max_formsets_number
            
            if self.inline_fk_name: # use the fk_name if any
                kwargs['fk_name'] = self.inline_fk_name

            return inlineformset_factory(self.inline.model_class,
                self.model_class, **kwargs)
        else:
            kwargs['fields'] = self.formset_field_names
            return modelformset_factory(self.model_class, **kwargs)

    def get_inline_fk_name(self):
        """
        Return the default fk_name to use.
        Better to pass it as an instance keyword argument, in general.
        """
        return None

    def get_extra_formsets(self):
        """
        Number of formsets in addition to the number of objects to
        formset.
        """
        return 3

    def get_orderable_formsets(self):
        """
        Is the formset orderable? Django does not yet make use of it in admin
        and neiter do we, at the moment.
        """
        return False

    def get_max_formsets_number(self):
        """
        Return the maximum number of formsets to allow.
        """
        return 20

    def get_formset_deletable(self):
        """
        Return true if it should be possible to delete formsets.
        This displays a "Delete" checkbox with all formsets.
        """
        return self.get_permission(action_name='delete')

    def get_field_names_for_formsets(self):
        """
        Any of those fields will have formsets instead of a widget.
        """
        return self.reverse_fk_field_names


    def get_field_objects_for_formsets(self):
        """
        Return field objects for self.field_names_for_formsets.
        Uses self.field_names_for_formsets by default.
        """
        return self.field_names_to_objects(self.field_names_for_formsets)

    def get_formset_field_names(self):
        """
        Names of fields for this content class formset.
        """
        return self.local_field_names
    
    def get_formset_field_objects(self):
        """
        Instances of fields for this content class formset.
        Uses self.formset_field_names by default.
        """
        return self.field_names_to_objects(self.formset_field_names)

    def get_inline_formset_field_names(self):
        """
        Returns a list of fields to use when creating inline formsets
        for a related object.
        
        Use any field name that is in self.inline.flat_fieldsets
        and in self.model_field_names.

        It will use required field names unless there are less than
        self.inline_formset_field_number total names.
        """
        names = []
        if self.inline:
            for name in self.inline.flat_fieldsets:
                if name in self.model_field_names:
                    names.append(name)

        if len(self.local_field_names) + len(names) <= self.inline_formset_fields_number:
            names += self.local_field_names
        else:
            names += self.required_field_names

        return names

    def get_inline_formset_fields_number(self):
        return 5

    def get_inline_formset_field_objects(self):
        """
        Instances of fields to use when creating inline formsets
        for a related object.
        Uses self.inline_formset_field_names by default.
        """
        return self.field_names_to_objects(self.inline_formset_field_names)

    # {{{ search/list view
    def get_search_engine(self):
        import jsearch
        engine = jsearch.ModelSearch(
            model_class = self.model_class,
            queryset = self.queryset,
            search_fields = self.list_columns,
            form_class = self.form_class
        )
        return engine

    def get_list_columns(self):
        return self.form_field_names

    def get_queryset(self):
        return self.model_class.objects.select_related()

    def list(self):
        self.search_engine.parse_request(self.request)
        self.add_to_context('search_engine')
        self.add_to_context('model_class')
        self.add_to_context('model_field_names')
        self.add_to_context('model_field_objects')
        # additionnal fancey links
    list = setopt(list, urlname='list', urlregex=r'^$', verbose_name=u'liste')
    # }}}

