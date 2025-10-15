from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum
from .models import Artesa, Jaula, RegistroMortalidad, RegistroUnidad

@shared_task
def generar_registros_diarios_de_unidades():
    """
    Tarea programada para ejecutarse una vez al día (ej. a la 1 AM).
    Recopila los datos del día anterior para cada unidad y crea un registro de resumen.
    """
    # Se calcula sobre los datos del día que acaba de terminar.
    fecha_registro = timezone.now().date() - timedelta(days=1)
    
    print(f"Iniciando generación de registros para la fecha: {fecha_registro}")

    # Unificar los modelos de unidad para no repetir código
    unidades_a_procesar = list(Artesa.objects.prefetch_related('lotes').all()) + \
                          list(Jaula.objects.prefetch_related('lotes').all())

    for unidad in unidades_a_procesar:
        lotes_en_unidad = unidad.lotes.all()
        
        # Si la unidad estaba vacía, no se crea registro.
        if not lotes_en_unidad:
            continue

        # Cálculos consolidados para la unidad en ese día
        total_peces = sum(lote.cantidad_total_peces for lote in lotes_en_unidad)
        total_biomasa = sum(lote.biomasa_kg for lote in lotes_en_unidad)
        total_alimento = sum(lote.alimento_diario_kg for lote in lotes_en_unidad)
        
        mortalidad_del_dia = RegistroMortalidad.objects.filter(
            lote__in=lotes_en_unidad, 
            fecha=fecha_registro
        ).aggregate(total_bajas=Sum('cantidad'))['total_bajas'] or 0

        # Obtener el ContentType para el modelo de la unidad (Artesa o Jaula)
        content_type = ContentType.objects.get_for_model(unidad)

        # Crea o actualiza el registro para esa unidad y esa fecha
        RegistroUnidad.objects.update_or_create(
            content_type=content_type,
            object_id=unidad.pk,
            fecha=fecha_registro,
            defaults={
                'cantidad_peces': total_peces,
                'biomasa_kg': total_biomasa,
                'alimento_kg': total_alimento,
                'mortalidad_total': mortalidad_del_dia,
            }
        )
        print(f"Registro creado/actualizado para {unidad.codigo} - {fecha_registro}")

    return f"Registros diarios generados con éxito para el {fecha_registro}"