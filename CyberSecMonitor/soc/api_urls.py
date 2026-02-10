from django.urls import path
from . import api

urlpatterns = [
    path("dashboard/", api.dashboard_api),
    path("ingest/", api.ingest_api),
    path("cases/", api.CaseListAPI.as_view()),
    path("cases/<int:pk>/", api.CaseDetailAPI.as_view()),
    path("cases/<int:case_id>/tasks/add/", api.case_add_task),
    path("cases/<int:case_id>/tasks/<int:task_id>/toggle/", api.case_toggle_task),
    path("alerts/", api.AlertListAPI.as_view()),
    path("rules/", api.RuleListAPI.as_view()),
    path("clients/", api.ClientListAPI.as_view()),
    path("employees/", api.EmployeeListAPI.as_view()),
    path("cases/<int:case_id>/dispatch/", api.dispatch_case),
    path("reports/today.csv", api.export_today_cases_csv),
]
