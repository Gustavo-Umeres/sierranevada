from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_comercializacion(request):
    return render(request, 'comercializacion/dashboard.html')