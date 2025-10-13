from django.db import models
from django.conf import settings
from django.utils import timezone

class Bastidor(models.Model):
    codigo = models.CharField(max_length=50, blank=True, editable=False)
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

class Artesa(models.Model):
    codigo = models.CharField(max_length=50, blank=True, editable=False)
    capacidad_maxima_unidades = models.PositiveIntegerField(default=0, help_text="Capacidad máxima en unidades de alevines")
    esta_disponible = models.BooleanField(default=True)

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

class Jaula(models.Model):
    codigo = models.CharField(max_length=50, blank=True, editable=False)
    capacidad_maxima_unidades = models.PositiveIntegerField(default=0, help_text="Capacidad máxima en unidades de peces")
    esta_disponible = models.BooleanField(default=True)

    def __str__(self):
        return self.codigo

    def save(self, *args, **kwargs):
        if not self.pk:
            prefijo = 'J'
            now = timezone.now()
            year_month = now.strftime('%y%m')
            ultimo = Jaula.objects.filter(codigo__startswith=f'{prefijo}{year_month}').order_by('codigo').last()
            correlativo = int(ultimo.codigo.split('-')[-1]) + 1 if ultimo else 1
            self.codigo = f'{prefijo}{year_month}-{correlativo:02d}'
        super().save(*args, **kwargs)

