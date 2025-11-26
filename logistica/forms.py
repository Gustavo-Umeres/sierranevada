from django import forms
from django.forms import inlineformset_factory
from .models import Proveedor, CategoriaInsumo, Insumo, OrdenCompra, DetalleOrdenCompra, MovimientoInventario

# --- FORMULARIOS PRINCIPALES CON ESTILO ---

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'ruc', 'direccion', 'telefono', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Proveedor S.A.C.'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 20123456789'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Av. Principal 123'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 987654321'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej: contacto@proveedor.com'}),
        }

class CategoriaInsumoForm(forms.ModelForm):
    class Meta:
        model = CategoriaInsumo
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Alimentos'}),
        }

class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = ['nombre', 'categoria', 'unidad_medida', 'stock_minimo']
        # Nota: stock_actual no se edita desde aquí, se maneja por movimientos.
        
        # --- ¡ESTE ES EL CAMBIO CLAVE! ---
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Alimento Alevín 1 (25kg)'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'unidad_medida': forms.Select(attrs={
                'class': 'form-control'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 100'
            }),
        }

class OrdenCompraForm(forms.ModelForm):
    class Meta:
        model = OrdenCompra
        fields = ['proveedor', 'fecha_esperada_entrega', 'estado']
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-control'}),
            'fecha_esperada_entrega': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar SOLO proveedores activos ↓↓↓
        self.fields['proveedor'].queryset = Proveedor.objects.filter(estado=True)

# --- FORMSET PARA DETALLES (CON ESTILO) ---

class DetalleOrdenCompraForm(forms.ModelForm):
    """
    Formulario base para que el formset tenga estilo.
    """
    class Meta:
        model = DetalleOrdenCompra
        fields = ('insumo', 'cantidad', 'precio_unitario')
        widgets = {
            'insumo': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Cantidad'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Precio S/.'}),
        }

# Formset para los detalles de la orden de compra
DetalleOrdenCompraFormSet = inlineformset_factory(
    OrdenCompra,
    DetalleOrdenCompra,
    form=DetalleOrdenCompraForm,  # Usamos el form con estilo
    fields=('insumo', 'cantidad', 'precio_unitario'),
    extra=1,
    can_delete=True
)

# --- OTROS FORMULARIOS ---

class MovimientoManualForm(forms.ModelForm):
    """
    Formulario para registrar entradas/salidas manuales.
    """
    class Meta:
        model = MovimientoInventario
        fields = ['insumo', 'tipo_movimiento', 'cantidad', 'descripcion']
        widgets = {
            'insumo': forms.Select(attrs={'class': 'form-control'}),
            'tipo_movimiento': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Cantidad a mover'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Despacho a estanque 5'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limitar las opciones a movimientos manuales
        self.fields['tipo_movimiento'].choices = [
            ('SALIDA', 'Salida (Producción/Baja)'),
            ('AJUSTE_POS', 'Ajuste Positivo (Sobrante)'),
            ('AJUSTE_NEG', 'Ajuste Negativo (Pérdida/Merma)'),
            ('ENTRADA', 'Entrada (Donación/Otro)'),
        ]