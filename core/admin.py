
from django.contrib import admin
from .models import Congestion, Accident

@admin.register(Congestion)
class CongestionAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'num_cars', 'section')
    search_fields = ('timestamp', 'section')

@admin.register(Accident)
class AccidentAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'num_instances', 'section')
    search_fields = ('timestamp', 'section')
