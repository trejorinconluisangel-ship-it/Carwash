import json

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time

from .models import (
    Recepcion, LUGAR_CHOICES, FORMA_PAGO_CHOICES, GASOLINA_CHOICES,
    ENTREGA_CHOICES, DIAGRAMA_TIPO_CHOICES, DIAGRAMAS_CONFIG,
)
from clientes.models import (
    Cliente, Vehiculo, COLOR_CHOICES, TIPO_VEHICULO_CHOICES,
    VISITAS_PREMIO_PEQUENO, VISITAS_PREMIO_GRANDE,
)
from servicios.models import TipoServicio, TipoVehiculo, PrecioPaquete, Servicio
from servicios.views import _mapear_tipo_vehiculo
from insumos.models import Insumo


def _entero_o_none(valor):
    valor = (valor or '').strip()
    if not valor.isdigit():
        return None
    return int(valor)


def recepcion_nueva(request):
    clientes = Cliente.objects.all().order_by('nombre')

    if request.method == 'POST':
        modo = request.POST.get('modo', 'espontaneo')

        placa = request.POST.get('placa', '').strip().upper()
        marca = request.POST.get('marca', '').strip()
        modelo = request.POST.get('modelo', '').strip()
        color = request.POST.get('color', '').strip()
        anio = _entero_o_none(request.POST.get('anio'))
        tipo_vehiculo_txt = request.POST.get('tipo_vehiculo_txt', '')
        telefono = request.POST.get('telefono', '').strip()

        cliente = None
        vehiculo = None
        cliente_nombre = ''

        if modo == 'registrado':
            cliente_id = request.POST.get('cliente_id')
            if not cliente_id:
                messages.error(request, 'Selecciona un cliente registrado.')
                return redirect('recepcion_nueva')
            cliente = get_object_or_404(Cliente, pk=cliente_id)
            cliente_nombre = cliente.nombre

            vehiculo_id = request.POST.get('vehiculo_id')
            if vehiculo_id:
                vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id, cliente=cliente)
                placa = placa or vehiculo.placa
                marca = marca or vehiculo.marca
                modelo = modelo or vehiculo.modelo
                color = color or vehiculo.color
                anio = anio or vehiculo.anio
                tipo_vehiculo_txt = tipo_vehiculo_txt or vehiculo.tipo
            elif placa or marca:
                vehiculo = Vehiculo.objects.create(
                    cliente=cliente, placa=placa or 'SIN PLACA', marca=marca,
                    modelo=modelo, anio=anio, color=color or 'otro',
                    tipo=tipo_vehiculo_txt or 'sedan',
                )

        elif modo == 'nuevo':
            nombre = request.POST.get('nombre', '').strip()
            if not nombre:
                messages.error(request, 'Escribe el nombre del cliente nuevo.')
                return redirect('recepcion_nueva')
            notas_cliente = request.POST.get('notas', '').strip()
            cliente = Cliente.objects.create(nombre=nombre, whatsapp=telefono, notas=notas_cliente)
            cliente_nombre = nombre
            if placa or marca:
                vehiculo = Vehiculo.objects.create(
                    cliente=cliente, placa=placa or 'SIN PLACA', marca=marca,
                    modelo=modelo, anio=anio, color=color or 'otro',
                    tipo=tipo_vehiculo_txt or 'sedan',
                )
            messages.success(request, f'Cliente "{nombre}" registrado.')

        else:
            cliente_nombre = request.POST.get('nombre', '').strip()

        tipo_servicio_id = request.POST.get('tipo_servicio_id')
        tipo_vehiculo_precio_id = request.POST.get('tipo_vehiculo_precio_id')
        es_cortesia = request.POST.get('es_cortesia') == 'on'
        precio_cobrado = '0' if es_cortesia else request.POST.get('precio_cobrado', '').strip()
        if not tipo_servicio_id or not tipo_vehiculo_precio_id or not precio_cobrado:
            messages.error(request, 'Elige el paquete, la categoría del vehículo y confirma el precio para poder cobrar.')
            return redirect('recepcion_nueva')
        tipo_servicio = get_object_or_404(TipoServicio, pk=tipo_servicio_id)
        tipo_vehiculo_precio = get_object_or_404(TipoVehiculo, pk=tipo_vehiculo_precio_id)
        insumos_usados_ids = request.POST.getlist('insumos_usados')

        try:
            diagrama_danos = json.loads(request.POST.get('diagrama_danos') or '{}')
        except (json.JSONDecodeError, TypeError):
            diagrama_danos = {}

        fecha = parse_date(request.POST.get('fecha', '')) or timezone.localdate()
        hora_recepcion = parse_time(request.POST.get('hora_recepcion', '')) or timezone.localtime().time()

        recepcion = Recepcion.objects.create(
            fecha=fecha,
            hora_recepcion=hora_recepcion,
            lugar=request.POST.get('lugar', 'negocio'),
            cliente=cliente,
            vehiculo=vehiculo,
            cliente_nombre=cliente_nombre,
            telefono=telefono,
            forma_pago=request.POST.get('forma_pago', ''),
            placa=placa,
            marca=marca,
            modelo=modelo,
            anio=anio,
            color=color,
            tipo_vehiculo_txt=tipo_vehiculo_txt,
            km=_entero_o_none(request.POST.get('km')),
            gasolina=request.POST.get('gasolina', ''),
            entrega=request.POST.get('entrega', 'recoge'),
            direccion_entrega=request.POST.get('direccion_entrega', '').strip(),
            diagrama_tipo=request.POST.get('diagrama_tipo', 'sedan'),
            diagrama_danos=diagrama_danos,
            retiro_valores=request.POST.get('retiro_valores') == 'on',
            obs_cliente=request.POST.get('obs_cliente', '').strip(),
            obs_colaborador=request.POST.get('obs_colaborador', '').strip(),
            firma_cliente=request.POST.get('firma_cliente', ''),
            firma_colaborador=request.POST.get('firma_colaborador', ''),
        )

        servicio = Servicio(
            fecha=fecha,
            hora=hora_recepcion,
            tipo_servicio=tipo_servicio,
            tipo_vehiculo=tipo_vehiculo_precio,
            cliente=cliente,
            vehiculo=vehiculo,
            precio_cobrado=precio_cobrado,
            es_cortesia=es_cortesia,
        )
        servicio._insumos_override = list(Insumo.objects.filter(pk__in=insumos_usados_ids))
        servicio.save()
        recepcion.servicio = servicio
        recepcion.save(update_fields=['servicio'])
        if es_cortesia:
            messages.success(request, 'Recepción registrada como cortesía — no se cobró.')
        else:
            messages.success(request, f'Recepción cobrada — ${servicio.precio_cobrado} registrados.')

        if cliente and float(servicio.precio_cobrado or 0) > 0:
            cliente.visitas_lealtad += 1
            cliente.save(update_fields=['visitas_lealtad'])
            if cliente.visitas_lealtad >= VISITAS_PREMIO_GRANDE:
                return redirect('premio_grande', pk=cliente.pk)
            elif cliente.visitas_lealtad == VISITAS_PREMIO_PEQUENO:
                return redirect('premio_pequeno', pk=cliente.pk)

        return redirect('recepcion_detalle', pk=recepcion.pk)

    tipos_servicio = TipoServicio.objects.filter(activo=True).order_by('orden')
    tipos_vehiculo_precio = TipoVehiculo.objects.filter(activo=True).order_by('orden')
    precios_data = {
        ts.pk: {tv.pk: 0 for tv in tipos_vehiculo_precio}
        for ts in tipos_servicio
    }
    for pp in PrecioPaquete.objects.filter(tipo_servicio__in=tipos_servicio, tipo_vehiculo__in=tipos_vehiculo_precio):
        precios_data[pp.tipo_servicio_id][pp.tipo_vehiculo_id] = float(pp.precio)

    tipo_map = {codigo: _mapear_tipo_vehiculo(codigo, tipos_vehiculo_precio) for codigo, _ in TIPO_VEHICULO_CHOICES}

    insumos_activos = Insumo.objects.all().order_by('nombre')
    insumos_por_paquete = {
        ts.pk: [i.pk for i in ts.insumos.all()] for ts in tipos_servicio
    }

    return render(request, 'recepcion/recepcion_form.html', {
        'clientes': clientes,
        'hoy': timezone.localdate().isoformat(),
        'hora_actual': timezone.localtime().strftime('%H:%M'),
        'lugar_choices': LUGAR_CHOICES,
        'forma_pago_choices': FORMA_PAGO_CHOICES,
        'gasolina_choices': GASOLINA_CHOICES,
        'entrega_choices': ENTREGA_CHOICES,
        'color_choices': COLOR_CHOICES,
        'tipo_vehiculo_choices': TIPO_VEHICULO_CHOICES,
        'diagrama_tipo_choices': DIAGRAMA_TIPO_CHOICES,
        'diagramas_config': DIAGRAMAS_CONFIG,
        'tipos_servicio': tipos_servicio,
        'tipos_vehiculo_precio': tipos_vehiculo_precio,
        'precios_json': json.dumps(precios_data),
        'tipo_map_json': json.dumps(tipo_map),
        'insumos_activos': insumos_activos,
        'insumos_por_paquete_json': json.dumps(insumos_por_paquete),
    })


