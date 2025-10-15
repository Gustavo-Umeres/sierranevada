import pandas as pd
import joblib
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

class Command(BaseCommand):
    help = 'Entrena y guarda el modelo de clasificación para diagnóstico de enfermedades'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando entrenamiento del modelo de diagnóstico...")

        # --- Rutas para guardar el modelo ---
        MODEL_DIR = os.path.join(settings.BASE_DIR, 'produccion', 'ia', 'predictores')
        MODEL_PATH = os.path.join(MODEL_DIR, 'diagnostico_model.joblib')
        COLUMNS_PATH = os.path.join(MODEL_DIR, 'diagnostico_features.joblib')
        os.makedirs(MODEL_DIR, exist_ok=True)

        # --- Cargar y preparar los datos ---
        try:
            data_path = os.path.join(settings.BASE_DIR, 'produccion', 'ia', 'datos_entrenamiento', 'datos_diagnostico.csv')
            df = pd.read_csv(data_path)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Error: No se encontró el archivo de datos en {data_path}"))
            return

        # --- Definir características (features) y objetivo (target) ---
        # Todas las columnas excepto las de identificación y el diagnóstico final
        features = df.drop(columns=['fecha', 'lote_id', 'diagnostico_final'])
        target = df['diagnostico_final']

        # Guardar los nombres de las columnas para usarlos en la predicción
        joblib.dump(features.columns.tolist(), COLUMNS_PATH)
        
        # LÍNEA MODIFICADA
        X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

        # --- Entrenar el modelo RandomForest ---
        self.stdout.write("Entrenando el modelo RandomForestClassifier...")
        model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
        model.fit(X_train, y_train)

        # --- Evaluar el modelo ---
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        self.stdout.write(f"Precisión del modelo en datos de prueba: {accuracy*100:.2f}%")

        # --- Guardar el modelo entrenado ---
        joblib.dump(model, MODEL_PATH)
        self.stdout.write(self.style.SUCCESS(f"¡Modelo de diagnóstico guardado exitosamente en {MODEL_PATH}!"))