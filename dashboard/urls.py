from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('datos-prueba/cargar/', views.cargar_datos_prueba, name='cargar_datos_prueba'),
    path('datos-prueba/limpiar/', views.limpiar_todos_datos, name='limpiar_todos_datos'),
]
