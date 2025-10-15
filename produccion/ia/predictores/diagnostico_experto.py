# produccion/ia/predictores/diagnostico_experto.py
import json
from django.conf import settings
import os

class SistemaExpertoSalud:
    def __init__(self):
        ruta_json = os.path.join(settings.BASE_DIR, 'produccion', 'ia', 'datos_entrenamiento', 'enfermedades_trucha.json')
        with open(ruta_json, 'r', encoding='utf-8') as f:
            self.base_conocimiento = json.load(f)

    def diagnosticar(self, sintomas_observados: list):
        """
        Recibe una lista de 0s y 1s correspondiente a los síntomas 
        y devuelve el mejor diagnóstico.
        """
        mejor_enfermedad = "Sano / Estrés leve"
        max_coincidencias = 0

        for nombre, detalles in self.base_conocimiento['enfermedades'].items():
            if 'sintomas' not in detalles:
                continue

            sintomas_enfermedad = detalles['sintomas']
            coincidencias = sum(1 for obs, esp in zip(sintomas_observados, sintomas_enfermedad) if obs == 1 and esp == 1)

            # Lógica simple: la enfermedad con más síntomas coincidentes gana
            if coincidencias > max_coincidencias:
                max_coincidencias = coincidencias
                mejor_enfermedad = nombre
        
        # Si hay al menos una coincidencia, devuelve la enfermedad. Si no, es probable que esté sano.
        if max_coincidencias > 0:
            resultado = self.base_conocimiento['enfermedades'][mejor_enfermedad]
            resultado['nombre'] = mejor_enfermedad
            return resultado
        else:
            return self.base_conocimiento['enfermedades']["Sano / Estrés leve"]