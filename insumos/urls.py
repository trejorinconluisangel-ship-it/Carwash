from django.urls import path
from . import views

urlpatterns = [
    # Proveedores
    path('proveedores/', views.proveedor_lista, name='proveedor_lista'),
    path('proveedores/nuevo/', views.proveedor_crear, name='proveedor_crear'),
    path('proveedores/<int:pk>/editar/', views.proveedor_editar, name='proveedor_editar'),
    path('proveedores/<int:pk>/eliminar/', views.proveedor_eliminar, name='proveedor_eliminar'),

    # Insumos
    path('insumos/', views.insumo_lista, name='insumo_lista'),
    path('insumos/nuevo/', views.insumo_crear, name='insumo_crear'),
    path('insumos/<int:pk>/', views.insumo_detalle, name='insumo_detalle'),
    path('insumos/<int:pk>/editar/', views.insumo_editar, name='insumo_editar'),
    path('insumos/<int:pk>/eliminar/', views.insumo_eliminar, name='insumo_eliminar'),

    # Compras
    path('compras/', views.compra_lista, name='compra_lista'),
    path('compras/nueva/', views.compra_crear, name='compra_crear'),
    path('compras/<int:pk>/eliminar/', views.compra_eliminar, name='compra_eliminar'),
]
