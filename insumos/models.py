from django.db import models


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
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='insumos')
    stock_actual = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=3, default=0,
                                       help_text='Alerta si el stock baja de este nivel')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Insumo'
        verbose_name_plural = 'Insumos'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.get_unidad_medida_display()})'

    @property
    def stock_bajo(self):
        return self.stock_actual <= self.stock_minimo and self.stock_minimo > 0

    def servicios_posibles(self):
        from servicios.models import InsumoEnServicio
        resultados = []
        for rel in InsumoEnServicio.objects.filter(insumo=self, cantidad_por_servicio__gt=0):
            posibles = int(self.stock_actual / rel.cantidad_por_servicio) if rel.cantidad_por_servicio > 0 else 0
            resultados.append({
                'tipo_servicio': rel.tipo_servicio,
                'posibles': posibles,
                'uso_por_servicio': rel.cantidad_por_servicio,
            })
        return resultados


class Compra(models.Model):
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, related_name='compras')
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
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
        return f'{self.insumo.nombre} — {self.cantidad} {self.insumo.unidad_medida} ({self.fecha})'

    def save(self, *args, **kwargs):
        self.costo_total = self.cantidad * self.costo_unitario
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.insumo.stock_actual += self.cantidad
            self.insumo.save(update_fields=['stock_actual'])
