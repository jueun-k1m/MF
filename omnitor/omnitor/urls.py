"""
URL configuration for omnitor project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    # ========== pages =============
    path('', views.pages.dashboard_view, name='dashboard_page'),
    path('calibration/', views.pages.calibration_view, name='calibration_page'),
    path('journal/', views.pages.journal_view, name='journal_page'),
    path('graph/', views.pages.graph_view, name='graph_page'),

    # =========== views ============
    path('dashboard_api/', views.dashboard.dashboard_api, name='dashboard_api'),
    path('calibrate_api/', views.calibrate.calibrate_api, name='calibrate_api'),
    path('camera_time_api/', views.camera_time.camera_time_api, name='camera_api'),
    path('journal_api/', views.journal.journal_api, name='journal_api'),
    path('graph_api/', views.graph, name='graph_api'),
]
