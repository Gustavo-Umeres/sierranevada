from django.db import models
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from django.conf import settings
from django.utils import timezone
import math
from decimal import Decimal
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# ----------------------------------------------------------------
# MODELO PARA BASTIDORES (OVAS)
# ----------------------------------------------------------------
class Bastidor(models.Model):
    codigo = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    capacidad_maxima_unidades = models.PositiveIntegerField(default=0, help_text="Capacidad máxima en unidades de ovas")
    esta_disponible = models.BooleanField(default=True)

    def __str__(self):
        return self.codigo

    def save(self, *args, **kwargs):
        if not self.pk:
            prefijo = 'B'
            now = timezone.now()
            year_month = now.strftime('%y%m')
            ultimo = Bastidor.objects.filter(codigo__startswith=f'{prefijo}{year_month}').order_by('codigo').last()
            correlativo = int(ultimo.codigo.split('-')[-1]) + 1 if ultimo else 1
            self.codigo = f'{prefijo}{year_month}-{correlativo:02d}'
        super().save(*args, **kwargs)


# ----------------------------------------------------------------
# MODELO ABSTRACTO PARA UNIDADES CON CAPACIDAD POR BIOMASA
# ----------------------------------------------------------------
class UnidadProduccionBiomasa(models.Model):
    FORMAS = (
        ('RECTANGULAR', 'Rectangular'),
        ('CIRCULAR', 'Circular'),
        ('HEXAGONAL', 'Hexagonal'),
        ('DECAGONAL', 'Decagonal'),
    )
    
    forma = models.CharField(max_length=20, choices=FORMAS, default='RECTANGULAR', verbose_name="Forma de la unidad")
    largo_m = models.FloatField(null=True, blank=True, verbose_name="Largo (m)")
    ancho_m = models.FloatField(null=True, blank=True, verbose_name="Ancho (m)")
    diametro_m = models.FloatField(null=True, blank=True, verbose_name="Diámetro / Ancho (m)", help_text="Para formas circulares o poligonales, es la distancia de lado a lado.")
    lado_m = models.FloatField(null=True, blank=True, verbose_name="Longitud de Lado (calculado)", editable=False)
    alto_m = models.FloatField(null=True, blank=True, verbose_name="Altura del Agua / Profundidad Efectiva (m)")
    densidad_siembra_kg_m3 = models.FloatField(default=10.0, verbose_name="Densidad de Siembra (kg/m³)")
    capacidad_maxima_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False, verbose_name="Capacidad Máxima de Biomasa (kg)")

    class Meta:
        abstract = True

    def _calcular_volumen(self):
        volumen = 0
        h = self.alto_m or 0
        if self.forma == 'RECTANGULAR':
            l = self.largo_m or 0; w = self.ancho_m or 0; volumen = l * w * h
        elif self.forma == 'CIRCULAR':
            radio = (self.diametro_m or 0) / 2; volumen = math.pi * (radio ** 2) * h
        elif self.forma in ['HEXAGONAL', 'DECAGONAL']:
            num_lados = 6 if self.forma == 'HEXAGONAL' else 10
            apotema = (self.diametro_m or 0) / 2
            area_base = (num_lados * (self.lado_m or 0) * apotema) / 2
            volumen = area_base * h
        return Decimal(volumen) if volumen > 0 else Decimal(0)

    def _calcular_capacidad_biomasa(self):
        volumen = self._calcular_volumen()
        densidad = Decimal(self.densidad_siembra_kg_m3 or 0)
        return round(volumen * densidad, 2)

    def save(self, *args, **kwargs):
        if self.forma in ['HEXAGONAL', 'DECAGONAL'] and self.diametro_m:
            num_lados = 6 if self.forma == 'HEXAGONAL' else 10
            apotema = (self.diametro_m or 0) / 2
            self.lado_m = 2 * apotema * math.tan(math.pi / num_lados)
        else:
            self.lado_m = None
        self.capacidad_maxima_kg = self._calcular_capacidad_biomasa()
        super().save(*args, **kwargs)


# ----------------------------------------------------------------
# MODELOS DE UNIDADES DE PRODUCCIÓN
# ----------------------------------------------------------------
class Artesa(UnidadProduccionBiomasa):
    codigo = models.CharField(max_length=50, unique=True, blank=True, editable=False)

    @property
    def biomasa_actual(self):
        total = self.lotes.aggregate(total_biomasa=Coalesce(Sum(F('cantidad_total_peces') * F('peso_promedio_pez_gr') / Decimal(1000.0)), Decimal(0.0)))['total_biomasa']
        return round(total, 2)

    @property
    def biomasa_disponible(self):
        return self.capacidad_maxima_kg - self.biomasa_actual

    @property
    def alimento_diario_total_kg(self):
        return round(sum(lote.alimento_diario_kg for lote in self.lotes.all()), 2)

    def __str__(self):
        return self.codigo

    def save(self, *args, **kwargs):
        if not self.pk:
            prefijo = 'A'
            now = timezone.now()
            year_month = now.strftime('%y%m')
            ultimo = Artesa.objects.filter(codigo__startswith=f'{prefijo}{year_month}').order_by('codigo').last()
            correlativo = int(ultimo.codigo.split('-')[-1]) + 1 if ultimo else 1
            self.codigo = f'{prefijo}{year_month}-{correlativo:02d}'
        super().save(*args, **kwargs)

