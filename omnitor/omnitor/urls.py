"""
URL configuration for omnitor project.
"""
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import api_dashboard, api_calibrate, api_journal, api_graph
from .views import pages

urlpatterns = [
    # ========== pages =============
    path('', pages.dashboard_view, name='dashboard_page'),
    path('calibrate/', pages.calibrate_view, name='calibrate_page'),
    path('journal/', pages.journal_view, name='journal_page'),
    path('graph/', pages.graph_view, name='graph_page'),

    # =========== views ============
    path('dashboard_api/', api_dashboard.dashboard_api, name='dashboard_api'),
    path('calibrate_api/', api_calibrate.calibrate_api, name='calibrate_api'),
    path('journal_api/', api_journal.journal_api, name='journal_api'),
    path('graph_api/', api_graph.graph_api, name='graph_api'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
