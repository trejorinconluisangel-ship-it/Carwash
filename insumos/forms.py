from django import forms
from .models import Proveedor, Insumo, Compra


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'contacto', 'telefono', 'email', 'direccion', 'notas']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del proveedor'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Persona de contacto'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '444 123 4567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@proveedor.com'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = ['nombre', 'descripcion', 'categoria', 'unidad_medida', 'contenido_envase',
                  'costo_estimado_servicio', 'proveedor', 'envases_stock_minimo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Abrillantador de llantas'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-select'}),
            'contenido_envase': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': '1'}),
            'costo_estimado_servicio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': 'Opcional'}),
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'envases_stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'placeholder': '0'}),
        }


class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['insumo', 'envases', 'costo_por_envase', 'fecha', 'proveedor', 'notas']
        widgets = {
            'insumo': forms.Select(attrs={'class': 'form-select'}),
            'envases': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '1', 'placeholder': '1'}),
            'costo_por_envase': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