class Jaula(UnidadProduccionBiomasa):
    TIPO_JAULA = (('JUVENIL', 'Juvenil'), ('ENGORDE', 'Engorde'))
    codigo = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    tipo = models.CharField(max_length=10, choices=TIPO_JAULA, default='ENGORDE', verbose_name="Tipo de Jaula")

    @property
    def biomasa_actual(self):
        total = self.lotes.aggregate(total_biomasa=Coalesce(Sum(F('cantidad_total_peces') * F('peso_promedio_pez_gr') / Decimal(1000.0)), Decimal(0.0)))['total_biomasa']
        return round(total, 2)

    @property
    def biomasa_disponible(self):
        return self.capacidad_maxima_kg - self.biomasa_actual
    
    @property
    def alimento_diario_total_kg(self):
        return round(sum(lote.alimento_diario_kg for lote in self.lotes.all()), 2)

    def __str__(self):
        return f"{self.codigo} ({self.get_tipo_display()})"
    
    def save(self, *args, **kwargs):
        if not self.pk:
            prefijo = 'J'
            now = timezone.now()
            year_month = now.strftime('%y%m')
            ultimo = Jaula.objects.filter(codigo__startswith=f'{prefijo}{year_month}').order_by('codigo').last()
            correlativo = int(ultimo.codigo.split('-')[-1]) + 1 if ultimo else 1
            self.codigo = f'{prefijo}{year_month}-{correlativo:02d}'
        super().save(*args, **kwargs)

