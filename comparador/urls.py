from django.urls import path
from . import views

urlpatterns = [
    path('comparador/', views.comparador_lista, name='comparador_lista'),
    path('comparador/nuevo/', views.producto_crear, name='producto_crear_comparador'),
    path('comparador/<int:pk>/', views.producto_detalle, name='producto_detalle_comparador'),
    path('comparador/<int:pk>/editar/', views.producto_editar, name='producto_editar_comparador'),
    path('comparador/<int:pk>/eliminar/', views.producto_eliminar, name='producto_eliminar_comparador'),

    path('comparador/<int:producto_pk>/precio/nuevo/', views.precio_crear, name='precio_crear_comparador'),
    path('comparador/precio/<int:pk>/editar/', views.precio_editar, name='precio_editar_comparador'),
    path('comparador/precio/<int:pk>/eliminar/', views.precio_eliminar, name='precio_eliminar_comparador'),

    path('comparador/categorias/', views.categoria_lista, name='categoria_lista_comparador'),
    path('comparador/categorias/<int:pk>/eliminar/', views.categoria_eliminar, name='categoria_eliminar_comparador'),
]
