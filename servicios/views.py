import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import (
    TipoServicio, TipoVehiculo, Servicio, PrecioPaquete,
    NEGOCIO_NOMBRE, NEGOCIO_DIRECCION, NEGOCIO_WHATSAPP_1, NEGOCIO_WHATSAPP_2, NEGOCIO_FACEBOOK,
)
from .forms import TipoServicioForm, TipoVehiculoForm, ServicioForm
from clientes.models import VISITAS_PREMIO_PEQUENO, VISITAS_PREMIO_GRANDE, TIPO_VEHICULO_CHOICES


# Mapeo best-effort del tipo de vehículo del cliente (moto/sedan/pickup...) a una
# categoría de precio (TipoVehiculo). Es solo una sugerencia inicial; el usuario
# siempre puede cambiar la categoría manualmente al registrar el servicio.
_TIPO_KEYWORDS = {
    'moto': [],
    'auto_chico': ['compactos'],
    'sedan': ['sedan', 'sedán'],
    'pickup': ['pick up', 'pick'],
    'camioneta': ['familiar'],
    'van': ['pasajeros'],
    'camion': ['grande'],
}


def _mapear_tipo_vehiculo(codigo_cliente, tipos_vehiculo):
    keywords = _TIPO_KEYWORDS.get(codigo_cliente, [])
    for tv in tipos_vehiculo:
        nombre = tv.nombre.lower()
        if any(k in nombre for k in keywords):
            return tv.pk
    return None


# ── Tipos de Servicio ────────────────────────────────────────────────────────

def tipo_servicio_lista(request):
    tipos = TipoServicio.objects.prefetch_related('insumos').all()
    return render(request, 'servicios/tipo_servicio_lista.html', {'tipos': tipos})


def tipo_servicio_crear(request):
    form = TipoServicioForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Tipo de servicio creado.')
        return redirect('precio_paquete_grid')
    return render(request, 'servicios/tipo_servicio_form.html', {'form': form, 'titulo': 'Nuevo Tipo de Servicio'})


def tipo_servicio_editar(request, pk):
    obj = get_object_or_404(TipoServicio, pk=pk)
    form = TipoServicioForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Tipo de servicio actualizado.')
        return redirect('precio_paquete_grid')
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
        return redirect('precio_paquete_grid')
    return render(request, 'servicios/tipo_vehiculo_form.html', {'form': form, 'titulo': 'Nuevo Tipo de Vehículo'})


def tipo_vehiculo_editar(request, pk):
    obj = get_object_or_404(TipoVehiculo, pk=pk)
    form = TipoVehiculoForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Tipo de vehículo actualizado.')
        return redirect('precio_paquete_grid')
    return render(request, 'servicios/tipo_vehiculo_form.html', {'form': form, 'titulo': 'Editar', 'obj': obj})


