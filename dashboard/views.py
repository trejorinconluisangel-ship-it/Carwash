import json
from datetime import date, timedelta, datetime
from django.shortcuts import render
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
