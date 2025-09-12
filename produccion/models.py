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
    cantidad_alimento_diario = models.FloatField(default=0.0, help_text="Cantidad de alimento a dar por día (en kg)")
    talla_min_cm = models.FloatField(null=True, blank=True, verbose_name="Talla Mínima (cm)")
    talla_max_cm = models.FloatField(null=True, blank=True, verbose_name="Talla Máxima (cm)")
    bastidor = models.OneToOneField(Bastidor, on_delete=models.SET_NULL, null=True, blank=True, related_name='lote_actual')
    artesa = models.OneToOneField(Artesa, on_delete=models.SET_NULL, null=True, blank=True, related_name='lote_actual')
    jaula = models.OneToOneField(Jaula, on_delete=models.SET_NULL, null=True, blank=True, related_name='lote_actual')
    fecha_ingreso_etapa = models.DateField(default=timezone.now)
    peso_promedio_pez_gr = models.FloatField(default=0.0, help_text="Peso promedio en gramos")
    tipo_alimento = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.codigo_lote
        
    def save(self, *args, **kwargs):
        if not self.pk:
            prefijo = 'L'
            now = timezone.now()
            year_month = now.strftime('%y%m')
            ultimo = Lote.objects.filter(codigo_lote__startswith=f'{prefijo}{year_month}').order_by('codigo_lote').last()
            correlativo = int(ultimo.codigo_lote.split('-')[-1]) + 1 if ultimo else 1
            self.codigo_lote = f'{prefijo}{year_month}-{correlativo:03d}'
        super().save(*args, **kwargs)

class RegistroDiario(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='registros_diarios')
    fecha = models.DateField()
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