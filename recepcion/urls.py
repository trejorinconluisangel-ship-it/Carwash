from django.urls import path
from . import views

urlpatterns = [
    path('recepcion/', views.recepcion_lista, name='recepcion_lista'),
    path('recepcion/nueva/', views.recepcion_nueva, name='recepcion_nueva'),
    path('recepcion/<int:pk>/', views.recepcion_detalle, name='recepcion_detalle'),
]
