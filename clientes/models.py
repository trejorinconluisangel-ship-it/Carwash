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


VISITAS_PREMIO_PEQUENO = 5
VISITAS_PREMIO_GRANDE = 10


class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    visitas_lealtad = models.IntegerField(default=0)
    fecha_ultimo_premio = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def primer_nombre(self):
        return self.nombre.split()[0] if self.nombre else ''

    @property
    def numero_whatsapp(self):
        if not self.whatsapp:
            return ''
        numero = ''.join(filter(str.isdigit, self.whatsapp))
        if len(numero) == 10:
            numero = '52' + numero
        return numero

    @property
    def whatsapp_url(self):
        numero = self.numero_whatsapp
        return f'https://wa.me/{numero}' if numero else ''

    @property
    def whatsapp_cumpleanos_url(self):
        numero = self.numero_whatsapp
        if not numero:
            return ''
        from urllib.parse import quote
        mensaje = (
            f'¡Feliz cumpleaños, {self.primer_nombre}! 🎉🚗 Todo el equipo de Neowash Auto-Wash te desea un excelente día. '
            'Como regalo, tienes un detalle especial esperándote en tu próxima visita 🎁'
        )
        return f'https://wa.me/{numero}?text={quote(mensaje)}'

    @property
    def total_servicios(self):
        return self.servicios.count()

    @property
    def premio_pequeno_alcanzado(self):
        return self.visitas_lealtad >= VISITAS_PREMIO_PEQUENO

    @property
    def premio_grande_disponible(self):
        return self.visitas_lealtad >= VISITAS_PREMIO_GRANDE

    @property
    def visitas_restantes_pequeno(self):
        return max(0, VISITAS_PREMIO_PEQUENO - self.visitas_lealtad)

    @property
    def visitas_restantes_grande(self):
        return max(0, VISITAS_PREMIO_GRANDE - self.visitas_lealtad)


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


class OportunidadCliente(models.Model):
    """Etiqueta libre para marcar que a un cliente le vendría bien un servicio o
    producto que hoy no ofrecemos (o nos falta el insumo). Cuando ya esté
    disponible, se usa para filtrar a quién ofrecérselo por WhatsApp."""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='oportunidades')
    etiqueta = models.CharField(max_length=100, help_text='Ej: Descontaminación de cristales, Pulido de faros...')
    notas = models.TextField(blank=True, help_text='Detalle de por qué le serviría (opcional)')
    atendida = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Oportunidad de Cliente'
        verbose_name_plural = 'Oportunidades de Clientes'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.cliente.nombre} — {self.etiqueta}'
