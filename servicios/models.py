from django.db import models
from django.utils import timezone


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
    precio_base = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tipo de Servicio'
        verbose_name_plural = 'Tipos de Servicio'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class TipoVehiculo(models.Model):
    nombre = models.CharField(max_length=80)
    multiplicador_precio = models.DecimalField(max_digits=4, decimal_places=2, default=1.0,
                                               help_text='Multiplicador sobre el precio base (ej: 1.5 = 50% más caro)')

    class Meta:
        verbose_name = 'Tipo de Vehículo'
        verbose_name_plural = 'Tipos de Vehículo'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class InsumoEnServicio(models.Model):
    """Define cuánto de un insumo se usa por cada tipo de servicio."""
    tipo_servicio = models.ForeignKey(TipoServicio, on_delete=models.CASCADE, related_name='insumos_requeridos')
    insumo = models.ForeignKey('insumos.Insumo', on_delete=models.CASCADE, related_name='servicios_que_usan')
    cantidad_por_servicio = models.DecimalField(max_digits=8, decimal_places=3,
                                                help_text='Cantidad de insumo usada por servicio')

    class Meta:
        verbose_name = 'Insumo en Servicio'
        verbose_name_plural = 'Insumos en Servicios'
        unique_together = ('tipo_servicio', 'insumo')

    def __str__(self):
        return f'{self.insumo.nombre} × {self.cantidad_por_servicio} en {self.tipo_servicio.nombre}'


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

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        # Calcular costo de insumos automáticamente al crear
        if is_new:
            costo = sum(
                float(rel.cantidad_por_servicio) * float(rel.insumo.costo_unitario)
                for rel in self.tipo_servicio.insumos_requeridos.select_related('insumo').all()
            )
            self.costo_insumos = round(costo, 2)
        super().save(*args, **kwargs)
        if is_new:
            for rel in self.tipo_servicio.insumos_requeridos.all():
                insumo = rel.insumo
                insumo.stock_actual -= rel.cantidad_por_servicio
                if insumo.stock_actual < 0:
                    insumo.stock_actual = 0
                insumo.save(update_fields=['stock_actual'])


class DetalleInsumoServicio(models.Model):
    """Registro del insumo efectivamente consumido en un servicio concreto."""
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='detalle_insumos')
    insumo = models.ForeignKey('insumos.Insumo', on_delete=models.CASCADE)
    cantidad_usada = models.DecimalField(max_digits=8, decimal_places=3)

    def __str__(self):
        return f'{self.insumo.nombre} × {self.cantidad_usada} en servicio #{self.servicio_id}'