# ----------------------------------------------------------------
# MODELO DE LOTE (CON LÓGICA DE ALIMENTO CORREGIDA)
# ----------------------------------------------------------------
class Lote(models.Model):
    ETAPAS = (('OVAS', 'Ovas'), ('ALEVINES', 'Alevines'), ('JUVENILES', 'Juveniles'), ('ENGORDE', 'Engorde'))
    
    codigo_lote = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    etapa_actual = models.CharField(max_length=10, choices=ETAPAS)
    
    # --- CAMPOS NUEVOS PARA CÁLCULOS ---
    cantidad_inicial = models.PositiveIntegerField(default=0, editable=False, help_text="Cantidad de peces al inicio de la etapa actual")
    peso_promedio_inicial_gr = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'), editable=False, help_text="Peso promedio al inicio de la etapa actual")
    
    cantidad_total_peces = models.PositiveIntegerField(default=0)
    talla_min_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Talla Mínima (cm)")
    talla_max_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Talla Máxima (cm)")
    peso_promedio_pez_gr = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, help_text="Peso promedio en gramos")
    
    bastidor = models.OneToOneField('Bastidor', on_delete=models.SET_NULL, null=True, blank=True, related_name='lote_actual')
    artesa = models.ForeignKey('Artesa', on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes')
    jaula = models.ForeignKey('Jaula', on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes')
    
    fecha_ingreso_etapa = models.DateField(default=timezone.now)
    
    @property
    def tipo_alimento(self):
        """Determina el tipo de alimento recomendado según la talla."""
        if not self.talla_max_cm or self.talla_max_cm == 0:
            return "Alevines 1"
        
        talla = self.talla_max_cm

        if talla <= 8: return "Alevines 1"
        elif 8 < talla <= 10: return "Alevines 2"
        elif 10 < talla <= 15: return "Crecimiento 1"
        elif 15 < talla <= 20: return "Crecimiento 2"
        else: return "Engorde"

    @property
    def biomasa_kg(self):
        if self.cantidad_total_peces and self.peso_promedio_pez_gr:
            return (Decimal(self.cantidad_total_peces) * self.peso_promedio_pez_gr) / Decimal(1000)
        return Decimal(0)

    @property
    def racion_alimentaria_porcentaje(self):
        if not self.talla_max_cm or not self.peso_promedio_pez_gr:
            return Decimal(0)
        
        talla = self.talla_max_cm
        peso = self.peso_promedio_pez_gr
        
        # Lógica de ración basada en peso (más estándar en acuicultura)
        if peso <= 20: return Decimal('2.8')
        if peso <= 50: return Decimal('2.5')
        if peso <= 100: return Decimal('2.2')
        if peso <= 150: return Decimal('1.9')
        if peso <= 250: return Decimal('1.5')
        return Decimal('1.2')

    @property
    def alimento_diario_kg(self):
        if not self.cantidad_total_peces or not self.peso_promedio_pez_gr:
            return Decimal(0)
        
        racion = self.racion_alimentaria_porcentaje
        alimento_kg = (self.biomasa_kg * racion) / Decimal(100)
        return round(alimento_kg, 2)

    @property
    def ganancia_en_peso_gr(self):
        if self.peso_promedio_pez_gr and self.peso_promedio_inicial_gr is not None:
            return self.peso_promedio_pez_gr - self.peso_promedio_inicial_gr
        return Decimal(0)

    @property
    def conversion_alimenticia(self):
        biomasa_ganada_kg = (self.ganancia_en_peso_gr * Decimal(self.cantidad_total_peces)) / Decimal(1000)
        
        dias_en_etapa = (timezone.now().date() - self.fecha_ingreso_etapa).days
        if dias_en_etapa <= 0:
            return Decimal(0)
        
        # Este es un estimado simple. Una versión más precisa requeriría guardar el historial de alimentación.
        alimento_total_consumido_kg = self.alimento_diario_kg * dias_en_etapa

        if biomasa_ganada_kg > 0 and alimento_total_consumido_kg > 0:
            return round(alimento_total_consumido_kg / biomasa_ganada_kg, 2)
        return Decimal(0)
        
    def __str__(self):
        return self.codigo_lote
        
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            self.cantidad_inicial = self.cantidad_total_peces
            self.peso_promedio_inicial_gr = self.peso_promedio_pez_gr or Decimal('0.00')
            if not self.codigo_lote:
                prefijo = 'L'
                now = timezone.now()
                year_month = now.strftime('%y%m')
                ultimo = Lote.objects.filter(codigo_lote__startswith=f'{prefijo}{year_month}').order_by('codigo_lote').last()
                correlativo = int(ultimo.codigo_lote.split('-')[-1]) + 1 if ultimo else 1
                self.codigo_lote = f'{prefijo}{year_month}-{correlativo:03d}'
        
        super().save(*args, **kwargs)


# ----------------------------------------------------------------
# MODELOS DE REGISTROS
# ----------------------------------------------------------------
class RegistroDiario(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='registros_diarios')
    fecha = models.DateField(default=timezone.now)
    alimentacion_realizada = models.BooleanField(default=False)
    limpieza_realizada = models.BooleanField(default=False)
    class Meta: 
        unique_together = ('lote', 'fecha')
    def __str__(self): 
        return f"Registro de {self.lote.codigo_lote} para {self.fecha}"

class RegistroMortalidad(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='registros_mortalidad')
    fecha = models.DateField(auto_now_add=True)
    cantidad = models.PositiveIntegerField()
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    def __str__(self): 
        return f"{self.cantidad} bajas en {self.lote.codigo_lote} el {self.fecha}"
    

# produccion/models.py

class HistorialMovimiento(models.Model):
    TIPO_MOVIMIENTO = (
        ('CREACION', 'Creación de Lote'),
        ('MOVIMIENTO', 'Movimiento entre Unidades'),
        ('BAJAS', 'Registro de Mortalidad'),
        ('MEDICION', 'Registro de Talla/Peso'),
        ('FINALIZADO', 'Lote Finalizado'),
    )

    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='historial')
    fecha = models.DateTimeField(default=timezone.now)
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO)
    descripcion = models.CharField(max_length=255)
    cantidad_afectada = models.IntegerField(null=True, blank=True)
    
    # Puedes añadir más detalles si quieres
    # unidad_origen = models.CharField(max_length=50, blank=True)
    # unidad_destino = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.lote.codigo_lote} - {self.get_tipo_movimiento_display()} el {self.fecha.strftime('%d/%m/%Y')}"

    class Meta:
        ordering = ['-fecha']


class RegistroUnidad(models.Model):
    fecha = models.DateField(default=timezone.now)
    # Usaremos campos genéricos para apuntar a cualquier tipo de unidad
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    unidad = GenericForeignKey('content_type', 'object_id')

    # Datos consolidados del día
    biomasa_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cantidad_peces = models.PositiveIntegerField(default=0)
    alimento_kg = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    mortalidad_total = models.PositiveIntegerField(default=0)
    # Otros campos que quieras guardar...

    class Meta:
        unique_together = ('content_type', 'object_id', 'fecha')
        ordering = ['-fecha']

    def __str__(self):
        return f"Registro de {self.unidad} para {self.fecha}"