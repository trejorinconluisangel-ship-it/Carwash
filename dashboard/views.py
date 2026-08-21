import json
import random
from datetime import date, timedelta, datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDay, ExtractHour
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

    servicios_qs  = Servicio.objects.filter(fecha__gte=inicio, fecha__lte=fin).exclude(es_cortesia=True)
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

    # ── Horario con más afluencia (con su propio selector de período) ──
    periodo_horario = request.GET.get('periodo_horario', periodo)
    inicio_horario, fin_horario = _rango_periodo(periodo_horario, fecha_ref)
    servicios_horario_qs = Servicio.objects.filter(fecha__gte=inicio_horario, fecha__lte=fin_horario)

    HORA_INICIO, HORA_FIN = 6, 21  # rango típico de operación (6:00–21:00)
    por_hora = (
        servicios_horario_qs
        .annotate(hora_num=ExtractHour('hora'))
        .values('hora_num')
        .annotate(count=Count('id'))
    )
    conteo_por_hora = {r['hora_num']: r['count'] for r in por_hora}
    labels_horario = [f'{h}:00' for h in range(HORA_INICIO, HORA_FIN + 1)]
    data_horario = [conteo_por_hora.get(h, 0) for h in range(HORA_INICIO, HORA_FIN + 1)]
    hora_pico = None
    if any(data_horario):
        idx_pico = data_horario.index(max(data_horario))
        hora_pico = labels_horario[idx_pico]

    # ── Retorno de clientes (programa de lealtad) ────────────
    from clientes.models import Cliente, VISITAS_PREMIO_PEQUENO, VISITAS_PREMIO_GRANDE
    clientes_activos = Cliente.objects.filter(visitas_lealtad__gte=1)
    total_clientes_activos = clientes_activos.count()
    bucket_1 = clientes_activos.filter(visitas_lealtad=1).count()
    bucket_2_4 = clientes_activos.filter(visitas_lealtad__gte=2, visitas_lealtad__lt=VISITAS_PREMIO_PEQUENO).count()
    bucket_5_9 = clientes_activos.filter(visitas_lealtad__gte=VISITAS_PREMIO_PEQUENO, visitas_lealtad__lt=VISITAS_PREMIO_GRANDE).count()
    bucket_10mas = clientes_activos.filter(visitas_lealtad__gte=VISITAS_PREMIO_GRANDE).count()
    labels_lealtad = ['1 visita (nuevos)', f'2-{VISITAS_PREMIO_PEQUENO - 1} visitas', f'{VISITAS_PREMIO_PEQUENO}-{VISITAS_PREMIO_GRANDE - 1} visitas', f'{VISITAS_PREMIO_GRANDE}+ visitas']
    data_lealtad = [bucket_1, bucket_2_4, bucket_5_9, bucket_10mas]
    pct_retorno = round((total_clientes_activos - bucket_1) / total_clientes_activos * 100, 1) if total_clientes_activos else 0

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
        'labels_horario': json.dumps(labels_horario),
        'data_horario': json.dumps(data_horario),
        'hora_pico': hora_pico,
        'periodo_horario': periodo_horario,
        'labels_lealtad': json.dumps(labels_lealtad),
        'data_lealtad': json.dumps(data_lealtad),
        'total_clientes_activos': total_clientes_activos,
        'pct_retorno': pct_retorno,
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
    from servicios.models import TipoServicio, TipoVehiculo, Servicio, PrecioPaquete
    from tienda.models import ProductoTienda, EntradaProducto, VentaProducto
    from clientes.models import Cliente, Vehiculo

    hoy = date.today()

    # ── Proveedores ─────────────────────────────────────────
    prov1, _ = Proveedor.objects.get_or_create(nombre='Químicos del Norte',
        defaults={'contacto': 'Ramón Soto', 'telefono': '4421234567', 'email': 'ventas@quimicosnorte.mx'})
    prov2, _ = Proveedor.objects.get_or_create(nombre='Distribuidora Clean Pro',
        defaults={'contacto': 'Lucía Mendoza', 'telefono': '4429876543'})

    # ── Insumos (costo estimado por servicio, sin necesidad de historial de rendimiento) ──
    shampoo, _ = Insumo.objects.get_or_create(nombre='Shampoo Concentrado (demo)',
        defaults={'categoria': 'shampoo', 'unidad_medida': 'litro', 'costo_estimado_servicio': 8.00,
                  'envases_en_bodega': 4, 'envases_stock_minimo': 1, 'proveedor': prov1})
    cera, _ = Insumo.objects.get_or_create(nombre='Cera Líquida Brillante (demo)',
        defaults={'categoria': 'cera', 'unidad_medida': 'litro', 'costo_estimado_servicio': 15.00,
                  'envases_en_bodega': 2, 'envases_stock_minimo': 1, 'proveedor': prov1})
    desengrasante, _ = Insumo.objects.get_or_create(nombre='Desengrasante Motor (demo)',
        defaults={'categoria': 'desengrasante', 'unidad_medida': 'litro', 'costo_estimado_servicio': 12.00,
                  'envases_en_bodega': 2, 'envases_stock_minimo': 1, 'proveedor': prov2})
    aromatizante, _ = Insumo.objects.get_or_create(nombre='Aromatizante Cabina (demo)',
        defaults={'categoria': 'aromatizante', 'unidad_medida': 'pieza', 'costo_estimado_servicio': 5.00,
                  'envases_en_bodega': 8, 'envases_stock_minimo': 2, 'proveedor': prov2})
    microfibra, _ = Insumo.objects.get_or_create(nombre='Microfibra Detallado (demo)',
        defaults={'categoria': 'microfibra', 'unidad_medida': 'pieza', 'costo_estimado_servicio': 3.00,
                  'envases_en_bodega': 5, 'envases_stock_minimo': 2, 'proveedor': prov2})

    # ── Tipos de Servicio (paquetes de demo, inactivos para no mezclarse con los reales) ──
    express, _ = TipoServicio.objects.get_or_create(nombre='Express Exterior (demo)',
        defaults={'descripcion': 'Lavado rápido solo exterior', 'activo': False})
    completo, _ = TipoServicio.objects.get_or_create(nombre='Lavado Completo (demo)',
        defaults={'descripcion': 'Interior y exterior con aspirado', 'activo': False})
    motor_ts, _ = TipoServicio.objects.get_or_create(nombre='Detallado de Motor (demo)',
        defaults={'descripcion': 'Limpieza profunda de motor', 'activo': False})
    vestiduras, _ = TipoServicio.objects.get_or_create(nombre='Lavado de Vestiduras (demo)',
        defaults={'descripcion': 'Limpieza de asientos y tapetes', 'activo': False})

    # ── Tipos de Vehículo (demo, inactivos) ───────────────────
    moto, _ = TipoVehiculo.objects.get_or_create(nombre='Moto (demo)', defaults={'activo': False})
    auto, _ = TipoVehiculo.objects.get_or_create(nombre='Auto Pequeño (demo)', defaults={'activo': False})
    pickup, _ = TipoVehiculo.objects.get_or_create(nombre='Pick Up (demo)', defaults={'activo': False})
    camioneta, _ = TipoVehiculo.objects.get_or_create(nombre='Camioneta Grande (demo)', defaults={'activo': False})
    van, _ = TipoVehiculo.objects.get_or_create(nombre='Van / Combi (demo)', defaults={'activo': False})

    # ── Precios de demo (para que el dashboard tenga ganancias que graficar) ──
    precios_demo = {
        (express, auto): 80, (express, moto): 60, (express, pickup): 100,
        (express, camioneta): 110, (completo, auto): 150, (completo, pickup): 180,
        (completo, camioneta): 200, (motor_ts, pickup): 220, (motor_ts, camioneta): 240,
        (vestiduras, auto): 250, (vestiduras, camioneta): 300,
    }
    for (ts, tv), precio in precios_demo.items():
        PrecioPaquete.objects.get_or_create(tipo_servicio=ts, tipo_vehiculo=tv, defaults={'precio': precio})

    # ── Productos que usa cada paquete ────────────────────────
    express.insumos.add(shampoo, aromatizante)
    completo.insumos.add(shampoo, cera, aromatizante)
    motor_ts.insumos.add(desengrasante)
    vestiduras.insumos.add(microfibra, aromatizante)

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
        (0, express, auto), (0, completo, camioneta), (1, express, pickup),
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
        precio = precios_demo.get((tipo_s, tipo_v), 100)
        Servicio.objects.get_or_create(
            fecha=fecha_s, tipo_servicio=tipo_s, tipo_vehiculo=tipo_v, precio_cobrado=precio,
            defaults={'notas': 'Dato de prueba'}
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
    from servicios.models import TipoServicio, TipoVehiculo, Servicio
    from tienda.models import ProductoTienda, EntradaProducto, VentaProducto
    from clientes.models import Cliente, Vehiculo

    Servicio.objects.all().delete()
    VentaProducto.objects.all().delete()
    EntradaProducto.objects.all().delete()
    Compra.objects.all().delete()
    Vehiculo.objects.all().delete()
    Cliente.objects.all().delete()
    Insumo.objects.all().delete()
    ProductoTienda.objects.all().delete()
    TipoServicio.objects.all().delete()
    TipoVehiculo.objects.all().delete()
    Proveedor.objects.all().delete()

    messages.success(request, '🗑️ Todos los datos fueron eliminados. El sistema está listo para usar.')
    return redirect('dashboard')
