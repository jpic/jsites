import jsites
import models
from jadmin import menus

class CarSite(jsites.ControllerWrapper):
    def get_menu(self):
        menu = menus.Menu()
        site = menu.add('siteitem', 'siteurl')
        site.add('sitesubitem', 'sitesuburl')
        return menu

from django.forms.models import modelform_factory, inlineformset_factory
class CarController(jsites.Controller):
    def get_menu(self):
        menu = menus.Menu()
        controller = menu.add('controlleritem', 'controllerurl')
        controller.add('controllersubitem', 'url')
        return menu
    name = 'car'
    urlname = 'cars'
    content_class = models.Car
    def save_formset(self):
        print 'saving formset'
        self.formset_object.save()
    def get_formset_class(self):
        return inlineformset_factory(self.content_class, models.Whell)
    def get_formset_object(self):
        kwargs = {
            'instance': self.content_object,
        }
        if self.request.method == 'POST':
            formset = self.formset_class(self.request.POST, **kwargs)
        else:
            formset = self.formset_class(**kwargs)
        return formset 

site = CarSite('sitename')
site.register(CarController('carlol'))
