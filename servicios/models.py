from django.db import models
from django.utils import timezone

NEGOCIO_NOMBRE = 'NEOWASH AUTO-WASH'
NEGOCIO_DIRECCION = 'Calle Belisario Domínguez #247, La Bola, Ezequiel Montes, Qro.'
NEGOCIO_WHATSAPP_1 = '56 2375 9152'
NEGOCIO_WHATSAPP_2 = '441 122 6818'
NEGOCIO_FACEBOOK = 'Neowash'


TIPO_SERVICIO_CHOICES = [
    ('express_ext', 'Lavado Express Exterior'),
    ('express_int', 'Lavado Express Interior'),
    ('completo', 'Lavado Completo'),
    ('motor', 'Detallado de Motor'),
    ('vestiduras', 'Lavado de Vestiduras'),
    ('encerado', 'Encerado / Pulido'),
    ('premium', 'Servicio Premium Full'),
]

TIPO_VEHICULO_CHOICES = [
    ('moto', 'Moto'),
    ('auto_chico', 'Auto Pequeño'),
    ('sedan', 'Sedán / Auto Mediano'),
    ('pickup', 'Pick Up'),
    ('camioneta', 'Camioneta / SUV'),
    ('van', 'Van / Minivan'),
    ('camion', 'Camión'),
]


class TipoServicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    orden = models.PositiveSmallIntegerField(default=0, help_text='Orden en que se muestra (Paquete 1, 2...)')
    activo = models.BooleanField(default=True)
    insumos = models.ManyToManyField('insumos.Insumo', related_name='tipos_servicio', blank=True,
                                     help_text='Productos que se usan en este paquete')

    class Meta:
        verbose_name = 'Tipo de Servicio'
        verbose_name_plural = 'Tipos de Servicio'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre

    @property
    def costo_estimado_total(self):
        return round(sum(i.costo_por_servicio for i in self.insumos.all()), 2)


class TipoVehiculo(models.Model):
    nombre = models.CharField(max_length=80)
    orden = models.PositiveSmallIntegerField(default=0, help_text='Orden en que se muestra (chico a grande)')
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tipo de Vehículo'
        verbose_name_plural = 'Tipos de Vehículo'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class PrecioPaquete(models.Model):
    """Precio fijo de un paquete (TipoServicio) para una categoría de vehículo (TipoVehiculo)."""
    tipo_servicio = models.ForeignKey(TipoServicio, on_delete=models.CASCADE, related_name='precios')
    tipo_vehiculo = models.ForeignKey(TipoVehiculo, on_delete=models.CASCADE, related_name='precios')
    precio = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Precio de Paquete'
        verbose_name_plural = 'Precios de Paquetes'
        unique_together = ('tipo_servicio', 'tipo_vehiculo')
        ordering = ['tipo_servicio', 'tipo_vehiculo']

    def __str__(self):
        return f'{self.tipo_servicio} × {self.tipo_vehiculo} = ${self.precio}'


class Servicio(models.Model):
    fecha = models.DateField(default=timezone.now)
    hora = models.TimeField(default=timezone.now)
    tipo_servicio = models.ForeignKey(TipoServicio, on_delete=models.PROTECT, related_name='servicios')
    tipo_vehiculo = models.ForeignKey(TipoVehiculo, on_delete=models.PROTECT, related_name='servicios')
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='servicios')
    vehiculo = models.ForeignKey('clientes.Vehiculo', on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='servicios')
    precio_cobrado = models.DecimalField(max_digits=8, decimal_places=2)
    costo_insumos = models.DecimalField(max_digits=8, decimal_places=2, default=0,
                                        help_text='Costo estimado de insumos usados en este servicio')
    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['-fecha', '-hora']

    def __str__(self):
        return f'{self.tipo_servicio} — {self.tipo_vehiculo} — {self.fecha}'

    @property
    def ganancia(self):
        return float(self.precio_cobrado) - float(self.costo_insumos)

    @property
    def nombre_cliente_display(self):
        if self.cliente:
            return self.cliente.nombre
        if hasattr(self, 'recepcion') and self.recepcion.cliente_nombre:
            return self.recepcion.cliente_nombre
        return 'Cliente'

    @property
    def telefono_contacto(self):
        if hasattr(self, 'recepcion') and self.recepcion.telefono:
            return self.recepcion.telefono
        if self.cliente and self.cliente.whatsapp:
            return self.cliente.whatsapp
        return ''

    @property
    def vehiculo_descripcion_ticket(self):
        if self.vehiculo:
            partes = [p for p in [self.vehiculo.marca, self.vehiculo.modelo] if p]
            desc = ' '.join(partes)
            if self.vehiculo.placa:
                desc += f' ({self.vehiculo.placa})'
            return desc.strip() or '—'
        if hasattr(self, 'recepcion'):
            r = self.recepcion
            partes = [p for p in [r.marca, r.modelo] if p]
            desc = ' '.join(partes)
            if r.placa:
                desc += f' ({r.placa})'
            return desc.strip() or '—'
        return '—'

    @property
    def whatsapp_ticket_url(self):
        tel = self.telefono_contacto
        if not tel:
            return ''
        from urllib.parse import quote
        numero = ''.join(filter(str.isdigit, tel))
        if len(numero) == 10:
            numero = '52' + numero
        primer_nombre = self.nombre_cliente_display.split()[0] if self.nombre_cliente_display else ''
        descripcion = f'\n{self.tipo_servicio.descripcion}\n' if self.tipo_servicio.descripcion else ''
        mensaje = (
            f'🚗💦 *{NEGOCIO_NOMBRE}*\n\n'
            f'🧾 *Ticket de servicio*\n'
            f'Fecha: {self.fecha.strftime("%d/%m/%Y")}\n'
            f'Cliente: {self.nombre_cliente_display}\n'
            f'Vehículo: {self.vehiculo_descripcion_ticket}\n'
            f'Servicio: {self.tipo_servicio.nombre}{descripcion}'
            f'Total: ${self.precio_cobrado}\n\n'
            f'🙏 ¡Gracias{", " + primer_nombre if primer_nombre else ""}, por confiar en nuestro trabajo!\n\n'
            f'📍 {NEGOCIO_DIRECCION}\n'
            f'📱 {NEGOCIO_WHATSAPP_1} · {NEGOCIO_WHATSAPP_2}\n'
            f'📘 Facebook: {NEGOCIO_FACEBOOK}'
        )
        return f'https://wa.me/{numero}?text={quote(mensaje)}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        insumos = []
        if is_new:
            insumos = list(self.tipo_servicio.insumos.all())
            # Costo estimado: promedio de costo por vehículo de cada insumo que usa este paquete
            self.costo_insumos = round(sum(i.costo_por_servicio for i in insumos), 2)
        super().save(*args, **kwargs)
        if is_new:
            # Conteo automático de rendimiento: +1 vehículo al envase activo de cada insumo usado
            for insumo in insumos:
                envase = insumo.envase_activo
                if envase:
                    envase.vehiculos_atendidos += 1
                    envase.save(update_fields=['vehiculos_atendidos'])
