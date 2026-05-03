
from django.contrib import admin
from .models import Congestion, Accident, HistoricData

@admin.register(Congestion)
class CongestionAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'num_cars', 'section')
    search_fields = ('timestamp', 'section')

@admin.register(Accident)
class AccidentAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'num_instances', 'section')
    search_fields = ('timestamp', 'section')

@admin.register(HistoricData)
class HistoricDataAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'num_cars_top', 'num_cars_bottom', 'num_cars_left', 'num_cars_right', 'total_cars')
    search_fields = ('timestamp',)
