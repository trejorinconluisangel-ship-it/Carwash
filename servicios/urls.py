from django.urls import path
from . import views

urlpatterns = [
    # Tipos de servicio
    path('tipos-servicio/', views.tipo_servicio_lista, name='tipo_servicio_lista'),
    path('tipos-servicio/nuevo/', views.tipo_servicio_crear, name='tipo_servicio_crear'),
    path('tipos-servicio/<int:pk>/editar/', views.tipo_servicio_editar, name='tipo_servicio_editar'),
    path('tipos-servicio/<int:pk>/eliminar/', views.tipo_servicio_eliminar, name='tipo_servicio_eliminar'),

    # Tipos de vehículo
    path('tipos-vehiculo/', views.tipo_vehiculo_lista, name='tipo_vehiculo_lista'),
    path('tipos-vehiculo/nuevo/', views.tipo_vehiculo_crear, name='tipo_vehiculo_crear'),
    path('tipos-vehiculo/<int:pk>/editar/', views.tipo_vehiculo_editar, name='tipo_vehiculo_editar'),
    path('tipos-vehiculo/<int:pk>/eliminar/', views.tipo_vehiculo_eliminar, name='tipo_vehiculo_eliminar'),

    # Insumos en servicio
    path('insumos-servicio/', views.insumo_servicio_lista, name='insumo_servicio_lista'),
    path('insumos-servicio/nuevo/', views.insumo_servicio_crear, name='insumo_servicio_crear'),
    path('insumos-servicio/<int:pk>/eliminar/', views.insumo_servicio_eliminar, name='insumo_servicio_eliminar'),

    # Servicios
    path('servicios/', views.servicio_lista, name='servicio_lista'),
    path('servicios/nuevo/', views.servicio_crear, name='servicio_crear'),
    path('servicios/<int:pk>/eliminar/', views.servicio_eliminar, name='servicio_eliminar'),

    # API
    path('api/precio-sugerido/', views.precio_sugerido_api, name='precio_sugerido_api'),
]
