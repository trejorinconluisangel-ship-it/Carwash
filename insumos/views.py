from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum, F
from .models import Proveedor, Insumo, Compra
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
    insumos = Insumo.objects.select_related('proveedor').all()
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
    servicios_posibles = insumo.servicios_posibles()
    return render(request, 'insumos/insumo_detalle.html', {
        'insumo': insumo,
        'compras': compras,
        'servicios_posibles': servicios_posibles,
    })


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
        # Revertir stock
        obj.insumo.stock_actual -= obj.cantidad
        if obj.insumo.stock_actual < 0:
            obj.insumo.stock_actual = 0
        obj.insumo.save(update_fields=['stock_actual'])
        obj.delete()
        messages.success(request, 'Compra eliminada y stock revertido.')
        return redirect('compra_lista')
    return render(request, 'insumos/confirmar_eliminar.html', {'obj': obj, 'tipo': 'compra'})