class Lote(models.Model):
    ETAPAS = (('OVAS', 'Ovas'), ('ALEVINES', 'Alevines'), ('ENGORDE', 'Engorde'))
    codigo_lote = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    etapa_actual = models.CharField(max_length=10, choices=ETAPAS)
    cantidad_total_peces = models.PositiveIntegerField(default=0)
    cantidad_alimento_diario_gr = models.FloatField(default=0.0, help_text="Cantidad de alimento a dar por día (en GRAMOS)")
    talla_min_cm = models.FloatField(null=True, blank=True, verbose_name="Talla Mínima (cm)")
    talla_max_cm = models.FloatField(null=True, blank=True, verbose_name="Talla Máxima (cm)")
    bastidor = models.OneToOneField(Bastidor, on_delete=models.SET_NULL, null=True, blank=True, related_name='lote_actual')
    artesa = models.OneToOneField(Artesa, on_delete=models.SET_NULL, null=True, blank=True, related_name='lote_actual')
    jaula = models.OneToOneField(Jaula, on_delete=models.SET_NULL, null=True, blank=True, related_name='lote_actual')
    fecha_ingreso_etapa = models.DateField(default=timezone.now)
    peso_promedio_pez_gr = models.FloatField(null=True, blank=True, help_text="Peso promedio en gramos")
    tipo_alimento = models.CharField(max_length=100, blank=True)
    
    # --- PROPIEDADES DE BIOMASA Y ALIMENTACIÓN ---
    @property
    def biomasa_kg(self):
        """Calcula y devuelve la biomasa total del lote en kilogramos."""
        if self.cantidad_total_peces and self.peso_promedio_pez_gr:
            biomasa_gramos = self.cantidad_total_peces * self.peso_promedio_pez_gr
            return biomasa_gramos / 1000
        return 0
    
    @property
    def biomasa_gr(self):
        """Calcula y devuelve la biomasa total del lote en gramos."""
        if self.cantidad_total_peces and self.peso_promedio_pez_gr:
            return self.cantidad_total_peces * self.peso_promedio_pez_gr
        return 0
    
    @property
    def etapa_crecimiento(self):
        """Determina la etapa de crecimiento basada en peso y talla."""
        if not self.peso_promedio_pez_gr or not self.talla_max_cm:
            return "Indeterminada"
        
        peso = self.peso_promedio_pez_gr
        talla = self.talla_max_cm
        
        if peso < 2 and talla < 3:
            return "Larva"
        elif peso < 10 and talla < 8:
            return "Alevín pequeño"
        elif peso < 25 and talla < 12:
            return "Alevín mediano"
        elif peso < 75 and talla < 18:
            return "Alevín grande"
        elif peso < 150 and talla < 25:
            return "Juvenil"
        elif peso < 300 and talla < 35:
            return "Adulto pequeño"
        else:
            return "Adulto"
    
    @property
    def tipo_alimento_recomendado(self):
        """Recomienda el tipo de alimento según la etapa de crecimiento."""
        etapa = self.etapa_crecimiento
        
        recomendaciones = {
            "Larva": "Microplancton, Artemia nauplii",
            "Alevín pequeño": "Artemia, Pellets 0.5mm",
            "Alevín mediano": "Pellets 1mm, Artemia",
            "Alevín grande": "Pellets 1.5mm, Pellets 2mm",
            "Juvenil": "Pellets 2mm, Pellets 3mm",
            "Adulto pequeño": "Pellets 3mm, Pellets 4mm",
            "Adulto": "Pellets 4mm, Pellets 5mm"
        }
        
        return recomendaciones.get(etapa, "Consultar especialista")
    
    @property
    def tasa_alimentacion_optima(self):
        """Calcula la tasa de alimentación óptima según peso y temperatura."""
        if not self.peso_promedio_pez_gr:
            return 0.0
        
        peso = self.peso_promedio_pez_gr
        
        # Tasas de alimentación basadas en peso (porcentaje de biomasa por día)
        if peso < 2:
            return 0.12  # 12% de la biomasa
        elif peso < 5:
            return 0.10  # 10% de la biomasa
        elif peso < 10:
            return 0.08  # 8% de la biomasa
        elif peso < 25:
            return 0.06  # 6% de la biomasa
        elif peso < 50:
            return 0.04  # 4% de la biomasa
        elif peso < 100:
            return 0.03  # 3% de la biomasa
        elif peso < 200:
            return 0.025 # 2.5% de la biomasa
        elif peso < 300:
            return 0.02  # 2% de la biomasa
        else:
            return 0.015 # 1.5% de la biomasa
    
    def calcular_alimentacion_optimizada(self):
        """Calcula la alimentación óptima basada en biomasa, peso y talla."""
        if not self.cantidad_total_peces or not self.peso_promedio_pez_gr:
            return {
                'cantidad_gr': 0,
                'tipo_alimento': 'No disponible',
                'etapa_crecimiento': 'Indeterminada',
                'tasa_alimentacion': 0,
                'biomasa_kg': 0,
                'recomendaciones': 'Completar datos de peso y talla'
            }
        
        biomasa_gr = self.biomasa_gr
        tasa = self.tasa_alimentacion_optima
        cantidad_gr = biomasa_gr * tasa
        
        return {
            'cantidad_gr': round(cantidad_gr, 2),
            'tipo_alimento': self.tipo_alimento_recomendado,
            'etapa_crecimiento': self.etapa_crecimiento,
            'tasa_alimentacion': round(tasa * 100, 2),  # En porcentaje
            'biomasa_kg': round(self.biomasa_kg, 2),
            'recomendaciones': self._generar_recomendaciones()
        }
    
    def _generar_recomendaciones(self):
        """Genera recomendaciones específicas para el lote."""
        recomendaciones = []
        
        if self.peso_promedio_pez_gr and self.talla_max_cm:
            peso = self.peso_promedio_pez_gr
            talla = self.talla_max_cm
            
            # Recomendaciones basadas en peso y talla
            if peso < 5:
                recomendaciones.append("Alimentar 4-6 veces al día")
                recomendaciones.append("Usar alimento de alta digestibilidad")
            elif peso < 25:
                recomendaciones.append("Alimentar 3-4 veces al día")
                recomendaciones.append("Monitorear crecimiento semanalmente")
            elif peso < 100:
                recomendaciones.append("Alimentar 2-3 veces al día")
                recomendaciones.append("Verificar calidad del agua")
            else:
                recomendaciones.append("Alimentar 2 veces al día")
                recomendaciones.append("Controlar parámetros de agua")
            
            # Recomendaciones específicas por etapa
            etapa = self.etapa_crecimiento
            if etapa in ["Larva", "Alevín pequeño"]:
                recomendaciones.append("Mantener temperatura estable")
                recomendaciones.append("Evitar sobrealimentación")
            elif etapa in ["Alevín mediano", "Alevín grande"]:
                recomendaciones.append("Incrementar gradualmente el tamaño del pellet")
                recomendaciones.append("Monitorear conversión alimenticia")
            elif etapa in ["Juvenil", "Adulto pequeño"]:
                recomendaciones.append("Optimizar frecuencia de alimentación")
                recomendaciones.append("Controlar densidad de población")
            else:
                recomendaciones.append("Preparar para cosecha")
                recomendaciones.append("Optimizar conversión alimenticia")
        
        return recomendaciones
    # -------------------------

    def __str__(self):
        return self.codigo_lote
        
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and not self.codigo_lote:
            prefijo = 'L'
            now = timezone.now()
            year_month = now.strftime('%y%m')
            ultimo = Lote.objects.filter(codigo_lote__startswith=f'{prefijo}{year_month}').order_by('codigo_lote').last()
            correlativo = int(ultimo.codigo_lote.split('-')[-1]) + 1 if ultimo else 1
            self.codigo_lote = f'{prefijo}{year_month}-{correlativo:03d}'
        super().save(*args, **kwargs)

    def calcular_alimento_estandar(self):
        racion_gramos = self.cantidad_total_peces / 100
        self.cantidad_alimento_diario_gr = round(racion_gramos, 2)
        self.save(update_fields=['cantidad_alimento_diario_gr'])

    def recalcular_alimento_por_biomasa(self):
        """Recalcula la alimentación diaria usando el sistema optimizado."""
        calculo = self.calcular_alimentacion_optimizada()
        self.cantidad_alimento_diario_gr = calculo['cantidad_gr']
        self.save(update_fields=['cantidad_alimento_diario_gr'])

