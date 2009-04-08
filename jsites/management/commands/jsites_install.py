import os

from django.core.management.base import BaseCommand
from django.db.models import get_app

class Command(BaseCommand):
    help = 'Create a symlink in jsites/templates/jsites to jsites/templates/jsites_default.'
    
    def handle(self, *args, **options):
        a = get_app('jsites')
        m = a.__file__
        j = m.rstrip('models.pyc')
        t = os.path.join(j, 'templates/jsites')
        d = os.path.join(j, 'templates/jsites_default')
        os.symlink(d, t)
