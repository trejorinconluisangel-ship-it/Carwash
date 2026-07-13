from django.urls import path
from . import views

urlpatterns = [
    path('clientes/', views.cliente_lista, name='cliente_lista'),
    path('clientes/nuevo/', views.cliente_crear, name='cliente_crear'),
    path('clientes/<int:pk>/', views.cliente_detalle, name='cliente_detalle'),
    path('clientes/<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('clientes/<int:pk>/eliminar/', views.cliente_eliminar, name='cliente_eliminar'),

    path('clientes/<int:cliente_pk>/vehiculo/nuevo/', views.vehiculo_crear, name='vehiculo_crear'),
    path('vehiculos/<int:pk>/editar/', views.vehiculo_editar, name='vehiculo_editar'),
    path('vehiculos/<int:pk>/eliminar/', views.vehiculo_eliminar, name='vehiculo_eliminar'),

    path('api/vehiculos-cliente/', views.vehiculos_por_cliente_api, name='vehiculos_por_cliente_api'),
]