class RegistroDiario(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='registros_diarios')
    fecha = models.DateField()
    alimentacion_realizada = models.BooleanField(default=False)
    limpieza_realizada = models.BooleanField(default=False)
    class Meta: unique_together = ('lote', 'fecha')
    def __str__(self): return f"Registro de {self.lote.codigo_lote} para {self.fecha}"

class RegistroMortalidad(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='registros_mortalidad')
    fecha = models.DateField(auto_now_add=True)
    cantidad = models.PositiveIntegerField()
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    def __str__(self): return f"{self.cantidad} bajas en {self.lote.codigo_lote} el {self.fecha}"

class Alimentacion(models.Model):
    """
    Modelo para registrar la alimentación detallada de larvas y peces.
    Permite llevar un historial completo de cuánto y cuándo se ha alimentado cada lote.
    """
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='registros_alimentacion')
    fecha = models.DateField(default=timezone.now)
    hora = models.TimeField(default=timezone.now)
    cantidad_alimento_gr = models.FloatField(help_text="Cantidad de alimento administrado en gramos")
    tipo_alimento = models.CharField(max_length=100, help_text="Tipo de alimento utilizado")
    observaciones = models.TextField(blank=True, help_text="Observaciones adicionales sobre la alimentación")
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha', '-hora']
        verbose_name = 'Registro de Alimentación'
        verbose_name_plural = 'Registros de Alimentación'
    
    def __str__(self):
        return f"Alimentación de {self.lote.codigo_lote} - {self.fecha} {self.hora}"
    
    def save(self, *args, **kwargs):
        # Actualizar el registro diario correspondiente
        registro_diario, created = self.lote.registros_diarios.get_or_create(fecha=self.fecha)
        registro_diario.alimentacion_realizada = True
        registro_diario.save()
        super().save(*args, **kwargs)