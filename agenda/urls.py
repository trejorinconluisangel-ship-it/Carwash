from django.urls import path
from . import views

urlpatterns = [
    path('agenda/', views.calendario, name='agenda_calendario'),
    path('agenda/nueva/', views.cita_crear, name='cita_crear'),
    path('agenda/<int:pk>/editar/', views.cita_editar, name='cita_editar'),
    path('agenda/<int:pk>/eliminar/', views.cita_eliminar, name='cita_eliminar'),
    path('agenda/<int:pk>/estado/', views.cita_estado, name='cita_estado'),
]
