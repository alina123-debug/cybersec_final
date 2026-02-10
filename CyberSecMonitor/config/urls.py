from django.contrib import admin
from django.urls import path, include
from soc import views as soc_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # UI pages
    path("", soc_views.dashboard_page, name="dashboard"),
    path("alerts/", soc_views.alerts_page, name="alerts"),
    path("cases/", soc_views.cases_page, name="cases"),
    path("cases/<int:case_id>/", soc_views.case_detail_page, name="case_detail"),
    path("rules/", soc_views.rules_page, name="rules"),
    path("reports/", soc_views.reports_page, name="reports"),
    path("settings/", soc_views.settings_page, name="settings"),

    # Playbooks wiki
    path("playbooks/<slug:slug>/", soc_views.playbook_page, name="playbook"),

    # API
    path("api/", include("soc.api_urls")),
]
