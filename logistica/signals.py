from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from .models import MovimientoInventario

@receiver(post_save, sender=MovimientoInventario)
def actualizar_stock_on_save(sender, instance, created, **kwargs):
    """
    Actualiza el stock_actual del insumo CADA VEZ que se CREA un movimiento.
    """
    if created:
        insumo = instance.insumo
        if instance.tipo_movimiento in ['ENTRADA', 'AJUSTE_POS']:
            insumo.stock_actual = F('stock_actual') + instance.cantidad
        elif instance.tipo_movimiento in ['SALIDA', 'AJUSTE_NEG']:
            # Opcional: Validar que no quede en negativo
            # if insumo.stock_actual < instance.cantidad:
            #     # Manejar error de stock insuficiente
            #     pass 
            insumo.stock_actual = F('stock_actual') - instance.cantidad
        
        insumo.save(update_fields=['stock_actual'])

@receiver(post_delete, sender=MovimientoInventario)
def actualizar_stock_on_delete(sender, instance, **kwargs):
    """
    Revierte el movimiento si este es eliminado (opcional pero recomendado).
    """
    insumo = instance.insumo
    if instance.tipo_movimiento in ['ENTRADA', 'AJUSTE_POS']:
        insumo.stock_actual = F('stock_actual') - instance.cantidad
    elif instance.tipo_movimiento in ['SALIDA', 'AJUSTE_NEG']:
        insumo.stock_actual = F('stock_actual') + instance.cantidad
    
    insumo.save(update_fields=['stock_actual'])