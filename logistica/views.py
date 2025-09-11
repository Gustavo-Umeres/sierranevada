from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_logistica(request):
    return render(request, 'logistica/dashboard.html')