from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum, F, Case, When, IntegerField
from django.utils import timezone
from .models import Proveedor, Insumo, Compra, EnvaseEnUso, ItemLista, Recordatorio, CATEGORIA_CHOICES, PRIORIDAD_LISTA
from .forms import ProveedorForm, InsumoForm, CompraForm


# ── Proveedores ─────────────────────────────────────────────────────────────

def proveedor_lista(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'insumos/proveedor_lista.html', {'proveedores': proveedores})


def proveedor_crear(request):
    form = ProveedorForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Proveedor registrado correctamente.')
        return redirect('proveedor_lista')
    return render(request, 'insumos/proveedor_form.html', {'form': form, 'titulo': 'Nuevo Proveedor'})


def proveedor_editar(request, pk):
    obj = get_object_or_404(Proveedor, pk=pk)
    form = ProveedorForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Proveedor actualizado.')
        return redirect('proveedor_lista')
    return render(request, 'insumos/proveedor_form.html', {'form': form, 'titulo': 'Editar Proveedor', 'obj': obj})


def proveedor_eliminar(request, pk):
    obj = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Proveedor eliminado.')
        return redirect('proveedor_lista')
    return render(request, 'insumos/confirmar_eliminar.html', {'obj': obj, 'tipo': 'proveedor'})


# ── Insumos ──────────────────────────────────────────────────────────────────

def insumo_lista(request):
    from django.db.models import OuterRef, Subquery
    from comparador.models import Producto as ComparadorProducto
    cp_subq = ComparadorProducto.objects.filter(insumo=OuterRef('pk')).values('pk')[:1]
    insumos = Insumo.objects.select_related('proveedor').annotate(
        comparador_pk=Subquery(cp_subq)
    )
    return render(request, 'insumos/insumo_lista.html', {'insumos': insumos})


def insumo_crear(request):
    form = InsumoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Insumo registrado correctamente.')
        return redirect('insumo_lista')
    return render(request, 'insumos/insumo_form.html', {'form': form, 'titulo': 'Nuevo Insumo'})


def insumo_editar(request, pk):
    obj = get_object_or_404(Insumo, pk=pk)
    form = InsumoForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Insumo actualizado.')
        return redirect('insumo_lista')
    return render(request, 'insumos/insumo_form.html', {'form': form, 'titulo': 'Editar Insumo', 'obj': obj})


