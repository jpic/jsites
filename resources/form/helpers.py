class Form(helpers.AdminForm):
    def __init__(self, form, merge_formset_objects, *args):
        super(Form, self).__init__(form, *args)
        self.field_forms = {}
        for formset in merge_formset_objects.values():
            for field in formset.forms[0].fields:
                self.field_forms[field] = formset.forms[0]

    def __iter__(self):
        for name, options in self.fieldsets:
            yield Fieldset(self.form, self.field_forms, name, **options)

class Fieldset(helpers.Fieldset):
    def __init__(self, form, field_forms, name, **kwargs):
        super(Fieldset, self).__init__(form, name, **kwargs)
        self.field_forms = field_forms

    def __iter__(self):
        for field in self.fields:
            yield Fieldline(self.form, self.field_forms, field)

class Fieldline(helpers.Fieldline):
    def __init__(self, form, field_forms, field):
        super(Fieldline, self).__init__(form, field)
        self.field_forms = field_forms

    def __iter__(self):
        for i, field in enumerate(self.fields):
            yield Field(self.form, self.field_forms, field, is_first=(i == 0))
    def errors(self):
        errors = []
        for field in self.fields:
            if field not in self.fields_forms:
                form = self.form
            else:
                form = self.field_forms[field]

            errors.append(form[field].errors.as_ul())

        return mark_safe(u'\n'.join(errors).strip('\n'))

class Field(helpers.AdminField):
    def __init__(self, form, field_forms, field, is_first):
        if not field in field_forms:
            super(Field, self).__init__(form, field, is_first)
        else:
            super(Field, self).__init__(field_forms[field], field, is_first)


