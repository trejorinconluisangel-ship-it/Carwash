from django.db import models


PRIORIDAD_CHOICES = [
    ('fuego', '🔥 Fuego'),
    ('pronto', '⚡ Pronto'),
    ('sinprisa', '🌿 Sin prisa'),
]


class Pendiente(models.Model):
    texto = models.CharField(max_length=300)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='sinprisa')
    completado = models.BooleanField(default=False)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pendiente'
        verbose_name_plural = 'Pendientes'

    def __str__(self):
        return self.texto[:60]