def tipo_vehiculo_eliminar(request, pk):
    obj = get_object_or_404(TipoVehiculo, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Tipo de vehículo eliminado.')
        return redirect('tipo_vehiculo_lista')
    return render(request, 'servicios/confirmar_eliminar.html', {'obj': obj, 'tipo': 'tipo de vehículo'})


# ── Precios de Paquetes ──────────────────────────────────────────────────────

def precio_paquete_grid(request):
    tipos_servicio = list(TipoServicio.objects.filter(activo=True))
    tipos_vehiculo = list(TipoVehiculo.objects.filter(activo=True))

    if request.method == 'POST':
        for ts in tipos_servicio:
            for tv in tipos_vehiculo:
                valor = request.POST.get(f'precio_{ts.pk}_{tv.pk}', '').strip()
                if valor == '':
                    continue
                try:
                    precio = round(float(valor), 2)
                except ValueError:
                    continue
                PrecioPaquete.objects.update_or_create(
                    tipo_servicio=ts, tipo_vehiculo=tv, defaults={'precio': precio}
                )
        messages.success(request, 'Precios actualizados.')
        return redirect('precio_paquete_grid')

    precios = {
        (p.tipo_servicio_id, p.tipo_vehiculo_id): p.precio
        for p in PrecioPaquete.objects.filter(tipo_servicio__in=tipos_servicio, tipo_vehiculo__in=tipos_vehiculo)
    }
    paquetes = [
        (ts, [(tv, precios.get((ts.pk, tv.pk))) for tv in tipos_vehiculo])
        for ts in tipos_servicio
    ]

    return render(request, 'servicios/precio_paquete_grid.html', {
        'paquetes': paquetes,
        'tipos_vehiculo': tipos_vehiculo,
    })


# ── Servicios del día ────────────────────────────────────────────────────────

def servicio_lista(request):
    servicios = Servicio.objects.select_related('tipo_servicio', 'tipo_vehiculo').all()
    return render(request, 'servicios/servicio_lista.html', {'servicios': servicios})


def servicio_crear(request):
    tipos_servicio = TipoServicio.objects.filter(activo=True)
    tipos_vehiculo = TipoVehiculo.objects.filter(activo=True)

    # Precios sugeridos para JS: {tipo_servicio_id: {tipo_vehiculo_id: precio}}
    precios_pp = {
        (p.tipo_servicio_id, p.tipo_vehiculo_id): float(p.precio)
        for p in PrecioPaquete.objects.filter(tipo_servicio__in=tipos_servicio, tipo_vehiculo__in=tipos_vehiculo)
    }
    precios_data = {}
    for ts in tipos_servicio:
        precios_data[ts.pk] = {'vehiculos': {}}
        for tv in tipos_vehiculo:
            precios_data[ts.pk]['vehiculos'][tv.pk] = precios_pp.get((ts.pk, tv.pk), 0)

    # Mapa tipo de vehículo del cliente (moto/sedan/pickup...) → TipoVehiculo (categoría de precio)
    tipo_map = {codigo: _mapear_tipo_vehiculo(codigo, tipos_vehiculo) for codigo, _ in TIPO_VEHICULO_CHOICES}

    recepcion_id = request.GET.get('recepcion') or request.POST.get('recepcion_id')
    recepcion_obj = None
    if recepcion_id:
        from recepcion.models import Recepcion
        recepcion_obj = Recepcion.objects.filter(pk=recepcion_id).first()

    initial = {}
    if request.method == 'GET':
        for campo in ('cliente', 'vehiculo', 'tipo_servicio', 'tipo_vehiculo', 'fecha'):
            valor = request.GET.get(campo)
            if valor:
                initial[campo] = valor

    form = ServicioForm(request.POST or None, initial=initial)
    if form.is_valid():
        if form.cleaned_data.get('es_cortesia'):
            form.instance.precio_cobrado = 0
        form.instance._insumos_override = list(form.cleaned_data.get('insumos_usados') or [])
        servicio = form.save()
        if servicio.es_cortesia:
            messages.success(request, 'Servicio registrado como cortesía — no se cobró.')
        else:
            messages.success(request, 'Servicio registrado.')

        if recepcion_obj:
            recepcion_obj.servicio = servicio
            recepcion_obj.save(update_fields=['servicio'])

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
        'tipo_map_json': json.dumps(tipo_map),
        'tipos_servicio': tipos_servicio,
        'tipos_vehiculo': tipos_vehiculo,
        'recepcion_obj': recepcion_obj,
    })


def servicio_ticket(request, pk):
    servicio = get_object_or_404(
        Servicio.objects.select_related('tipo_servicio', 'tipo_vehiculo', 'cliente', 'vehiculo'),
        pk=pk,
    )
    return render(request, 'servicios/servicio_ticket.html', {
        'servicio': servicio,
        'negocio_nombre': NEGOCIO_NOMBRE,
        'negocio_direccion': NEGOCIO_DIRECCION,
        'negocio_whatsapp_1': NEGOCIO_WHATSAPP_1,
        'negocio_whatsapp_2': NEGOCIO_WHATSAPP_2,
        'negocio_facebook': NEGOCIO_FACEBOOK,
    })


def servicio_eliminar(request, pk):
    obj = get_object_or_404(Servicio, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Servicio eliminado.')
        return redirect('servicio_lista')
    return render(request, 'servicios/confirmar_eliminar.html', {'obj': obj, 'tipo': 'servicio'})


def precio_sugerido_api(request):
    """API simple para consultar el precio fijo de un paquete + categoría de vehículo."""
    ts_id = request.GET.get('tipo_servicio')
    tv_id = request.GET.get('tipo_vehiculo')
    pp = PrecioPaquete.objects.filter(tipo_servicio_id=ts_id, tipo_vehiculo_id=tv_id).first()
    return JsonResponse({'precio': float(pp.precio) if pp else 0})
