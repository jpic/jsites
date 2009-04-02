from django.contrib import admin

import models

class TicketAdmin(admin.ModelAdmin):
    fieldsets = (
        ('id', {'fields': (('title', 'description'),)}),
        ('todo', {'fields': (('price', 'deadline'),)}),
    )

admin.site.register(models.Ticket, TicketAdmin)
admin.site.register(models.Foo)
