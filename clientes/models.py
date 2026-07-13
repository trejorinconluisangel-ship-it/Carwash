from django.db import models


COLOR_CHOICES = [
    ('blanco', 'Blanco'), ('negro', 'Negro'), ('gris', 'Gris'),
    ('plata', 'Plata'), ('rojo', 'Rojo'), ('azul', 'Azul'),
    ('verde', 'Verde'), ('amarillo', 'Amarillo'), ('naranja', 'Naranja'),
    ('cafe', 'Café / Beige'), ('morado', 'Morado'), ('otro', 'Otro'),
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


class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def whatsapp_url(self):
        if not self.whatsapp:
            return ''
        numero = ''.join(filter(str.isdigit, self.whatsapp))
        if len(numero) == 10:
            numero = '52' + numero
        return f'https://wa.me/{numero}'

    @property
    def total_servicios(self):
        return sum(v.servicios.count() for v in self.vehiculos.all())


class Vehiculo(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='vehiculos')
    placa = models.CharField(max_length=20)
    marca = models.CharField(max_length=80)
    modelo = models.CharField(max_length=80, blank=True)
    anio = models.PositiveSmallIntegerField(null=True, blank=True)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='otro')
    tipo = models.CharField(max_length=20, choices=TIPO_VEHICULO_CHOICES, default='sedan')
    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'
        ordering = ['placa']

    def __str__(self):
        partes = [self.marca]
        if self.modelo:
            partes.append(self.modelo)
        if self.anio:
            partes.append(str(self.anio))
        partes.append(f'[{self.placa}]')
        return ' '.join(partes)

    @property
    def descripcion_completa(self):
        color = self.get_color_display()
        return f'{color} · {self.get_tipo_display()}'
