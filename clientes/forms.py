from django import forms
from .models import Cliente, Vehiculo


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'whatsapp', 'email', 'notas']
        widgets = {
            'nombre':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'whatsapp':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': '444 123 4567'}),
            'email':     forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'notas':     forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Preferencias, observaciones...'}),
        }


class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['cliente', 'placa', 'marca', 'modelo', 'anio', 'color', 'tipo', 'notas']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'placa':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'AAA-000-A', 'style': 'text-transform:uppercase;'}),
            'marca':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Toyota, Nissan, Ford...'}),
            'modelo':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Corolla, Versa, F-150...'}),
            'anio':    forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2020', 'min': '1990', 'max': '2030'}),
            'color':   forms.Select(attrs={'class': 'form-select'}),
            'tipo':    forms.Select(attrs={'class': 'form-select'}),
            'notas':   forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class VehiculoSinClienteForm(forms.ModelForm):
    """Formulario de vehículo sin campo cliente (se pasa por URL)."""
    class Meta:
        model = Vehiculo
        fields = ['placa', 'marca', 'modelo', 'anio', 'color', 'tipo', 'notas']
        widgets = {
            'placa':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'AAA-000-A', 'style': 'text-transform:uppercase;'}),
            'marca':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Toyota, Nissan, Ford...'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Corolla, Versa, F-150...'}),
            'anio':   forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2020', 'min': '1990', 'max': '2030'}),
            'color':  forms.Select(attrs={'class': 'form-select'}),
            'tipo':   forms.Select(attrs={'class': 'form-select'}),
            'notas':  forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
