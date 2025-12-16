from django.shortcuts import render

# 1. 메인 대시보드 화면
def dashboard_view(request):
    return render(request, 'index.html')

# 2. 보정(Calibration) 설정 화면
def calibration_view(request):
    return render(request, 'index.html')

# 3. 농장 일지 화면
def journal_view(request):
    return render(request, 'index.html')

# 4. 그래프 분석 화면
def graph_view(request):
    return render(request, 'index.html')