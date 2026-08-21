from django import forms
from .models import TipoServicio, TipoVehiculo, Servicio


class TipoServicioForm(forms.ModelForm):
    class Meta:
        model = TipoServicio
        fields = ['nombre', 'descripcion', 'orden', 'activo', 'insumos']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Neo Express'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'insumos': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }


class TipoVehiculoForm(forms.ModelForm):
    class Meta:
        model = TipoVehiculo
        fields = ['nombre', 'orden', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Camioneta familiar'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['fecha', 'hora', 'tipo_servicio', 'tipo_vehiculo',
                  'cliente', 'vehiculo', 'precio_cobrado', 'es_cortesia', 'insumos_usados', 'notas']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'tipo_servicio': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_servicio'}),
            'tipo_vehiculo': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_vehiculo'}),
            'cliente': forms.Select(attrs={'class': 'form-select', 'id': 'id_cliente'}),
            'vehiculo': forms.Select(attrs={'class': 'form-select', 'id': 'id_vehiculo'}),
            'precio_cobrado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'placeholder': '0.00', 'id': 'id_precio_cobrado'}),
            'es_cortesia': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_es_cortesia'}),
            'insumos_usados': forms.CheckboxSelectMultiple(),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
