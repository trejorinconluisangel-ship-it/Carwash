from django.contrib import admin
from .models import Recepcion


@admin.register(Recepcion)
class RecepcionAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'hora_recepcion', 'cliente', 'cliente_nombre', 'placa', 'servicio')
    list_filter = ('fecha', 'lugar')
    search_fields = ('cliente_nombre', 'placa', 'marca', 'telefono')
