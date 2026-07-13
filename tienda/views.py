from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count
from .models import ProductoTienda, EntradaProducto, VentaProducto
from .forms import ProductoTiendaForm, EntradaProductoForm, VentaProductoForm


# ── Productos ────────────────────────────────────────────────────────────────

def producto_lista(request):
    productos = ProductoTienda.objects.select_related('proveedor').filter(activo=True)
    total_valor = sum(p.valor_inventario for p in productos)
    return render(request, 'tienda/producto_lista.html', {
        'productos': productos,
        'total_valor': total_valor,
    })


def producto_crear(request):
    form = ProductoTiendaForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Producto registrado correctamente.')
        return redirect('producto_lista')
    return render(request, 'tienda/producto_form.html', {'form': form, 'titulo': 'Nuevo Producto'})


def producto_editar(request, pk):
    obj = get_object_or_404(ProductoTienda, pk=pk)
    form = ProductoTiendaForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Producto actualizado.')
        return redirect('producto_lista')
    return render(request, 'tienda/producto_form.html', {'form': form, 'titulo': 'Editar Producto', 'obj': obj})


def producto_eliminar(request, pk):
    obj = get_object_or_404(ProductoTienda, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Producto eliminado.')
        return redirect('producto_lista')
    return render(request, 'tienda/confirmar_eliminar.html', {'obj': obj, 'tipo': 'producto'})


def producto_detalle(request, pk):
    producto = get_object_or_404(ProductoTienda, pk=pk)
    entradas = producto.entradas.all()[:10]
    ventas = producto.ventas.all()[:10]
    total_vendido = producto.ventas.aggregate(t=Sum('total_venta'))['t'] or 0
    total_ganancia = producto.ventas.aggregate(t=Sum('ganancia'))['t'] or 0
    return render(request, 'tienda/producto_detalle.html', {
        'producto': producto,
        'entradas': entradas,
        'ventas': ventas,
        'total_vendido': total_vendido,
        'total_ganancia': total_ganancia,
    })


# ── Entradas de producto ──────────────────────────────────────────────────────

def entrada_lista(request):
    entradas = EntradaProducto.objects.select_related('producto', 'proveedor').all()
    total_invertido = entradas.aggregate(t=Sum('costo_total'))['t'] or 0
    return render(request, 'tienda/entrada_lista.html', {
        'entradas': entradas,
        'total_invertido': total_invertido,
    })


def entrada_crear(request):
    form = EntradaProductoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Entrada registrada. Stock actualizado.')
        return redirect('entrada_lista')
    return render(request, 'tienda/entrada_form.html', {'form': form, 'titulo': 'Registrar Entrada de Producto'})


def entrada_eliminar(request, pk):
    obj = get_object_or_404(EntradaProducto, pk=pk)
    if request.method == 'POST':
        obj.producto.stock_actual -= obj.cantidad
        if obj.producto.stock_actual < 0:
            obj.producto.stock_actual = 0
        obj.producto.save(update_fields=['stock_actual'])
        obj.delete()
        messages.success(request, 'Entrada eliminada y stock revertido.')
        return redirect('entrada_lista')
    return render(request, 'tienda/confirmar_eliminar.html', {'obj': obj, 'tipo': 'entrada'})


# ── Ventas ────────────────────────────────────────────────────────────────────

def venta_lista(request):
    ventas = VentaProducto.objects.select_related('producto').all()
    total_ventas = ventas.aggregate(t=Sum('total_venta'))['t'] or 0
    total_ganancia = ventas.aggregate(t=Sum('ganancia'))['t'] or 0
    return render(request, 'tienda/venta_lista.html', {
        'ventas': ventas,
        'total_ventas': total_ventas,
        'total_ganancia': total_ganancia,
    })


def venta_crear(request):
    productos = ProductoTienda.objects.filter(activo=True)
    precios_json = {str(p.pk): {'venta': float(p.precio_venta), 'compra': float(p.precio_compra), 'stock': float(p.stock_actual)} for p in productos}

    import json
    form = VentaProductoForm(request.POST or None)
    if form.is_valid():
        venta = form.save(commit=False)
        if venta.cantidad > venta.producto.stock_actual:
            messages.warning(request, f'Stock insuficiente. Solo hay {venta.producto.stock_actual} unidades.')
        else:
            venta.save()
            messages.success(request, f'Venta registrada. Ganancia: ${venta.ganancia:.2f}')
            return redirect('venta_lista')
    return render(request, 'tienda/venta_form.html', {
        'form': form,
        'titulo': 'Registrar Venta',
        'precios_json': json.dumps(precios_json),
        'productos': productos,
    })


def venta_eliminar(request, pk):
    obj = get_object_or_404(VentaProducto, pk=pk)
    if request.method == 'POST':
        obj.producto.stock_actual += obj.cantidad
        obj.producto.save(update_fields=['stock_actual'])
        obj.delete()
        messages.success(request, 'Venta eliminada y stock restituido.')
        return redirect('venta_lista')
    return render(request, 'tienda/confirmar_eliminar.html', {'obj': obj, 'tipo': 'venta'})


def precio_producto_api(request):
    pk = request.GET.get('pk')
    try:
        p = ProductoTienda.objects.get(pk=pk)
        return JsonResponse({'precio_venta': float(p.precio_venta), 'precio_compra': float(p.precio_compra), 'stock': float(p.stock_actual)})
    except ProductoTienda.DoesNotExist:
        return JsonResponse({'precio_venta': 0, 'precio_compra': 0, 'stock': 0})
