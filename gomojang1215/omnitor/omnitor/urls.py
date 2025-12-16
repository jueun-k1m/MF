from django.urls import path
from . import views

urlpatterns = [
    # ==========================
    # 1. 화면 (HTML Pages) - 브라우저 주소창에 치는 주소
    # ==========================
    path('', views.dashboard_view, name='dashboard_page'),         # 메인화면
    path('calibration/', views.calibration_view, name='calibration_page'),
    path('journal/', views.journal_view, name='journal_page'),
    path('analysis/', views.graph_view, name='graph_page'),

    # ==========================
    # 2. 데이터 (REST API) - 자바스크립트(fetch)가 요청하는 주소
    # ==========================
    path('api/dashboard/', views.dashboard_api, name='dashboard_api'),
    path('api/calibrate/', views.calibrate_api, name='calibrate_api'),
    path('api/camera/', views.camera_time_api, name='camera_api'),
    path('api/journal/', views.journal_api, name='journal_api'),
    path('api/graph/', views.graph_api, name='graph_api'),
]