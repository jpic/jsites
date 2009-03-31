import jsites
import models
from jadmin import menus

class CarSite(jsites.ControllerWrapper):
    name='sitename'
    urlname=name

from django.forms.models import modelform_factory, inlineformset_factory, modelformset_factory
class CarController(jsites.Controller):
    name = 'car'
    urlname = 'cars'
    fieldsets = (
        (None, {'fields': ('name','brand')}),
        ('comment', {'fields': ('comment',)}),
    )
    wysiwyg_field_names = ('comment',)

class BrandController(jsites.Controller):
    name='brands'
    urlname=name

class WheelController(jsites.Controller):
    name = 'bar'
    urlname=name

class SeatController(jsites.Controller):
    name = 'seats'
    urlname = name

site = CarSite()
site.register(models.Car, CarController)
site.register(models.Whell, WheelController)
site.register(models.Seat, SeatController)
print site.get_urls()
