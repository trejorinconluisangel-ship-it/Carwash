import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import TipoServicio, TipoVehiculo, InsumoEnServicio, Servicio
from .forms import TipoServicioForm, TipoVehiculoForm, InsumoEnServicioForm, ServicioForm
from clientes.models import VISITAS_PREMIO_PEQUENO, VISITAS_PREMIO_GRANDE


# ── Tipos de Servicio ────────────────────────────────────────────────────────

def tipo_servicio_lista(request):
    tipos = TipoServicio.objects.prefetch_related('insumos_requeridos__insumo').all()
    return render(request, 'servicios/tipo_servicio_lista.html', {'tipos': tipos})


def tipo_servicio_crear(request):
    form = TipoServicioForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Tipo de servicio creado.')
        return redirect('tipo_servicio_lista')
    return render(request, 'servicios/tipo_servicio_form.html', {'form': form, 'titulo': 'Nuevo Tipo de Servicio'})


def tipo_servicio_editar(request, pk):
    obj = get_object_or_404(TipoServicio, pk=pk)
    form = TipoServicioForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Tipo de servicio actualizado.')
        return redirect('tipo_servicio_lista')
    return render(request, 'servicios/tipo_servicio_form.html', {'form': form, 'titulo': 'Editar', 'obj': obj})


def tipo_servicio_eliminar(request, pk):
    obj = get_object_or_404(TipoServicio, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Tipo de servicio eliminado.')
        return redirect('tipo_servicio_lista')
    return render(request, 'servicios/confirmar_eliminar.html', {'obj': obj, 'tipo': 'tipo de servicio'})


# ── Tipos de Vehículo ────────────────────────────────────────────────────────

def tipo_vehiculo_lista(request):
    tipos = TipoVehiculo.objects.all()
    return render(request, 'servicios/tipo_vehiculo_lista.html', {'tipos': tipos})


def tipo_vehiculo_crear(request):
    form = TipoVehiculoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Tipo de vehículo creado.')
        return redirect('tipo_vehiculo_lista')
    return render(request, 'servicios/tipo_vehiculo_form.html', {'form': form, 'titulo': 'Nuevo Tipo de Vehículo'})


def tipo_vehiculo_editar(request, pk):
    obj = get_object_or_404(TipoVehiculo, pk=pk)
    form = TipoVehiculoForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Tipo de vehículo actualizado.')
        return redirect('tipo_vehiculo_lista')
    return render(request, 'servicios/tipo_vehiculo_form.html', {'form': form, 'titulo': 'Editar', 'obj': obj})


def tipo_vehiculo_eliminar(request, pk):
    obj = get_object_or_404(TipoVehiculo, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Tipo de vehículo eliminado.')
        return redirect('tipo_vehiculo_lista')
    return render(request, 'servicios/confirmar_eliminar.html', {'obj': obj, 'tipo': 'tipo de vehículo'})


# ── Insumos en Servicio ──────────────────────────────────────────────────────

def insumo_servicio_lista(request):
    relaciones = InsumoEnServicio.objects.select_related('tipo_servicio', 'insumo').all()
    return render(request, 'servicios/insumo_servicio_lista.html', {'relaciones': relaciones})


def insumo_servicio_crear(request):
    form = InsumoEnServicioForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Relación insumo-servicio creada.')
        return redirect('insumo_servicio_lista')
    return render(request, 'servicios/insumo_servicio_form.html', {'form': form, 'titulo': 'Asignar Insumo a Servicio'})


def insumo_servicio_eliminar(request, pk):
    obj = get_object_or_404(InsumoEnServicio, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Relación eliminada.')
        return redirect('insumo_servicio_lista')
    return render(request, 'servicios/confirmar_eliminar.html', {'obj': obj, 'tipo': 'relación'})


# ── Servicios del día ────────────────────────────────────────────────────────

def servicio_lista(request):
    servicios = Servicio.objects.select_related('tipo_servicio', 'tipo_vehiculo').all()
    return render(request, 'servicios/servicio_lista.html', {'servicios': servicios})


def servicio_crear(request):
    tipos_servicio = TipoServicio.objects.filter(activo=True)
    tipos_vehiculo = TipoVehiculo.objects.all()

    # Precios sugeridos para JS: {tipo_servicio_id: {tipo_vehiculo_id: precio}}
    precios_data = {}
    for ts in tipos_servicio:
        precios_data[ts.pk] = {'precio_base': float(ts.precio_base), 'vehiculos': {}}
        for tv in tipos_vehiculo:
            precios_data[ts.pk]['vehiculos'][tv.pk] = round(float(ts.precio_base) * float(tv.multiplicador_precio), 2)

    form = ServicioForm(request.POST or None)
    if form.is_valid():
        servicio = form.save()
        messages.success(request, 'Servicio registrado. Stock de insumos actualizado.')

        cliente = servicio.cliente
        if cliente and float(servicio.precio_cobrado or 0) > 0:
            cliente.visitas_lealtad += 1
            cliente.save(update_fields=['visitas_lealtad'])
            if cliente.visitas_lealtad >= VISITAS_PREMIO_GRANDE:
                return redirect('premio_grande', pk=cliente.pk)
            elif cliente.visitas_lealtad == VISITAS_PREMIO_PEQUENO:
                return redirect('premio_pequeno', pk=cliente.pk)

        return redirect('servicio_lista')

    return render(request, 'servicios/servicio_form.html', {
        'form': form,
        'titulo': 'Registrar Servicio',
        'precios_json': json.dumps(precios_data),
        'tipos_servicio': tipos_servicio,
        'tipos_vehiculo': tipos_vehiculo,
    })


def servicio_eliminar(request, pk):
    obj = get_object_or_404(Servicio, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Servicio eliminado.')
        return redirect('servicio_lista')
    return render(request, 'servicios/confirmar_eliminar.html', {'obj': obj, 'tipo': 'servicio'})


def precio_sugerido_api(request):
    """API simple para calcular precio sugerido en JS."""
    ts_id = request.GET.get('tipo_servicio')
    tv_id = request.GET.get('tipo_vehiculo')
    try:
        ts = TipoServicio.objects.get(pk=ts_id)
        tv = TipoVehiculo.objects.get(pk=tv_id)
        precio = round(float(ts.precio_base) * float(tv.multiplicador_precio), 2)
        return JsonResponse({'precio': precio})
    except Exception:
        return JsonResponse({'precio': 0})
