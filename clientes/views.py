from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum
from .models import Cliente, Vehiculo, VISITAS_PREMIO_PEQUENO, VISITAS_PREMIO_GRANDE
from .forms import ClienteForm, VehiculoForm, VehiculoSinClienteForm


# ── Clientes ─────────────────────────────────────────────────────────────────

def cliente_lista(request):
    q = request.GET.get('q', '').strip()
    clientes = Cliente.objects.prefetch_related('vehiculos').all()
    if q:
        clientes = clientes.filter(nombre__icontains=q) | clientes.filter(whatsapp__icontains=q)
    return render(request, 'clientes/cliente_lista.html', {'clientes': clientes, 'q': q})


def promocion_masiva(request):
    from django.utils import timezone

    q = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '')
    try:
        dias_inactivo = int(request.GET.get('dias_inactivo', '30'))
    except ValueError:
        dias_inactivo = 30

    hoy = timezone.localdate()

    base_qs = Cliente.objects.exclude(whatsapp='').prefetch_related('vehiculos', 'servicios')
    if q:
        base_qs = base_qs.filter(nombre__icontains=q)

    clientes_calc = []
    for c in base_qs:
        servicios_list = list(c.servicios.all())
        c.num_servicios = len(servicios_list)
        c.num_vehiculos_calc = len(list(c.vehiculos.all()))
        c.ultima_visita_calc = max((s.fecha for s in servicios_list), default=None)
        c.total_gastado_calc = sum(float(s.precio_cobrado) for s in servicios_list)
        c.dias_sin_venir = (hoy - c.ultima_visita_calc).days if c.ultima_visita_calc else None
        c.es_primerizo = c.num_servicios == 1
        c.es_inactivo = c.dias_sin_venir is not None and c.dias_sin_venir >= dias_inactivo
        c.es_frecuente = c.visitas_lealtad >= VISITAS_PREMIO_PEQUENO
        c.es_multi_vehiculo = c.num_vehiculos_calc > 1
        c.es_cumple_mes = bool(c.fecha_nacimiento and c.fecha_nacimiento.month == hoy.month)
        c.es_premio_grande = c.visitas_lealtad >= VISITAS_PREMIO_GRANDE
        clientes_calc.append(c)

    conteos = {
        'primerizos':     sum(1 for c in clientes_calc if c.es_primerizo),
        'inactivos':      sum(1 for c in clientes_calc if c.es_inactivo),
        'frecuentes':     sum(1 for c in clientes_calc if c.es_frecuente),
        'multi_vehiculo': sum(1 for c in clientes_calc if c.es_multi_vehiculo),
        'cumple_mes':     sum(1 for c in clientes_calc if c.es_cumple_mes),
        'premio_grande':  sum(1 for c in clientes_calc if c.es_premio_grande),
        'top_gasto':      sum(1 for c in clientes_calc if c.total_gastado_calc > 0),
    }

    if categoria == 'primerizos':
        clientes = [c for c in clientes_calc if c.es_primerizo]
    elif categoria == 'inactivos':
        clientes = [c for c in clientes_calc if c.es_inactivo]
    elif categoria == 'frecuentes':
        clientes = [c for c in clientes_calc if c.es_frecuente]
    elif categoria == 'multi_vehiculo':
        clientes = [c for c in clientes_calc if c.es_multi_vehiculo]
    elif categoria == 'cumple_mes':
        clientes = [c for c in clientes_calc if c.es_cumple_mes]
    elif categoria == 'premio_grande':
        clientes = [c for c in clientes_calc if c.es_premio_grande]
    elif categoria == 'top_gasto':
        clientes = sorted((c for c in clientes_calc if c.total_gastado_calc > 0), key=lambda c: -c.total_gastado_calc)[:20]
    else:
        clientes = clientes_calc

    sin_whatsapp = Cliente.objects.filter(whatsapp='').count()

    return render(request, 'clientes/promocion_masiva.html', {
        'clientes': clientes,
        'q': q,
        'categoria': categoria,
        'dias_inactivo': dias_inactivo,
        'conteos': conteos,
        'sin_whatsapp': sin_whatsapp,
    })


def cliente_crear(request):
    form = ClienteForm(request.POST or None)
    if form.is_valid():
        cliente = form.save()
        messages.success(request, f'Cliente "{cliente.nombre}" registrado.')
        return redirect('cliente_detalle', pk=cliente.pk)
    return render(request, 'clientes/cliente_form.html', {'form': form, 'titulo': 'Nuevo Cliente'})


