from django import forms
from .models import Cita


class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['fecha', 'hora', 'cliente', 'vehiculo', 'nombre_contacto',
                  'telefono_contacto', 'tipo_servicio', 'estado', 'notas']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'cliente': forms.Select(attrs={'class': 'form-select', 'id': 'id_cliente'}),
            'vehiculo': forms.Select(attrs={'class': 'form-select', 'id': 'id_vehiculo'}),
            'nombre_contacto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Si no está registrado como cliente'}),
            'telefono_contacto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'WhatsApp / teléfono'}),
            'tipo_servicio': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
