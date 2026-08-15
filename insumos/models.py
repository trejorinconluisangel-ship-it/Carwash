from django.db import models
from django.utils import timezone


class Proveedor(models.Model):
    nombre = models.CharField(max_length=150)
    contacto = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


CATEGORIA_CHOICES = [
    ('limpiador', 'Limpiador'),
    ('desengrasante', 'Desengrasante'),
    ('cera', 'Cera / Pulimento'),
    ('shampoo', 'Shampoo'),
    ('abrillantador', 'Abrillantador'),
    ('aromatizante', 'Aromatizante'),
    ('microfibra', 'Microfibra / Esponja'),
    ('otro', 'Otro'),
]

UNIDAD_CHOICES = [
    ('litro', 'Litro (L)'),
    ('mililitro', 'Mililitro (mL)'),
    ('kilo', 'Kilogramo (kg)'),
    ('gramo', 'Gramo (g)'),
    ('pieza', 'Pieza'),
    ('galon', 'Galón'),
]


class Insumo(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES, default='otro')
    unidad_medida = models.CharField(max_length=20, choices=UNIDAD_CHOICES, default='litro')
    contenido_envase = models.DecimalField(max_digits=10, decimal_places=3, default=1,
                                           help_text='Cuánto trae cada envase, en la unidad de medida (ej: 1 para un bote de 1 litro)')
    costo_envase = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                       help_text='Costo de un envase nuevo — se actualiza solo con la última compra')
    costo_estimado_servicio = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
                                                   help_text='Costo por servicio mientras no haya historial de rendimiento (opcional)')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='insumos')
    envases_en_bodega = models.PositiveIntegerField(default=0, help_text='Envases cerrados, sin abrir, guardados')
    envases_stock_minimo = models.PositiveIntegerField(default=0, help_text='Alerta si los envases en bodega bajan de este nivel')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Insumo'
        verbose_name_plural = 'Insumos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def stock_bajo(self):
        return self.envases_en_bodega <= self.envases_stock_minimo and self.envases_stock_minimo > 0

    @property
    def envase_activo(self):
        return self.envases_uso.filter(fecha_fin__isnull=True).first()

    @property
    def envases_terminados(self):
        return self.envases_uso.filter(fecha_fin__isnull=False)

    @property
    def rendimiento_promedio(self):
        terminados = [e for e in self.envases_terminados if e.vehiculos_atendidos > 0]
        if not terminados:
            return None
        return sum(e.vehiculos_atendidos for e in terminados) / len(terminados)

    @property
    def costo_por_servicio(self):
        terminados = [e for e in self.envases_terminados if e.vehiculos_atendidos > 0]
        if terminados:
            return round(sum(e.costo_por_vehiculo for e in terminados) / len(terminados), 2)
        return float(self.costo_estimado_servicio) if self.costo_estimado_servicio else 0.0

    @property
    def consumo_promedio_por_vehiculo(self):
        """Cuánto (en la unidad de medida) se gasta en promedio por vehículo, según el historial real."""
        terminados = [e for e in self.envases_terminados if e.vehiculos_atendidos > 0]
        if not terminados:
            return None
        return round(sum(e.consumo_por_vehiculo for e in terminados) / len(terminados), 3)


PRIORIDAD_LISTA = [
    ('fuego',    '🔥 Fuego'),
    ('pronto',   '⚡ Pronto'),
    ('sinprisa', '🌿 Sin prisa'),
]


class ItemLista(models.Model):
    insumo       = models.ForeignKey(Insumo, null=True, blank=True, on_delete=models.SET_NULL, related_name='items_lista')
    nombre_libre = models.CharField(max_length=200, blank=True)
    cantidad     = models.CharField(max_length=80, blank=True, help_text='Ej: 2 litros, 1 caja, 500 ml')
    proveedor    = models.ForeignKey(Proveedor, null=True, blank=True, on_delete=models.SET_NULL, related_name='items_lista')
    prioridad    = models.CharField(max_length=10, choices=PRIORIDAD_LISTA, default='sinprisa')
    notas        = models.CharField(max_length=400, blank=True)
    comprado     = models.BooleanField(default=False)
    fecha_compra = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Item de lista'
        verbose_name_plural = 'Lista de compras'

    def __str__(self):
        return self.nombre_display

    @property
    def nombre_display(self):
        return self.insumo.nombre if self.insumo_id else self.nombre_libre

    @property
    def color(self):
        return {'fuego': 'red', 'pronto': 'yellow', 'sinprisa': 'green'}.get(self.prioridad, 'cyan')


class Recordatorio(models.Model):
    texto            = models.CharField(max_length=500)
    prioridad        = models.CharField(max_length=10, choices=PRIORIDAD_LISTA, default='sinprisa')
    completado       = models.BooleanField(default=False)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Recordatorio'
        verbose_name_plural = 'Recordatorios'

    def __str__(self):
        return self.texto[:60]


class Compra(models.Model):
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, related_name='compras')
    envases = models.PositiveIntegerField(default=1, help_text='Cuántos envases compraste')
    costo_por_envase = models.DecimalField(max_digits=10, decimal_places=2)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    fecha = models.DateField()
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        ordering = ['-fecha', '-created_at']

    def __str__(self):
        return f'{self.insumo.nombre} — {self.envases} envase(s) ({self.fecha})'

    def save(self, *args, **kwargs):
        self.costo_total = self.envases * self.costo_por_envase
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.insumo.envases_en_bodega += self.envases
            self.insumo.costo_envase = self.costo_por_envase
            self.insumo.save(update_fields=['envases_en_bodega', 'costo_envase'])


class EnvaseEnUso(models.Model):
    """Ciclo de vida de un envase abierto: cuenta cuántos vehículos atendió hasta agotarse."""
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, related_name='envases_uso')
    fecha_inicio = models.DateField(default=timezone.localdate)
    fecha_fin = models.DateField(null=True, blank=True)
    costo_envase = models.DecimalField(max_digits=10, decimal_places=2, help_text='Costo del envase al momento de abrirlo')
    contenido_envase = models.DecimalField(max_digits=10, decimal_places=3, default=1,
                                           help_text='Contenido del envase al momento de abrirlo, en la unidad de medida del insumo')
    vehiculos_atendidos = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Envase en Uso'
        verbose_name_plural = 'Envases en Uso'
        ordering = ['-fecha_inicio']

    def __str__(self):
        estado = 'en uso' if self.fecha_fin is None else f'terminado {self.fecha_fin}'
        return f'{self.insumo.nombre} — abierto {self.fecha_inicio} ({estado})'

    @property
    def costo_por_vehiculo(self):
        if self.vehiculos_atendidos <= 0:
            return 0.0
        return round(float(self.costo_envase) / self.vehiculos_atendidos, 2)

    @property
    def consumo_por_vehiculo(self):
        if self.vehiculos_atendidos <= 0:
            return 0.0
        return round(float(self.contenido_envase) / self.vehiculos_atendidos, 3)
