from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Case, When, IntegerField
from django.utils import timezone
from .models import Pendiente, PRIORIDAD_CHOICES


_PRIO_ORDER = Case(
    When(prioridad='fuego', then=0),
    When(prioridad='pronto', then=1),
    When(prioridad='sinprisa', then=2),
    default=3,
    output_field=IntegerField(),
)


def pendiente_lista(request):
    pendientes = (
        Pendiente.objects
        .annotate(orden_prio=_PRIO_ORDER)
        .order_by('completado', 'orden_prio', '-created_at')
    )
    activos_count = pendientes.filter(completado=False).count()
    fuego_count = pendientes.filter(completado=False, prioridad='fuego').count()
    pronto_count = pendientes.filter(completado=False, prioridad='pronto').count()

    return render(request, 'pendientes/pendiente_lista.html', {
        'pendientes': pendientes,
        'activos_count': activos_count,
        'fuego_count': fuego_count,
        'pronto_count': pronto_count,
        'prioridades': PRIORIDAD_CHOICES,
    })


def pendiente_crear(request):
    if request.method == 'POST':
        texto = request.POST.get('texto', '').strip()
        prioridad = request.POST.get('prioridad', 'sinprisa')
        if texto:
            Pendiente.objects.create(texto=texto, prioridad=prioridad)
        else:
            messages.error(request, 'Escribe el pendiente.')
    return redirect('pendiente_lista')


def pendiente_toggle(request, pk):
    if request.method == 'POST':
        p = get_object_or_404(Pendiente, pk=pk)
        p.completado = not p.completado
        p.fecha_completado = timezone.now() if p.completado else None
        p.save(update_fields=['completado', 'fecha_completado'])
    return redirect('pendiente_lista')


def pendiente_eliminar(request, pk):
    if request.method == 'POST':
        get_object_or_404(Pendiente, pk=pk).delete()
    return redirect('pendiente_lista')
