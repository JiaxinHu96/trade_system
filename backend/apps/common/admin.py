from django.contrib import admin
from .models import DashboardPreference, DashboardTab

admin.site.register(DashboardTab)
admin.site.register(DashboardPreference)
