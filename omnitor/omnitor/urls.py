from django.urls import path
from .views import dashboard, calibrate, camera_time, journal, graph 
from .views import pages

urlpatterns = [
    # ========== pages =============
    path('', pages.dashboard_view, name='dashboard_page'),
    path('calibrate/', pages.calibrate_view, name='calibrate_page'),
    path('journal/', pages.journal_view, name='journal_page'),
    path('graph/', pages.graph_view, name='graph_page'),

    # =========== views (API) ============
    path('dashboard_api/', dashboard.dashboard_api, name='dashboard_api'),
    path('calibrate_api/', calibrate.calibrate_api, name='calibrate_api'),
    path('camera_time_api/', camera_time.camera_time_api, name='camera_api'),
    path('journal_api/', journal.journal_api, name='journal_api'),
    path('graph_api/', graph.graph_api, name='graph_api'),
]
