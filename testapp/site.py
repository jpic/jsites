import jsites
import models

class CarController(jsites.Controller):
    name = 'car'
    urlname = 'cars'
    content_class = models.Car

site = jsites.ControllerWrapper('sitename')
site.register(CarController('carlol'))
