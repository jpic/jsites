from django.db import models
from django.contrib.auth.models import User

class Search(models.Model):
    user = models.ForeignKey(User, verbose_name=(u'user'), null=True, blank=True)
    url = models.TextField(verbose_name=(u'url'), null=True, blank=True)
