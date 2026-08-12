from django.db import models


ESTADO_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('confirmada', 'Confirmada'),
    ('completada', 'Completada'),
    ('cancelada', 'Cancelada'),
    ('no_show', 'No se presentó'),
]


class Cita(models.Model):
    fecha = models.DateField()
    hora = models.TimeField()

    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='citas')
    vehiculo = models.ForeignKey('clientes.Vehiculo', on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='citas')
    nombre_contacto = models.CharField(max_length=150, blank=True,
                                       help_text='Si el cliente aún no está registrado')
    telefono_contacto = models.CharField(max_length=20, blank=True)

    tipo_servicio = models.ForeignKey('servicios.TipoServicio', on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='citas')
    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES, default='pendiente')
    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['fecha', 'hora']

    def __str__(self):
        quien = self.cliente.nombre if self.cliente else (self.nombre_contacto or 'Sin nombre')
        return f'{quien} — {self.fecha} {self.hora}'

    @property
    def nombre_display(self):
        return self.cliente.nombre if self.cliente else (self.nombre_contacto or 'Cliente sin nombre')