def recepcion_lista(request):
    from django.db.models import Q

    q = request.GET.get('q', '').strip()
    fecha_desde = parse_date(request.GET.get('fecha_desde', '') or '')
    fecha_hasta = parse_date(request.GET.get('fecha_hasta', '') or '')
    solo_obs = request.GET.get('solo_obs') == '1'

    recepciones = Recepcion.objects.select_related('cliente', 'servicio', 'servicio__tipo_servicio').all()

    if q:
        recepciones = recepciones.filter(
            Q(cliente__nombre__icontains=q) | Q(cliente_nombre__icontains=q) |
            Q(placa__icontains=q) | Q(telefono__icontains=q) |
            Q(marca__icontains=q) | Q(modelo__icontains=q)
        )
    if fecha_desde:
        recepciones = recepciones.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        recepciones = recepciones.filter(fecha__lte=fecha_hasta)
    if solo_obs:
        recepciones = recepciones.exclude(obs_cliente='', obs_colaborador='')

    return render(request, 'recepcion/recepcion_lista.html', {
        'recepciones': recepciones,
        'q': q,
        'fecha_desde': request.GET.get('fecha_desde', ''),
        'fecha_hasta': request.GET.get('fecha_hasta', ''),
        'solo_obs': solo_obs,
    })


def recepcion_detalle(request, pk):
    recepcion = get_object_or_404(
        Recepcion.objects.select_related('cliente', 'vehiculo', 'servicio', 'servicio__tipo_servicio', 'servicio__tipo_vehiculo'),
        pk=pk,
    )
    return render(request, 'recepcion/recepcion_detalle.html', {
        'recepcion': recepcion,
        'diagramas': recepcion.diagramas_activos,
    })
