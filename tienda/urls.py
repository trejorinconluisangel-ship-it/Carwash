from django.urls import path
from . import views

urlpatterns = [
    # Productos
    path('tienda/', views.producto_lista, name='producto_lista'),
    path('tienda/nuevo/', views.producto_crear, name='producto_crear'),
    path('tienda/<int:pk>/', views.producto_detalle, name='producto_detalle'),
    path('tienda/<int:pk>/editar/', views.producto_editar, name='producto_editar'),
    path('tienda/<int:pk>/eliminar/', views.producto_eliminar, name='producto_eliminar'),

    # Entradas
    path('tienda/entradas/', views.entrada_lista, name='entrada_lista'),
    path('tienda/entradas/nueva/', views.entrada_crear, name='entrada_crear'),
    path('tienda/entradas/<int:pk>/eliminar/', views.entrada_eliminar, name='entrada_eliminar'),

    # Ventas
    path('tienda/ventas/', views.venta_lista, name='venta_lista'),
    path('tienda/ventas/nueva/', views.venta_crear, name='venta_crear'),
    path('tienda/ventas/<int:pk>/eliminar/', views.venta_eliminar, name='venta_eliminar'),

    # API
    path('tienda/api/precio/', views.precio_producto_api, name='precio_producto_api'),
]
