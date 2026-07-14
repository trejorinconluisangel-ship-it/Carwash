import json
import random
from datetime import date, timedelta, datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDay
from django.utils import timezone


def _rango_periodo(periodo, fecha_ref=None):
    hoy = fecha_ref or date.today()
    if periodo == 'dia':
        return hoy, hoy
    elif periodo == 'semana':
        inicio = hoy - timedelta(days=hoy.weekday())
        return inicio, inicio + timedelta(days=6)
    elif periodo == 'mes':
        inicio = hoy.replace(day=1)
        if hoy.month == 12:
            fin = hoy.replace(year=hoy.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            fin = hoy.replace(month=hoy.month + 1, day=1) - timedelta(days=1)
        return inicio, fin
    elif periodo == 'semestre':
        if hoy.month <= 6:
            return hoy.replace(month=1, day=1), hoy.replace(month=6, day=30)
        else:
            return hoy.replace(month=7, day=1), hoy.replace(month=12, day=31)
    elif periodo == 'anio':
        return hoy.replace(month=1, day=1), hoy.replace(month=12, day=31)
    return hoy, hoy


def dashboard(request):
    from servicios.models import Servicio
    from insumos.models import Insumo, Compra
    from tienda.models import VentaProducto, ProductoTienda, EntradaProducto

    periodo = request.GET.get('periodo', 'mes')
    fecha_sel = request.GET.get('fecha', str(date.today()))
    try:
        fecha_ref = datetime.strptime(fecha_sel, '%Y-%m-%d').date()
    except ValueError:
        fecha_ref = date.today()

    inicio, fin = _rango_periodo(periodo, fecha_ref)

    servicios_qs  = Servicio.objects.filter(fecha__gte=inicio, fecha__lte=fin)
    compras_qs    = Compra.objects.filter(fecha__gte=inicio, fecha__lte=fin)
    ventas_ts_qs  = VentaProducto.objects.filter(fecha__gte=inicio, fecha__lte=fin)
    entradas_ts_qs= EntradaProducto.objects.filter(fecha__gte=inicio, fecha__lte=fin)

    # ── KPIs Servicios ──────────────────────────────────────
    total_ingresos_serv = servicios_qs.aggregate(t=Sum('precio_cobrado'))['t'] or 0
    total_servicios     = servicios_qs.count()
    ticket_promedio     = round(float(total_ingresos_serv) / total_servicios, 2) if total_servicios else 0
    total_costo_insumos = servicios_qs.aggregate(t=Sum('costo_insumos'))['t'] or 0
    ganancia_servicios  = float(total_ingresos_serv) - float(total_costo_insumos)

    # ── KPIs Tienda ─────────────────────────────────────────
    total_ingresos_tienda = ventas_ts_qs.aggregate(t=Sum('total_venta'))['t'] or 0
    total_ganancia_tienda = ventas_ts_qs.aggregate(t=Sum('ganancia'))['t'] or 0
    total_gasto_tienda    = entradas_ts_qs.aggregate(t=Sum('costo_total'))['t'] or 0
    total_ventas_tienda   = ventas_ts_qs.count()

    # ── KPIs Compras insumos ────────────────────────────────
    total_gastos_insumos = compras_qs.aggregate(t=Sum('costo_total'))['t'] or 0

    # ── Totales combinados ──────────────────────────────────
    ingresos_totales = float(total_ingresos_serv) + float(total_ingresos_tienda)
    ganancia_total   = ganancia_servicios + float(total_ganancia_tienda)

    # ── Gráfica de línea: ingresos por día (servicios + tienda) ──
    serv_dia = (
        servicios_qs
        .annotate(dia=TruncDay('fecha'))
        .values('dia')
        .annotate(total=Sum('precio_cobrado'), count=Count('id'), costo=Sum('costo_insumos'))
        .order_by('dia')
    )
    serv_dia_map = {str(r['dia'])[:10]: r for r in serv_dia}

    tienda_dia = (
        ventas_ts_qs
        .annotate(dia=TruncDay('fecha'))
        .values('dia')
        .annotate(total=Sum('total_venta'), gan=Sum('ganancia'))
        .order_by('dia')
    )
    tienda_dia_map = {str(r['dia'])[:10]: r for r in tienda_dia}

    all_dias = sorted(set(list(serv_dia_map.keys()) + list(tienda_dia_map.keys())))
    labels_dia         = all_dias
    data_ingresos_serv = [float(serv_dia_map.get(d, {}).get('total', 0) or 0) for d in all_dias]
    data_ingresos_tienda = [float(tienda_dia_map.get(d, {}).get('total', 0) or 0) for d in all_dias]
    data_ganancia_dia  = [
        float(serv_dia_map.get(d, {}).get('total', 0) or 0) - float(serv_dia_map.get(d, {}).get('costo', 0) or 0)
        + float(tienda_dia_map.get(d, {}).get('gan', 0) or 0)
        for d in all_dias
    ]
    data_conteo = [int(serv_dia_map.get(d, {}).get('count', 0) or 0) for d in all_dias]

    # ── Por tipo de servicio ────────────────────────────────
    por_tipo = (
        servicios_qs
        .values('tipo_servicio__nombre')
        .annotate(total=Sum('precio_cobrado'), count=Count('id'))
        .order_by('-total')
    )
    labels_tipo        = [r['tipo_servicio__nombre'] or 'Sin tipo' for r in por_tipo]
    data_tipo_ingresos = [float(r['total']) for r in por_tipo]
    data_tipo_count    = [r['count'] for r in por_tipo]

    # ── Por tipo de vehículo ────────────────────────────────
    por_vehiculo = (
        servicios_qs
        .values('tipo_vehiculo__nombre')
        .annotate(total=Sum('precio_cobrado'), count=Count('id'))
        .order_by('-count')
    )
    labels_vehiculo         = [r['tipo_vehiculo__nombre'] or 'Sin tipo' for r in por_vehiculo]
    data_vehiculo_count     = [r['count'] for r in por_vehiculo]
    data_vehiculo_ingresos  = [float(r['total']) for r in por_vehiculo]

    # ── Top productos tienda ────────────────────────────────
    top_productos = (
        ventas_ts_qs
        .values('producto__nombre')
        .annotate(total=Sum('total_venta'), gan=Sum('ganancia'), cnt=Count('id'))
        .order_by('-total')[:6]
    )
    labels_productos  = [r['producto__nombre'] for r in top_productos]
    data_prod_ingresos= [float(r['total']) for r in top_productos]
    data_prod_ganancia= [float(r['gan']) for r in top_productos]

    # ── Alertas ─────────────────────────────────────────────
    insumos_alerta   = [i for i in Insumo.objects.all() if i.stock_bajo]
    productos_alerta = [p for p in ProductoTienda.objects.filter(activo=True) if p.stock_bajo]

    ultimos_servicios = Servicio.objects.select_related('tipo_servicio', 'tipo_vehiculo').all()[:5]

    periodo_opciones = {'dia': 'Día', 'semana': 'Semana', 'mes': 'Mes', 'semestre': 'Semestre', 'anio': 'Año'}

    context = {
        'periodo': periodo,
        'fecha_sel': fecha_sel,
        'periodo_opciones': periodo_opciones,
        'inicio': inicio,
        'fin': fin,
        # KPIs servicios
        'total_ingresos_serv': total_ingresos_serv,
        'total_servicios': total_servicios,
        'ticket_promedio': ticket_promedio,
        'total_costo_insumos': total_costo_insumos,
        'ganancia_servicios': ganancia_servicios,
        # KPIs tienda
        'total_ingresos_tienda': total_ingresos_tienda,
        'total_ganancia_tienda': total_ganancia_tienda,
        'total_ventas_tienda': total_ventas_tienda,
        # Totales combinados
        'ingresos_totales': ingresos_totales,
        'ganancia_total': ganancia_total,
        # Charts
        'labels_dia': json.dumps(labels_dia),
        'data_ingresos_serv': json.dumps(data_ingresos_serv),
        'data_ingresos_tienda': json.dumps(data_ingresos_tienda),
        'data_ganancia_dia': json.dumps(data_ganancia_dia),
        'data_conteo': json.dumps(data_conteo),
        'labels_tipo': json.dumps(labels_tipo),
        'data_tipo_ingresos': json.dumps(data_tipo_ingresos),
        'data_tipo_count': json.dumps(data_tipo_count),
        'labels_vehiculo': json.dumps(labels_vehiculo),
        'data_vehiculo_count': json.dumps(data_vehiculo_count),
        'data_vehiculo_ingresos': json.dumps(data_vehiculo_ingresos),
        'labels_productos': json.dumps(labels_productos),
        'data_prod_ingresos': json.dumps(data_prod_ingresos),
        'data_prod_ganancia': json.dumps(data_prod_ganancia),
        # Alertas
        'insumos_alerta': insumos_alerta,
        'productos_alerta': productos_alerta,
        'ultimos_servicios': ultimos_servicios,
        'hoy': date.today(),
    }
    return render(request, 'dashboard/dashboard.html', context)


def cargar_datos_prueba(request):
    if request.method != 'POST':
        return render(request, 'dashboard/datos_prueba_confirm.html', {'accion': 'cargar'})

    from insumos.models import Proveedor, Insumo, Compra
    from servicios.models import TipoServicio, TipoVehiculo, InsumoEnServicio, Servicio
    from tienda.models import ProductoTienda, EntradaProducto, VentaProducto
    from clientes.models import Cliente, Vehiculo

    hoy = date.today()

    # ── Proveedores ─────────────────────────────────────────
    prov1, _ = Proveedor.objects.get_or_create(nombre='Químicos del Norte',
        defaults={'contacto': 'Ramón Soto', 'telefono': '4421234567', 'email': 'ventas@quimicosnorte.mx'})
    prov2, _ = Proveedor.objects.get_or_create(nombre='Distribuidora Clean Pro',
        defaults={'contacto': 'Lucía Mendoza', 'telefono': '4429876543'})

    # ── Insumos ──────────────────────────────────────────────
    shampoo, _ = Insumo.objects.get_or_create(nombre='Shampoo Concentrado',
        defaults={'categoria': 'limpieza', 'unidad_medida': 'L', 'costo_unitario': 45.00,
                  'stock_actual': 12, 'stock_minimo': 3, 'proveedor': prov1})
    cera, _ = Insumo.objects.get_or_create(nombre='Cera Líquida Brillante',
        defaults={'categoria': 'acabado', 'unidad_medida': 'L', 'costo_unitario': 90.00,
                  'stock_actual': 6, 'stock_minimo': 2, 'proveedor': prov1})
    desengrasante, _ = Insumo.objects.get_or_create(nombre='Desengrasante Motor',
        defaults={'categoria': 'limpieza', 'unidad_medida': 'L', 'costo_unitario': 60.00,
                  'stock_actual': 4, 'stock_minimo': 2, 'proveedor': prov2})
    aromatizante, _ = Insumo.objects.get_or_create(nombre='Aromatizante Cabina',
        defaults={'categoria': 'acabado', 'unidad_medida': 'pz', 'costo_unitario': 15.00,
                  'stock_actual': 20, 'stock_minimo': 5, 'proveedor': prov2})
    microfibra, _ = Insumo.objects.get_or_create(nombre='Microfibra Detallado',
        defaults={'categoria': 'herramienta', 'unidad_medida': 'pz', 'costo_unitario': 25.00,
                  'stock_actual': 8, 'stock_minimo': 3, 'proveedor': prov2})

    # ── Tipos de Servicio ────────────────────────────────────
    express, _ = TipoServicio.objects.get_or_create(nombre='Express Exterior',
        defaults={'precio_base': 80.00, 'descripcion': 'Lavado rápido solo exterior'})
    completo, _ = TipoServicio.objects.get_or_create(nombre='Lavado Completo',
        defaults={'precio_base': 150.00, 'descripcion': 'Interior y exterior con aspirado'})
    motor_ts, _ = TipoServicio.objects.get_or_create(nombre='Detallado de Motor',
        defaults={'precio_base': 200.00, 'descripcion': 'Limpieza profunda de motor'})
    vestiduras, _ = TipoServicio.objects.get_or_create(nombre='Lavado de Vestiduras',
        defaults={'precio_base': 300.00, 'descripcion': 'Limpieza de asientos y tapetes'})

    # ── Tipos de Vehículo ────────────────────────────────────
    moto, _ = TipoVehiculo.objects.get_or_create(nombre='Moto',
        defaults={'multiplicador_precio': 0.70})
    auto, _ = TipoVehiculo.objects.get_or_create(nombre='Auto Pequeño',
        defaults={'multiplicador_precio': 1.00})
    pickup, _ = TipoVehiculo.objects.get_or_create(nombre='Pick Up',
        defaults={'multiplicador_precio': 1.30})
    camioneta, _ = TipoVehiculo.objects.get_or_create(nombre='Camioneta Grande',
        defaults={'multiplicador_precio': 1.50})
    van, _ = TipoVehiculo.objects.get_or_create(nombre='Van / Combi',
        defaults={'multiplicador_precio': 1.60})

    # ── Insumos por Servicio ─────────────────────────────────
    InsumoEnServicio.objects.get_or_create(tipo_servicio=express, insumo=shampoo,
        defaults={'cantidad_por_servicio': 0.10})
    InsumoEnServicio.objects.get_or_create(tipo_servicio=express, insumo=aromatizante,
        defaults={'cantidad_por_servicio': 1})
    InsumoEnServicio.objects.get_or_create(tipo_servicio=completo, insumo=shampoo,
        defaults={'cantidad_por_servicio': 0.20})
    InsumoEnServicio.objects.get_or_create(tipo_servicio=completo, insumo=cera,
        defaults={'cantidad_por_servicio': 0.10})
    InsumoEnServicio.objects.get_or_create(tipo_servicio=completo, insumo=aromatizante,
        defaults={'cantidad_por_servicio': 1})
    InsumoEnServicio.objects.get_or_create(tipo_servicio=motor_ts, insumo=desengrasante,
        defaults={'cantidad_por_servicio': 0.30})
    InsumoEnServicio.objects.get_or_create(tipo_servicio=vestiduras, insumo=microfibra,
        defaults={'cantidad_por_servicio': 2})
    InsumoEnServicio.objects.get_or_create(tipo_servicio=vestiduras, insumo=aromatizante,
        defaults={'cantidad_por_servicio': 1})

    # ── Clientes y Vehículos ─────────────────────────────────
    c1, _ = Cliente.objects.get_or_create(nombre='Carlos Ramírez',
        defaults={'whatsapp': '4421112233', 'notas': 'Cliente frecuente'})
    Vehiculo.objects.get_or_create(cliente=c1, placa='QRO-123-A',
        defaults={'marca': 'Nissan', 'modelo': 'Sentra', 'anio': 2020, 'color': 'blanco', 'tipo': 'auto_pequeño'})

    c2, _ = Cliente.objects.get_or_create(nombre='Laura Domínguez',
        defaults={'whatsapp': '4424445566'})
    Vehiculo.objects.get_or_create(cliente=c2, placa='QRO-456-B',
        defaults={'marca': 'Toyota', 'modelo': 'Hilux', 'anio': 2021, 'color': 'gris', 'tipo': 'pick_up'})

    c3, _ = Cliente.objects.get_or_create(nombre='Pedro Vargas',
        defaults={'whatsapp': '4427778899'})
    Vehiculo.objects.get_or_create(cliente=c3, placa='QRO-789-C',
        defaults={'marca': 'Honda', 'modelo': 'CB500', 'anio': 2019, 'color': 'rojo', 'tipo': 'moto'})

    # ── Servicios de los últimos 30 días ─────────────────────
    servicios_data = [
        (2, express, auto), (3, completo, auto), (5, express, pickup),
        (5, motor_ts, pickup), (7, express, auto), (8, completo, camioneta),
        (10, express, moto), (10, express, auto), (12, vestiduras, auto),
        (13, completo, pickup), (15, express, auto), (17, express, camioneta),
        (18, completo, auto), (20, express, moto), (21, motor_ts, camioneta),
        (22, express, auto), (24, completo, pickup), (25, express, auto),
        (27, vestiduras, camioneta), (28, express, auto),
    ]
    for dias_atras, tipo_s, tipo_v in servicios_data:
        fecha_s = hoy - timedelta(days=dias_atras)
        precio = round(float(tipo_s.precio_base) * float(tipo_v.multiplicador_precio), 2)
        costo = sum(
            float(rel.cantidad_por_servicio) * float(rel.insumo.costo_unitario)
            for rel in InsumoEnServicio.objects.filter(tipo_servicio=tipo_s).select_related('insumo')
        )
        Servicio.objects.get_or_create(
            fecha=fecha_s, tipo_servicio=tipo_s, tipo_vehiculo=tipo_v, precio_cobrado=precio,
            defaults={'costo_insumos': round(costo, 2), 'notas': 'Dato de prueba'}
        )

    # ── Productos Tienda ─────────────────────────────────────
    arom, _ = ProductoTienda.objects.get_or_create(nombre='Aromatizante Pino',
        defaults={'categoria': 'aromatizante', 'precio_compra': 18.00, 'precio_venta': 35.00,
                  'stock_actual': 15, 'stock_minimo': 5, 'unidad': 'pz'})
    micfib, _ = ProductoTienda.objects.get_or_create(nombre='Microfibra Premium',
        defaults={'categoria': 'accesorio', 'precio_compra': 30.00, 'precio_venta': 60.00,
                  'stock_actual': 10, 'stock_minimo': 3, 'unidad': 'pz'})
    kit, _ = ProductoTienda.objects.get_or_create(nombre='Kit Limpieza Dashboard',
        defaults={'categoria': 'accesorio', 'precio_compra': 55.00, 'precio_venta': 99.00,
                  'stock_actual': 5, 'stock_minimo': 2, 'unidad': 'pz'})

    # ── Ventas Tienda ────────────────────────────────────────
    ventas_data = [
        (3, arom, 2), (7, micfib, 1), (12, arom, 1), (15, kit, 1),
        (18, arom, 3), (22, micfib, 2), (26, kit, 1),
    ]
    for dias_atras, prod, cant in ventas_data:
        fecha_v = hoy - timedelta(days=dias_atras)
        gan = round((float(prod.precio_venta) - float(prod.precio_compra)) * cant, 2)
        VentaProducto.objects.get_or_create(
            fecha=fecha_v, producto=prod, cantidad=cant,
            defaults={'precio_unitario': prod.precio_venta,
                      'total_venta': round(float(prod.precio_venta) * cant, 2),
                      'ganancia': gan, 'notas': 'Dato de prueba'}
        )

    messages.success(request, '✅ Datos de prueba cargados correctamente. ¡Explora el sistema!')
    return redirect('dashboard')


def limpiar_todos_datos(request):
    if request.method != 'POST':
        from servicios.models import Servicio
        from insumos.models import Insumo
        from clientes.models import Cliente
        from tienda.models import ProductoTienda
        ctx = {
            'accion': 'limpiar',
            'n_servicios': Servicio.objects.count(),
            'n_clientes': Cliente.objects.count(),
            'n_insumos': Insumo.objects.count(),
            'n_productos': ProductoTienda.objects.count(),
        }
        return render(request, 'dashboard/datos_prueba_confirm.html', ctx)

    from insumos.models import Proveedor, Insumo, Compra
    from servicios.models import TipoServicio, TipoVehiculo, InsumoEnServicio, Servicio
    from tienda.models import ProductoTienda, EntradaProducto, VentaProducto
    from clientes.models import Cliente, Vehiculo

    Servicio.objects.all().delete()
    VentaProducto.objects.all().delete()
    EntradaProducto.objects.all().delete()
    Compra.objects.all().delete()
    InsumoEnServicio.objects.all().delete()
    Vehiculo.objects.all().delete()
    Cliente.objects.all().delete()
    Insumo.objects.all().delete()
    ProductoTienda.objects.all().delete()
    TipoServicio.objects.all().delete()
    TipoVehiculo.objects.all().delete()
    Proveedor.objects.all().delete()

    messages.success(request, '🗑️ Todos los datos fueron eliminados. El sistema está listo para usar.')
    return redirect('dashboard')