def insumo_eliminar(request, pk):
    obj = get_object_or_404(Insumo, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Insumo eliminado.')
        return redirect('insumo_lista')
    return render(request, 'insumos/confirmar_eliminar.html', {'obj': obj, 'tipo': 'insumo'})


def insumo_detalle(request, pk):
    insumo = get_object_or_404(Insumo, pk=pk)
    compras = insumo.compras.all()[:10]
    return render(request, 'insumos/insumo_detalle.html', {
        'insumo': insumo,
        'compras': compras,
        'envase_activo': insumo.envase_activo,
        'envases_terminados': insumo.envases_terminados[:10],
    })


def envase_abrir(request, pk):
    insumo = get_object_or_404(Insumo, pk=pk)
    if request.method == 'POST':
        if insumo.envase_activo:
            messages.error(request, 'Ya hay un envase en uso. Márcalo como terminado antes de abrir otro.')
        elif insumo.envases_en_bodega <= 0:
            messages.error(request, 'No hay envases en bodega. Registra una compra primero.')
        else:
            EnvaseEnUso.objects.create(insumo=insumo, costo_envase=insumo.costo_envase,
                                       contenido_envase=insumo.contenido_envase)
            insumo.envases_en_bodega -= 1
            insumo.save(update_fields=['envases_en_bodega'])
            messages.success(request, 'Envase abierto. A partir de ahora se cuentan los vehículos atendidos.')
    return redirect('insumo_detalle', pk=pk)


def envase_terminar(request, pk):
    insumo = get_object_or_404(Insumo, pk=pk)
    if request.method == 'POST':
        envase = insumo.envase_activo
        if envase:
            envase.fecha_fin = timezone.localdate()
            envase.save(update_fields=['fecha_fin'])
            messages.success(request, f'Envase marcado como terminado — rindió {envase.vehiculos_atendidos} vehículos.')
        else:
            messages.error(request, 'Este insumo no tiene un envase en uso.')
    return redirect('insumo_detalle', pk=pk)


# ── Compras ──────────────────────────────────────────────────────────────────

def compra_lista(request):
    compras = Compra.objects.select_related('insumo', 'proveedor').all()
    total_gastado = compras.aggregate(total=Sum('costo_total'))['total'] or 0
    return render(request, 'insumos/compra_lista.html', {'compras': compras, 'total_gastado': total_gastado})


def compra_crear(request):
    form = CompraForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Compra registrada. Stock actualizado.')
        return redirect('compra_lista')
    return render(request, 'insumos/compra_form.html', {'form': form, 'titulo': 'Registrar Compra'})


def compra_eliminar(request, pk):
    obj = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST':
        # Revertir envases en bodega
        obj.insumo.envases_en_bodega = max(0, obj.insumo.envases_en_bodega - obj.envases)
        obj.insumo.save(update_fields=['envases_en_bodega'])
        obj.delete()
        messages.success(request, 'Compra eliminada y envases revertidos.')
        return redirect('compra_lista')
    return render(request, 'insumos/confirmar_eliminar.html', {'obj': obj, 'tipo': 'compra'})


# ── Orden de prioridad compartido ────────────────────────────────────────────
_PRIO_ORDER = Case(
    When(prioridad='fuego',    then=0),
    When(prioridad='pronto',   then=1),
    When(prioridad='sinprisa', then=2),
    default=3,
    output_field=IntegerField(),
)


# ── Lista de compras ─────────────────────────────────────────────────────────

def lista_compras(request):
    filtro_cat  = request.GET.get('cat', '')
    filtro_prov = request.GET.get('prov', '')

    items = (
        ItemLista.objects
        .select_related('insumo', 'proveedor')
        .annotate(orden_prio=_PRIO_ORDER)
        .order_by('comprado', 'orden_prio', '-created_at')
    )
    if filtro_cat:
        from django.db.models import Q
        items = items.filter(
            Q(insumo__categoria=filtro_cat) | Q(insumo__isnull=True)
        ) if filtro_cat else items
        items = items.filter(Q(insumo__categoria=filtro_cat))
    if filtro_prov:
        items = items.filter(proveedor_id=filtro_prov)

    recordatorios = (
        Recordatorio.objects
        .annotate(orden_prio=_PRIO_ORDER)
        .order_by('completado', 'orden_prio', '-created_at')
    )

    pendientes   = items.filter(comprado=False).count()
    fuego_count  = items.filter(comprado=False, prioridad='fuego').count()
    pronto_count = items.filter(comprado=False, prioridad='pronto').count()

    return render(request, 'insumos/lista_compras.html', {
        'items':        items,
        'recordatorios': recordatorios,
        'pendientes':   pendientes,
        'fuego_count':  fuego_count,
        'pronto_count': pronto_count,
        'insumos':      Insumo.objects.order_by('nombre'),
        'proveedores':  Proveedor.objects.order_by('nombre'),
        'categorias':   CATEGORIA_CHOICES,
        'prioridades':  PRIORIDAD_LISTA,
        'filtro_cat':   filtro_cat,
        'filtro_prov':  filtro_prov,
    })


def item_crear(request):
    if request.method == 'POST':
        insumo_id    = request.POST.get('insumo') or None
        nombre_libre = request.POST.get('nombre_libre', '').strip()
        cantidad     = request.POST.get('cantidad', '').strip()
        proveedor_id = request.POST.get('proveedor') or None
        prioridad    = request.POST.get('prioridad', 'sinprisa')
        notas        = request.POST.get('notas', '').strip()

        if insumo_id or nombre_libre:
            item = ItemLista(
                cantidad=cantidad, prioridad=prioridad, notas=notas,
            )
            if insumo_id:
                item.insumo_id = insumo_id
            else:
                item.nombre_libre = nombre_libre
            if proveedor_id:
                item.proveedor_id = proveedor_id
            item.save()
            messages.success(request, f'"{item.nombre_display}" agregado a la lista.')
        else:
            messages.error(request, 'Escribe el nombre del producto o selecciona un insumo.')
    return redirect('lista_compras')


def item_toggle(request, pk):
    if request.method == 'POST':
        from django.utils import timezone
        item = get_object_or_404(ItemLista, pk=pk)
        item.comprado = not item.comprado
        item.fecha_compra = timezone.now() if item.comprado else None
        item.save(update_fields=['comprado', 'fecha_compra'])
    return redirect('lista_compras')


def item_eliminar_lista(request, pk):
    if request.method == 'POST':
        get_object_or_404(ItemLista, pk=pk).delete()
    return redirect('lista_compras')


def recordatorio_crear(request):
    if request.method == 'POST':
        texto     = request.POST.get('texto', '').strip()
        prioridad = request.POST.get('prioridad', 'sinprisa')
        if texto:
            Recordatorio.objects.create(texto=texto, prioridad=prioridad)
        else:
            messages.error(request, 'Escribe el recordatorio.')
    return redirect('lista_compras')


def recordatorio_toggle(request, pk):
    if request.method == 'POST':
        from django.utils import timezone
        r = get_object_or_404(Recordatorio, pk=pk)
        r.completado = not r.completado
        r.fecha_completado = timezone.now() if r.completado else None
        r.save(update_fields=['completado', 'fecha_completado'])
    return redirect('lista_compras')


def recordatorio_eliminar(request, pk):
    if request.method == 'POST':
        get_object_or_404(Recordatorio, pk=pk).delete()
    return redirect('lista_compras')
