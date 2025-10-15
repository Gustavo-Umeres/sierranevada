# En sierra_nevada/celery.py

import os
from celery import Celery

# Establece el módulo de configuración de Django para el programa 'celery'.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sierra_nevada.settings')

app = Celery('sierra_nevada')

# Usa una cadena aquí para que el worker no tenga que serializar
# el objeto de configuración a los procesos hijos.
# - namespace='CELERY' significa que todas las claves de configuración de Celery
#   deben tener un prefijo `CELERY_`.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Carga automáticamente los módulos de tasks.py de todas las apps registradas.
app.autodiscover_tasks()