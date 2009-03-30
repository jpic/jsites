import jsites
import models
from jadmin import menus

class CarSite(jsites.ControllerWrapper):
    def get_menu(self):
        menu = menus.Menu()
        site = menu.add('siteitem', 'siteurl')
        site.add('sitesubitem', 'sitesuburl')
        return menu

class CarController(jsites.Controller):
    def get_menu(self):
        menu = menus.Menu()
        controller = menu.add('controlleritem', 'controllerurl')
        controller.add('controllersubitem', 'url')
        return menu
    name = 'car'
    urlname = 'cars'
    content_class = models.Car

site = CarSite('sitename')
site.register(CarController('carlol'))
