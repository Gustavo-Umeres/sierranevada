import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from produccion.models import Lote, RegistroMortalidad


class Command(BaseCommand):
    help = 'Entrena y guarda el modelo de red neuronal para predecir riesgos de salud'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando recolección de datos para entrenamiento...")

        # --- RUTA ABSOLUTA CORRECTA ---
        MODEL_DIR = os.path.join(settings.BASE_DIR, 'produccion', 'ia')
        MODEL_PATH = os.path.join(MODEL_DIR, 'modelo_salud.h5')
        SCALER_PATH = os.path.join(MODEL_DIR, 'scaler_salud.pkl')
        os.makedirs(MODEL_DIR, exist_ok=True)  # Crea la carpeta si no existe

        # 1. Obtener datos históricos
        lotes_historicos = Lote.objects.exclude(etapa_actual='OVAS').filter(cantidad_total_peces__gt=0)
        if lotes_historicos.count() < 2:
            self.stdout.write(self.style.ERROR("No hay suficientes datos históricos para entrenar un modelo útil."))
            return

        features = []
        labels = []
        for lote in lotes_historicos:
            mortalidad_total = lote.registros_mortalidad.aggregate(total=Sum('cantidad'))['total'] or 0
            brote_mortalidad = 1 if (mortalidad_total > lote.cantidad_inicial * 0.05) else 0
            dias_en_etapa = (timezone.now().date() - lote.fecha_ingreso_etapa).days if lote.fecha_ingreso_etapa else 0

            features.append([
                lote.peso_promedio_inicial_gr or 0,
                lote.cantidad_inicial or 0,
                dias_en_etapa
            ])
            labels.append(brote_mortalidad)

        X = np.array(features, dtype=np.float32)
        y = np.array(labels, dtype=np.float32)

        # 2. Dividir y escalar datos
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        # 3. Construir y entrenar el modelo
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(X_train.shape[1],)),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        self.stdout.write("Entrenando red neuronal...")
        model.fit(X_train, y_train, epochs=100, batch_size=10, validation_split=0.2, verbose=0)

        # 4. Evaluar y guardar en la ruta absoluta
        loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
        self.stdout.write(f"Precisión del modelo en datos de prueba: {accuracy*100:.2f}%")

        model.save(MODEL_PATH)
        joblib.dump(scaler, SCALER_PATH)

        # --- MENSAJE DE ÉXITO CORREGIDO ---
        self.stdout.write(self.style.SUCCESS(f"Modelo guardado en: {MODEL_PATH}"))
