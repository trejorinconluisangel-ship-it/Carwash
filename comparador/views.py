import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Min, Q
from .models import Categoria, Producto, PrecioProveedor
from .forms import CategoriaForm, ProductoForm, PrecioProveedorForm
from insumos.models import Proveedor, Insumo


def _insumos_json():
    """Datos de insumos para auto-completar en el formulario."""
    return json.dumps(
        {
            str(i.pk): {
                'nombre': i.nombre,
                'unidad': i.unidad_medida,
                'descripcion': i.descripcion,
            }
            for i in Insumo.objects.all()
        },
        ensure_ascii=False,
    )


def comparador_lista(request):
    q = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')
    proveedor_id = request.GET.get('proveedor', '')

    productos = Producto.objects.prefetch_related(
        'precios__proveedor', 'categoria', 'insumo'
    ).annotate(precio_min=Min('precios__precio'))

    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | Q(descripcion__icontains=q)
            | Q(insumo__nombre__icontains=q)
        )
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    if proveedor_id:
        productos = productos.filter(precios__proveedor_id=proveedor_id)

    categorias = Categoria.objects.all()
    proveedores = Proveedor.objects.all()

    return render(request, 'comparador/comparador_lista.html', {
        'productos': productos,
        'categorias': categorias,
        'proveedores': proveedores,
        'q': q,
        'categoria_id': categoria_id,
        'proveedor_id': proveedor_id,
        'total': productos.count(),
    })


def producto_detalle(request, pk):
    producto = get_object_or_404(Producto.objects.select_related('insumo', 'categoria'), pk=pk)
    precios = producto.precios.select_related('proveedor').order_by('precio')
    return render(request, 'comparador/producto_detalle.html', {
        'producto': producto,
        'precios': precios,
    })


def producto_crear(request):
    insumo_pk = request.GET.get('insumo')
    initial = {}
    if insumo_pk:
        initial['insumo'] = insumo_pk

    form = ProductoForm(request.POST or None, initial=initial)
    if form.is_valid():
        p = form.save()
        messages.success(request, f'"{p.nombre_display}" agregado al comparador.')
        return redirect('precio_crear_comparador', producto_pk=p.pk)

    return render(request, 'comparador/producto_form.html', {
        'form': form,
        'titulo': 'Nuevo Producto',
        'insumos_json': _insumos_json(),
        'insumo_preselect': insumo_pk,
    })


def producto_editar(request, pk):
    obj = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Producto actualizado.')
        return redirect('producto_detalle_comparador', pk=obj.pk)

    return render(request, 'comparador/producto_form.html', {
        'form': form,
        'titulo': 'Editar Producto',
        'obj': obj,
        'insumos_json': _insumos_json(),
    })


def producto_eliminar(request, pk):
    obj = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        nombre = obj.nombre_display
        obj.delete()
        messages.success(request, f'"{nombre}" eliminado.')
        return redirect('comparador_lista')
    return render(request, 'comparador/confirmar_eliminar.html', {'obj': obj, 'tipo': 'producto'})


def precio_crear(request, producto_pk):
    producto = get_object_or_404(Producto.objects.select_related('insumo'), pk=producto_pk)
    form = PrecioProveedorForm(request.POST or None)
    if form.is_valid():
        precio = form.save(commit=False)
        precio.producto = producto
        precio.save()
        messages.success(request, f'Precio de {precio.proveedor} registrado.')
        return redirect('producto_detalle_comparador', pk=producto.pk)
    return render(request, 'comparador/precio_form.html', {
        'form': form, 'producto': producto, 'titulo': 'Agregar Precio'
    })


def precio_editar(request, pk):
    obj = get_object_or_404(PrecioProveedor.objects.select_related('producto__insumo'), pk=pk)
    form = PrecioProveedorForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Precio actualizado.')
        return redirect('producto_detalle_comparador', pk=obj.producto.pk)
    return render(request, 'comparador/precio_form.html', {
        'form': form, 'producto': obj.producto, 'titulo': 'Editar Precio', 'obj': obj
    })


def precio_eliminar(request, pk):
    obj = get_object_or_404(PrecioProveedor, pk=pk)
    producto_pk = obj.producto.pk
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Precio eliminado.')
        return redirect('producto_detalle_comparador', pk=producto_pk)
    return render(request, 'comparador/confirmar_eliminar.html', {'obj': obj, 'tipo': 'precio'})


def categoria_lista(request):
    form = CategoriaForm(request.POST or None)
    if form.is_valid():
        c = form.save()
        messages.success(request, f'Categoría "{c.nombre}" creada.')
        return redirect('categoria_lista_comparador')
    categorias = Categoria.objects.prefetch_related('productos').all()
    return render(request, 'comparador/categoria_lista.html', {
        'categorias': categorias, 'form': form
    })


def categoria_eliminar(request, pk):
    obj = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Categoría eliminada.')
    return redirect('categoria_lista_comparador')
