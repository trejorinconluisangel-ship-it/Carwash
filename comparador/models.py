from django.db import models
from django.utils import timezone


UNIDAD_CHOICES = [
    ('pieza', 'Pieza'),
    ('litro', 'Litro'),
    ('kg', 'Kilogramo'),
    ('gramo', 'Gramo'),
    ('ml', 'Mililitro'),
    ('par', 'Par'),
    ('caja', 'Caja'),
    ('paquete', 'Paquete'),
    ('rollo', 'Rollo'),
    ('otro', 'Otro'),
]


class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    insumo = models.OneToOneField(
        'insumos.Insumo', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='producto_comparador',
        verbose_name='Insumo vinculado',
    )
    nombre = models.CharField(max_length=200, blank=True)
    descripcion = models.TextField(blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    unidad = models.CharField(max_length=20, choices=UNIDAD_CHOICES, default='pieza', blank=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre_display

    @property
    def nombre_display(self):
        if self.insumo_id:
            return self.insumo.nombre
        return self.nombre

    @property
    def unidad_display(self):
        if self.insumo_id:
            return self.insumo.get_unidad_medida_display()
        return self.get_unidad_display()

    @property
    def es_vinculado(self):
        return self.insumo_id is not None

    @property
    def precio_minimo(self):
        p = self.precios.order_by('precio').first()
        return p.precio if p else None

    @property
    def proveedor_mas_barato(self):
        p = self.precios.select_related('proveedor').order_by('precio').first()
        return p.proveedor if p else None


class PrecioProveedor(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='precios')
    proveedor = models.ForeignKey('insumos.Proveedor', on_delete=models.CASCADE, related_name='precios_comparador')
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_actualizacion = models.DateField(default=timezone.now)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Precio por Proveedor'
        verbose_name_plural = 'Precios por Proveedor'
        ordering = ['precio']
        unique_together = [('producto', 'proveedor')]

    def __str__(self):
        return f'{self.producto} en {self.proveedor} — ${self.precio}'
