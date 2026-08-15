from django.db import models
from django.utils import timezone

from clientes.models import TIPO_VEHICULO_CHOICES


def _hora_actual():
    return timezone.localtime().time()


LUGAR_CHOICES = [
    ('negocio', 'En negocio'),
    ('domicilio', 'Recogido a domicilio'),
]

FORMA_PAGO_CHOICES = [
    ('efectivo', 'Efectivo'),
    ('transferencia', 'Transferencia'),
    ('tarjeta', 'Tarjeta'),
]

GASOLINA_CHOICES = [
    ('R', 'R'),
    ('1_4', '¼'),
    ('1_2', '½'),
    ('3_4', '¾'),
    ('lleno', 'Lleno'),
]

ENTREGA_CHOICES = [
    ('recoge', 'Pasa a recoger'),
    ('domicilio', 'Domicilio'),
]

DIAGRAMA_TIPO_CHOICES = [
    ('sedan', 'Sedán'),
    ('suv', 'SUV / Camioneta'),
    ('pickup', 'Pick Up'),
]

# vista -> (título, aspect-ratio css) por tipo de silueta. Imágenes en static/img/diagramas/.
DIAGRAMAS_CONFIG = {
    'sedan': [
        ('frontal', 'Frontal (frente)', '1.34'),
        ('trasero', 'Trasero (atrás)', '1.32'),
        ('lateral_izquierdo', 'Lateral izquierdo', '2.74'),
        ('lateral_derecho', 'Lateral derecho', '2.73'),
    ],
    'suv': [
        ('frontal', 'Frontal (frente)', '1.14'),
        ('trasero', 'Trasero (atrás)', '1.14'),
        ('lateral_izquierdo', 'Lateral izquierdo', '2.11'),
        ('lateral_derecho', 'Lateral derecho', '2.12'),
    ],
    'pickup': [
        ('frontal', 'Frontal (frente)', '1.16'),
        ('trasero', 'Trasero (atrás)', '1.16'),
        ('lateral_izquierdo', 'Lateral izquierdo', '2.47'),
        ('lateral_derecho', 'Lateral derecho', '2.50'),
    ],
}


class Recepcion(models.Model):
    fecha = models.DateField(default=timezone.localdate)
    hora_recepcion = models.TimeField(default=_hora_actual)
    lugar = models.CharField(max_length=10, choices=LUGAR_CHOICES, default='negocio')

    cliente = models.ForeignKey('clientes.Cliente', null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='recepciones')
    vehiculo = models.ForeignKey('clientes.Vehiculo', null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name='recepciones')

    cliente_nombre = models.CharField(max_length=150, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    forma_pago = models.CharField(max_length=15, choices=FORMA_PAGO_CHOICES, blank=True)

    placa = models.CharField(max_length=20, blank=True)
    marca = models.CharField(max_length=80, blank=True)
    modelo = models.CharField(max_length=80, blank=True)
    anio = models.PositiveSmallIntegerField(null=True, blank=True)
    color = models.CharField(max_length=20, blank=True)
    tipo_vehiculo_txt = models.CharField(max_length=20, choices=TIPO_VEHICULO_CHOICES, blank=True)
    km = models.PositiveIntegerField(null=True, blank=True)
    gasolina = models.CharField(max_length=6, choices=GASOLINA_CHOICES, blank=True)

    entrega = models.CharField(max_length=10, choices=ENTREGA_CHOICES, default='recoge')
    direccion_entrega = models.TextField(blank=True)

    diagrama_tipo = models.CharField(max_length=10, choices=DIAGRAMA_TIPO_CHOICES, default='sedan')
    diagrama_danos = models.JSONField(default=dict, blank=True)

    retiro_valores = models.BooleanField(default=False)
    obs_cliente = models.TextField(blank=True)
    obs_colaborador = models.TextField(blank=True)

    firma_cliente = models.TextField(blank=True)
    firma_colaborador = models.TextField(blank=True)

    servicio = models.OneToOneField('servicios.Servicio', null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='recepcion')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Recepción'
        verbose_name_plural = 'Recepciones'
        ordering = ['-fecha', '-hora_recepcion']

    def __str__(self):
        quien = self.cliente.nombre if self.cliente else (self.cliente_nombre or 'Cliente espontáneo')
        return f'{quien} — {self.placa or "sin placa"} — {self.fecha}'

    @property
    def vehiculo_descripcion(self):
        partes = [p for p in [self.marca, self.modelo] if p]
        if self.anio:
            partes.append(str(self.anio))
        return ' '.join(partes) or '—'

    @property
    def diagramas_activos(self):
        return DIAGRAMAS_CONFIG.get(self.diagrama_tipo, DIAGRAMAS_CONFIG['sedan'])
