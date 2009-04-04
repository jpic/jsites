from jsites.sites import ModelFormController
from django.contrib.auth.models import User
from django.conf import settings
from django.db import models

class UserController(ModelFormController):
    content_class = User
    field_names_for_merged_formsets = ('profile',)
