from django.db import models


CATEGORIA_TIENDA_CHOICES = [
    ('aromatizante', 'Aromatizante'),
    ('microfibra', 'Microfibra / Esponja'),
    ('cera', 'Cera / Pulimento'),
    ('shampoo', 'Shampoo'),
    ('desengrasante', 'Desengrasante'),
    ('accesorio', 'Accesorio para Auto'),
    ('limpiador', 'Limpiador Interior/Exterior'),
    ('otro', 'Otro'),
]

UNIDAD_TIENDA_CHOICES = [
    ('pieza', 'Pieza'),
    ('litro', 'Litro (L)'),
    ('mililitro', 'Mililitro (mL)'),
    ('kilo', 'Kilogramo (kg)'),
    ('par', 'Par'),
    ('paquete', 'Paquete'),
    ('kit', 'Kit'),
]


class ProductoTienda(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=30, choices=CATEGORIA_TIENDA_CHOICES, default='otro')
    unidad = models.CharField(max_length=20, choices=UNIDAD_TIENDA_CHOICES, default='pieza')
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                        help_text='Cuánto te costó a ti (precio de compra al proveedor)')
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                       help_text='Precio al que lo vendes al cliente')
    stock_actual = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    proveedor = models.ForeignKey('insumos.Proveedor', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='productos_tienda')
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Producto Tienda'
        verbose_name_plural = 'Productos Tienda'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def margen_ganancia(self):
        if self.precio_compra > 0:
            return round((float(self.precio_venta) - float(self.precio_compra)) / float(self.precio_compra) * 100, 1)
        return 0

    @property
    def ganancia_unitaria(self):
        return float(self.precio_venta) - float(self.precio_compra)

    @property
    def stock_bajo(self):
        return self.stock_actual <= self.stock_minimo and self.stock_minimo > 0

    @property
    def valor_inventario(self):
        return float(self.stock_actual) * float(self.precio_compra)


class EntradaProducto(models.Model):
    """Registra cuando compras mercancía para reabastecer la tienda."""
    producto = models.ForeignKey(ProductoTienda, on_delete=models.CASCADE, related_name='entradas')
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    fecha = models.DateField()
    proveedor = models.ForeignKey('insumos.Proveedor', on_delete=models.SET_NULL, null=True, blank=True)
    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Entrada de Producto'
        verbose_name_plural = 'Entradas de Productos'
        ordering = ['-fecha', '-created_at']

    def __str__(self):
        return f'{self.producto.nombre} +{self.cantidad} ({self.fecha})'

    def save(self, *args, **kwargs):
        self.costo_total = float(self.cantidad) * float(self.costo_unitario)
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.producto.stock_actual += self.cantidad
            self.producto.precio_compra = self.costo_unitario
            self.producto.save(update_fields=['stock_actual', 'precio_compra'])


class VentaProducto(models.Model):
    """Registra la venta de un producto de la tienda."""
    producto = models.ForeignKey(ProductoTienda, on_delete=models.CASCADE, related_name='ventas')
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    ganancia = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    fecha = models.DateField()
    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Venta de Producto'
        verbose_name_plural = 'Ventas de Productos'
        ordering = ['-fecha', '-created_at']

    def __str__(self):
        return f'{self.producto.nombre} ×{self.cantidad} (${self.total_venta}) — {self.fecha}'

    def save(self, *args, **kwargs):
        self.total_venta = float(self.cantidad) * float(self.precio_unitario)
        self.costo_total = float(self.cantidad) * float(self.producto.precio_compra)
        self.ganancia = self.total_venta - self.costo_total
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.producto.stock_actual -= self.cantidad
            if self.producto.stock_actual < 0:
                self.producto.stock_actual = 0
            self.producto.save(update_fields=['stock_actual'])
