from django import forms
from django.forms import inlineformset_factory

from .models import (
    Cliente,
    PedidoMayorista,
    DetallePedidoMayorista,
    VentaMinoristaPOS,
    DetalleVentaPOS,
    VentaMinoristaPedido,
    DetalleVentaPedido,
)


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "ruc_dni", "direccion", "telefono", "email", "tipo_cliente"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nombre / Razón social"}
            ),
            "ruc_dni": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "RUC o DNI"}
            ),
            "direccion": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Dirección"}
            ),
            "telefono": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Teléfono"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Correo electrónico"}
            ),
            "tipo_cliente": forms.Select(attrs={"class": "form-control"}),
        }


class PedidoMayoristaForm(forms.ModelForm):
    class Meta:
        model = PedidoMayorista
        fields = ["cliente", "lote", "toneladas_solicitadas", "precio_unitario_ton"]
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-control"}),
            "lote": forms.Select(attrs={"class": "form-control"}),
            "toneladas_solicitadas": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "precio_unitario_ton": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
        }


class PedidoMayoristaAprobacionForm(forms.ModelForm):
    class Meta:
        model = PedidoMayorista
        fields = ["estado", "observaciones_aprobacion"]
        widgets = {
            "estado": forms.Select(attrs={"class": "form-control"}),
            "observaciones_aprobacion": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }


class DetallePedidoMayoristaForm(forms.ModelForm):
    class Meta:
        model = DetallePedidoMayorista
        fields = ["descripcion", "cantidad_ton", "precio_unitario_ton"]
        widgets = {
            "descripcion": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Descripción del ítem"}
            ),
            "cantidad_ton": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "precio_unitario_ton": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
        }


DetallePedidoMayoristaFormSet = inlineformset_factory(
    PedidoMayorista,
    DetallePedidoMayorista,
    form=DetallePedidoMayoristaForm,
    fields=["descripcion", "cantidad_ton", "precio_unitario_ton"],
    extra=1,
    can_delete=True,
)


class VentaMinoristaPOSForm(forms.ModelForm):
    class Meta:
        model = VentaMinoristaPOS
        fields = ["cliente", "lote", "fecha", "tipo_pago"]
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-control"}),
            "lote": forms.Select(attrs={"class": "form-control"}),
            "fecha": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "tipo_pago": forms.Select(attrs={"class": "form-control"}),
        }


class DetalleVentaPOSForm(forms.ModelForm):
    class Meta:
        model = DetalleVentaPOS
        fields = ["descripcion", "cantidad_kg", "precio_unitario_kg"]
        widgets = {
            "descripcion": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Descripción (ej. Filete, Entero)"}
            ),
            "cantidad_kg": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "precio_unitario_kg": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
        }


DetalleVentaPOSFormSet = inlineformset_factory(
    VentaMinoristaPOS,
    DetalleVentaPOS,
    form=DetalleVentaPOSForm,
    fields=["descripcion", "cantidad_kg", "precio_unitario_kg"],
    extra=1,
    can_delete=True,
)


class VentaMinoristaPedidoForm(forms.ModelForm):
    class Meta:
        model = VentaMinoristaPedido
        fields = ["cliente", "lote", "fecha_pedido", "fecha_entrega", "estado", "tipo_pago"]
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-control"}),
            "lote": forms.Select(attrs={"class": "form-control"}),
            "fecha_pedido": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "fecha_entrega": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "estado": forms.Select(attrs={"class": "form-control"}),
            "tipo_pago": forms.Select(attrs={"class": "form-control"}),
        }


class DetalleVentaPedidoForm(forms.ModelForm):
    class Meta:
        model = DetalleVentaPedido
        fields = ["descripcion", "cantidad_kg", "precio_unitario_kg"]
        widgets = {
            "descripcion": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Descripción del producto"}
            ),
            "cantidad_kg": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "precio_unitario_kg": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
        }


DetalleVentaPedidoFormSet = inlineformset_factory(
    VentaMinoristaPedido,
    DetalleVentaPedido,
    form=DetalleVentaPedidoForm,
    fields=["descripcion", "cantidad_kg", "precio_unitario_kg"],
    extra=1,
    can_delete=True,
)




