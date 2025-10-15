# produccion/management/commands/entrenar_modelo_salud.py
import os
import numpy as np
import pandas as pd
import joblib
#import tensorflow as tf
from django.conf import settings
from django.core.management.base import BaseCommand
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

class Command(BaseCommand):
    help = 'Entrena y guarda un modelo básico de TensorFlow para el diagnóstico de salud.'

    def handle(self, *args, **options):
        self.stdout.write("Generando datos de ejemplo para el entrenamiento del modelo...")

        # Generar datos simulados
        # Características: peso_inicial, cantidad_inicial, dias_en_etapa
        np.random.seed(42)
        X = np.random.rand(100, 3) * [50, 20000, 90]
        # Etiqueta: probabilidad de enfermedad (simulada)
        y = (X[:, 0] * 0.005 + X[:, 2] * 0.002 + np.random.rand(100) * 0.3) / 10
        y = np.clip(y, 0, 1)

        # Crear un DataFrame y dividir los datos
        df = pd.DataFrame(X, columns=['temp_agua', 'ph', 'oxigeno'])
        df['salud_prob'] = y

        # Escalar los datos de entrada (fit y transform)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df[['temp_agua', 'ph', 'oxigeno']])
        y_scaled = df['salud_prob'].values

        # Construir el modelo de red neuronal
        model = tf.keras.models.Sequential([
            tf.keras.layers.Dense(10, activation='relu', input_shape=(3,)),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])

        # Entrenar el modelo
        model.fit(X_scaled, y_scaled, epochs=10, verbose=0)
        
        # Guardar el modelo y el scaler
        model_dir = os.path.join(settings.BASE_DIR, 'produccion', 'ia')
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

        model_path = os.path.join(model_dir, 'modelo_salud.h5')
        scaler_path = os.path.join(model_dir, 'scaler_salud.pkl')
        
        model.save(model_path)
        joblib.dump(scaler, scaler_path)

        self.stdout.write(self.style.SUCCESS(f"Modelo guardado en: {model_path}"))
        self.stdout.write(self.style.SUCCESS(f"Scaler guardado en: {scaler_path}"))