from django.shortcuts import render


# 1. 대시보드

def dashboard_view(request):
    return render(request, 'dashboard.html')

# 2. 그래프

def graph_view(request):
    return render(request, 'graph.html')

# 3. 농장 일지

def journal_view(request):
    return render(request, 'journal.html')

# 4. 보정

def calibration_view(request):
    return render(request, 'calibrate.html')
