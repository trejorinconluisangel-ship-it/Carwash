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

    @property
    def primer_nombre(self):
        if self.cliente:
            return self.cliente.primer_nombre
        if self.nombre_contacto:
            return self.nombre_contacto.split()[0]
        return ''

    @property
    def telefono_display(self):
        if self.telefono_contacto:
            return self.telefono_contacto
        if self.cliente and self.cliente.whatsapp:
            return self.cliente.whatsapp
        return ''

    @property
    def whatsapp_recordatorio_url(self):
        tel = self.telefono_display
        if not tel:
            return ''
        from urllib.parse import quote
        from servicios.models import NEGOCIO_NOMBRE, NEGOCIO_DIRECCION, NEGOCIO_WHATSAPP_1, NEGOCIO_WHATSAPP_2

        numero = ''.join(filter(str.isdigit, tel))
        if len(numero) == 10:
            numero = '52' + numero
        servicio_txt = f' para {self.tipo_servicio.nombre}' if self.tipo_servicio else ''
        mensaje = (
            f'🚗💦 *{NEGOCIO_NOMBRE}*\n\n'
            f'¡Hola{", " + self.primer_nombre if self.primer_nombre else ""}! Te recordamos tu cita{servicio_txt} '
            f'el {self.fecha.strftime("%d/%m/%Y")} a las {self.hora.strftime("%H:%M")} hrs.\n\n'
            f'📍 {NEGOCIO_DIRECCION}\n'
            f'📱 {NEGOCIO_WHATSAPP_1} · {NEGOCIO_WHATSAPP_2}\n\n'
            f'¡Te esperamos! 🙌'
        )
        return f'https://wa.me/{numero}?text={quote(mensaje)}'
