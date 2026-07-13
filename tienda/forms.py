from django import forms
from .models import ProductoTienda, EntradaProducto, VentaProducto


class ProductoTiendaForm(forms.ModelForm):
    class Meta:
        model = ProductoTienda
        fields = ['nombre', 'descripcion', 'categoria', 'unidad', 'precio_compra', 'precio_venta',
                  'stock_minimo', 'proveedor', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Aromatizante Vainilla 250mL'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'unidad': forms.Select(attrs={'class': 'form-select'}),
            'precio_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00', 'id': 'id_precio_compra'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00', 'id': 'id_precio_venta'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'placeholder': '0'}),
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EntradaProductoForm(forms.ModelForm):
    class Meta:
        model = EntradaProducto
        fields = ['producto', 'cantidad', 'costo_unitario', 'fecha', 'proveedor', 'notas']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'placeholder': '0'}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class VentaProductoForm(forms.ModelForm):
    class Meta:
        model = VentaProducto
        fields = ['producto', 'cantidad', 'precio_unitario', 'fecha', 'notas']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select', 'id': 'id_producto_venta'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'placeholder': '1', 'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00', 'id': 'id_precio_unitario_venta'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
