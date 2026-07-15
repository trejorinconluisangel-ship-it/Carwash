from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('', include('insumos.urls')),
    path('', include('servicios.urls')),
    path('', include('tienda.urls')),
    path('', include('clientes.urls')),
    path('', include('comparador.urls')),
]
