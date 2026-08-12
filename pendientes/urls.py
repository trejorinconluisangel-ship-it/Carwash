from django.urls import path
from . import views

urlpatterns = [
    path('pendientes/', views.pendiente_lista, name='pendiente_lista'),
    path('pendientes/agregar/', views.pendiente_crear, name='pendiente_crear'),
    path('pendientes/<int:pk>/toggle/', views.pendiente_toggle, name='pendiente_toggle'),
    path('pendientes/<int:pk>/eliminar/', views.pendiente_eliminar, name='pendiente_eliminar'),
]