def cliente_editar(request, pk):
    obj = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Cliente actualizado.')
        return redirect('cliente_detalle', pk=obj.pk)
    return render(request, 'clientes/cliente_form.html', {'form': form, 'titulo': 'Editar Cliente', 'obj': obj})


def cliente_eliminar(request, pk):
    obj = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Cliente eliminado.')
        return redirect('cliente_lista')
    return render(request, 'clientes/confirmar_eliminar.html', {'obj': obj, 'tipo': 'cliente'})


def cliente_detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    vehiculos = cliente.vehiculos.all()
    from servicios.models import Servicio
    servicios = Servicio.objects.filter(cliente=cliente).select_related(
        'tipo_servicio', 'tipo_vehiculo', 'vehiculo'
    ).order_by('-fecha', '-hora')
    total_gastado = servicios.aggregate(t=Sum('precio_cobrado'))['t'] or 0
    return render(request, 'clientes/cliente_detalle.html', {
        'cliente': cliente,
        'vehiculos': vehiculos,
        'servicios': servicios,
        'total_servicios': servicios.count(),
        'total_gastado': total_gastado,
        'meta_pequeno': VISITAS_PREMIO_PEQUENO,
        'meta_grande': VISITAS_PREMIO_GRANDE,
    })


# ── Vehículos ─────────────────────────────────────────────────────────────────

def vehiculo_crear(request, cliente_pk):
    cliente = get_object_or_404(Cliente, pk=cliente_pk)
    form = VehiculoSinClienteForm(request.POST or None)
    if form.is_valid():
        v = form.save(commit=False)
        v.cliente = cliente
        v.save()
        messages.success(request, f'Vehículo {v.placa} agregado a {cliente.nombre}.')
        return redirect('cliente_detalle', pk=cliente.pk)
    return render(request, 'clientes/vehiculo_form.html', {
        'form': form, 'titulo': 'Agregar Vehículo', 'cliente': cliente
    })


def vehiculo_editar(request, pk):
    obj = get_object_or_404(Vehiculo, pk=pk)
    form = VehiculoSinClienteForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Vehículo actualizado.')
        return redirect('cliente_detalle', pk=obj.cliente.pk)
    return render(request, 'clientes/vehiculo_form.html', {
        'form': form, 'titulo': 'Editar Vehículo', 'cliente': obj.cliente, 'obj': obj
    })


def vehiculo_eliminar(request, pk):
    obj = get_object_or_404(Vehiculo, pk=pk)
    cliente_pk = obj.cliente.pk
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Vehículo eliminado.')
        return redirect('cliente_detalle', pk=cliente_pk)
    return render(request, 'clientes/confirmar_eliminar.html', {'obj': obj, 'tipo': 'vehículo'})


# ── Lealtad ──────────────────────────────────────────────────────────────────

def premio_pequeno(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'clientes/premio_pequeno.html', {
        'cliente': cliente,
        'meta_pequeno': VISITAS_PREMIO_PEQUENO,
        'meta_grande': VISITAS_PREMIO_GRANDE,
    })


def premio_grande(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'clientes/premio_grande.html', {
        'cliente': cliente,
        'meta_grande': VISITAS_PREMIO_GRANDE,
    })


def canjear_premio_grande(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        from django.utils import timezone
        cliente.visitas_lealtad = 0
        cliente.fecha_ultimo_premio = timezone.now().date()
        cliente.save(update_fields=['visitas_lealtad', 'fecha_ultimo_premio'])
        messages.success(request, f'Premio grande canjeado para {cliente.nombre}. Contador reiniciado a 0.')
    return redirect('servicio_lista')


def reiniciar_lealtad(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.visitas_lealtad = 0
        cliente.save(update_fields=['visitas_lealtad'])
        messages.success(request, f'Contador de lealtad reiniciado para {cliente.nombre}.')
    return redirect('cliente_detalle', pk=pk)


# ── API para JS en el form de servicio ───────────────────────────────────────

def vehiculos_por_cliente_api(request):
    cliente_pk = request.GET.get('cliente_pk')
    if not cliente_pk:
        return JsonResponse({'vehiculos': []})
    vehiculos = Vehiculo.objects.filter(cliente_id=cliente_pk).values(
        'pk', 'placa', 'marca', 'modelo', 'color', 'tipo'
    )
    return JsonResponse({'vehiculos': list(vehiculos)})
