import calendar as cal_module
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse

from .models import Cita, ESTADO_CHOICES
from .forms import CitaForm

MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']


def _redirect_a_mes(fecha):
    return redirect(f"{reverse('agenda_calendario')}?year={fecha.year}&month={fecha.month}")


def calendario(request):
    hoy = timezone.localdate()
    try:
        year = int(request.GET.get('year', hoy.year))
        month = int(request.GET.get('month', hoy.month))
    except ValueError:
        year, month = hoy.year, hoy.month

    if month < 1:
        year, month = year - 1, 12
    elif month > 12:
        year, month = year + 1, 1

    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    cal_module.setfirstweekday(cal_module.SUNDAY)
    semanas_numeros = cal_module.monthcalendar(year, month)

    citas_mes = (
        Cita.objects.filter(fecha__year=year, fecha__month=month)
        .select_related('cliente', 'vehiculo', 'tipo_servicio')
        .order_by('hora')
    )
    citas_por_dia = {}
    for c in citas_mes:
        citas_por_dia.setdefault(c.fecha.day, []).append(c)

    semanas = []
    for semana in semanas_numeros:
        fila = []
        for dia in semana:
            if dia == 0:
                fila.append(None)
            else:
                fila.append({
                    'numero': dia,
                    'fecha_iso': date(year, month, dia).isoformat(),
                    'es_hoy': date(year, month, dia) == hoy,
                    'citas': citas_por_dia.get(dia, []),
                })
        semanas.append(fila)

    return render(request, 'agenda/calendario.html', {
        'semanas': semanas,
        'mes_nombre': MESES[month],
        'year': year, 'month': month,
        'prev_year': prev_year, 'prev_month': prev_month,
        'next_year': next_year, 'next_month': next_month,
        'hoy_year': hoy.year, 'hoy_month': hoy.month,
        'total_mes': citas_mes.count(),
        'pendientes_mes': citas_mes.filter(estado='pendiente').count(),
        'estados': ESTADO_CHOICES,
    })


def cita_crear(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save()
            messages.success(request, 'Cita agendada.')
            return _redirect_a_mes(cita.fecha)
    else:
        initial = {}
        fecha_qs = request.GET.get('fecha')
        if fecha_qs:
            initial['fecha'] = fecha_qs
        form = CitaForm(initial=initial)
    return render(request, 'agenda/cita_form.html', {'form': form, 'titulo': 'Nueva Cita'})


def cita_editar(request, pk):
    obj = get_object_or_404(Cita, pk=pk)
    if request.method == 'POST':
        form = CitaForm(request.POST, instance=obj)
        if form.is_valid():
            cita = form.save()
            messages.success(request, 'Cita actualizada.')
            return _redirect_a_mes(cita.fecha)
    else:
        form = CitaForm(instance=obj)
    return render(request, 'agenda/cita_form.html', {'form': form, 'titulo': 'Editar Cita', 'obj': obj})


def cita_eliminar(request, pk):
    obj = get_object_or_404(Cita, pk=pk)
    if request.method == 'POST':
        fecha = obj.fecha
        obj.delete()
        messages.success(request, 'Cita eliminada.')
        return _redirect_a_mes(fecha)
    return render(request, 'agenda/confirmar_eliminar.html', {'obj': obj})


def cita_estado(request, pk):
    obj = get_object_or_404(Cita, pk=pk)
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in dict(ESTADO_CHOICES):
            obj.estado = nuevo_estado
            obj.save(update_fields=['estado'])
    return _redirect_a_mes(obj.fecha)
