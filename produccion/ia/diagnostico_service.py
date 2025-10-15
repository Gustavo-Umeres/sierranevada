# En produccion/ia/diagnostico_service.py
#import tensorflow as tf
import joblib
import numpy as np
import os
from django.conf import settings
from django.utils import timezone
from produccion.models import Lote, RegistroCondiciones
from decimal import Decimal

class DiagnosticoService:
    def __init__(self):
        self.model = None
        self.scaler = None
        # La ruta al modelo debe estar en la carpeta 'ia/predictores'
        self.model_path = os.path.join(settings.BASE_DIR, 'produccion', 'ia', 'predictores', 'diagnostico_model.joblib')
        self.columns_path = os.path.join(settings.BASE_DIR, 'produccion', 'ia', 'predictores', 'diagnostico_features.joblib')
        self._load_model()

    def _load_model(self):
        try:
            self.model = joblib.load(self.model_path)
            self.feature_columns = joblib.load(self.columns_path)
        except FileNotFoundError:
            self.model = None
            self.feature_columns = None
        except Exception as e:
            self.model = None
            self.feature_columns = None
            raise Exception(f"Error al cargar el modelo o las columnas: {e}")

    def predecir(self, lote, registro_condiciones):
        if not self.model or not self.feature_columns:
            raise FileNotFoundError("El modelo de predicción no está disponible. Por favor, entrene el modelo con datos.")

        # Preparar los datos de entrada para la predicción, asegurando el orden correcto
        input_data = {
            'temp_agua': [float(registro_condiciones.temp_agua_c) if registro_condiciones.temp_agua_c else 0],
            'ph': [float(registro_condiciones.ph) if registro_condiciones.ph else 0],
            'oxigeno': [float(registro_condiciones.oxigeno_mg_l) if registro_condiciones.oxigeno_mg_l else 0],
            'amoniaco': [float(registro_condiciones.amoniaco_mg_l) if registro_condiciones.amoniaco_mg_l else 0],
            'sintoma_algodonoso': [0], # Suponemos que estos no están registrados y se mantienen en 0
            'sintoma_aletas_deshilachadas': [0],
            'comportamiento_anormal': [0]
        }
        
        # Crear DataFrame y asegurar el orden de las columnas
        input_df = pd.DataFrame(input_data)
        input_df = input_df[self.feature_columns]

        prediccion = self.model.predict(input_df)[0]
        probabilidades = self.model.predict_proba(input_df)[0]

        confianza = max(probabilidades) * 100
        
        # Mapeamos la predicción del modelo (que puede ser genérica) a un diagnóstico más rico
        diagnostico_principal = prediccion
        plan_de_accion_recomendado = KNOWLEDGE_BASE.get(diagnostico_principal, {}).get('plan_de_accion', ["No se encontró un plan de acción."])
        
        return {
            'lote': lote,
            'probabilidad': round(confianza, 2),
            'recomendacion': KNOWLEDGE_BASE.get(diagnostico_principal, {}).get('explicacion', "No hay una explicación disponible."),
            'nivel_riesgo': diagnostico_principal,
            'plan_de_accion': plan_de_accion_recomendado,
        }