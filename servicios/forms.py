from django import forms
from .models import TipoServicio, TipoVehiculo, InsumoEnServicio, Servicio


class TipoServicioForm(forms.ModelForm):
    class Meta:
        model = TipoServicio
        fields = ['nombre', 'descripcion', 'precio_base', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Lavado Express Exterior'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'precio_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'placeholder': '0.00'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TipoVehiculoForm(forms.ModelForm):
    class Meta:
        model = TipoVehiculo
        fields = ['nombre', 'multiplicador_precio']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Camioneta / SUV'}),
            'multiplicador_precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.5', 'max': '5'}),
        }


class InsumoEnServicioForm(forms.ModelForm):
    class Meta:
        model = InsumoEnServicio
        fields = ['tipo_servicio', 'insumo', 'cantidad_por_servicio']
        widgets = {
            'tipo_servicio': forms.Select(attrs={'class': 'form-select'}),
            'insumo': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_por_servicio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': '0.000'}),
        }


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['fecha', 'hora', 'tipo_servicio', 'tipo_vehiculo',
                  'cliente', 'vehiculo', 'precio_cobrado', 'notas']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'tipo_servicio': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_servicio'}),
            'tipo_vehiculo': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_vehiculo'}),
            'cliente': forms.Select(attrs={'class': 'form-select', 'id': 'id_cliente'}),
            'vehiculo': forms.Select(attrs={'class': 'form-select', 'id': 'id_vehiculo'}),
            'precio_cobrado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'placeholder': '0.00', 'id': 'id_precio_cobrado'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
