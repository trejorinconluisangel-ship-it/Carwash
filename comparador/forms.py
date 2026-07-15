from django import forms
from .models import Categoria, Producto, PrecioProveedor


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Insumos, Herramientas, Limpieza…'}),
        }


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['insumo', 'nombre', 'descripcion', 'categoria', 'unidad']
        widgets = {
            'insumo':      forms.Select(attrs={'class': 'form-control', 'id': 'id_insumo_select'}),
            'nombre':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del producto'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descripción (opcional)'}),
            'categoria':   forms.Select(attrs={'class': 'form-control'}),
            'unidad':      forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        insumo = cleaned.get('insumo')
        nombre = (cleaned.get('nombre') or '').strip()
        if not insumo and not nombre:
            self.add_error('nombre', 'Escribe un nombre o vincula a un insumo existente.')
        return cleaned


class PrecioProveedorForm(forms.ModelForm):
    class Meta:
        model = PrecioProveedor
        fields = ['proveedor', 'precio', 'fecha_actualizacion', 'notas']
        widgets = {
            'proveedor':           forms.Select(attrs={'class': 'form-control'}),
            'precio':              forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'fecha_actualizacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notas':               forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ej: precio con descuento, presentación diferente…'}),
        }
