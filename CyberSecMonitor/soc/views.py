from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from core.models import Client
from .models import Case, Alert, Rule, IncidentType, Severity, CaseStatus, Verdict
from .services import compute_dashboard

def _ui_lang(request):
    return request.session.get("ui_lang", "en")

def dashboard_page(request):
    lang = _ui_lang(request)
    stats = compute_dashboard()
    return render(request, "dashboard.html", {
        "lang": lang,
        "stats": stats,
        "incident_types": IncidentType.values,
        "severities": Severity.values,
    })

def alerts_page(request):
    lang = _ui_lang(request)
    return render(request, "alerts.html", {
        "lang": lang,
        "incident_types": IncidentType.values,
        "severities": Severity.values,
    })

def cases_page(request):
    lang = _ui_lang(request)
    return render(request, "cases.html", {
        "lang": lang,
        "incident_types": IncidentType.values,
        "severities": Severity.values,
        "statuses": CaseStatus.values,
        "verdicts": Verdict.values,
        "type_filter": request.GET.get("incident_type", ""),
    })

def case_detail_page(request, case_id: int):
    lang = _ui_lang(request)
    case = get_object_or_404(Case, id=case_id)
    client_employees = list(case.client.employees.all().order_by("full_name")[:5])
    return render(request, "case_detail.html", {
        "lang": lang,
        "case": case,
        "employees": client_employees,
        "statuses": CaseStatus.values,
        "verdicts": Verdict.values,
    })

def rules_page(request):
    lang = _ui_lang(request)
    rules = Rule.objects.all().order_by("incident_type")
    return render(request, "rules.html", {
        "lang": lang,
        "rules": rules,
    })

def reports_page(request):
    lang = _ui_lang(request)
    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_cases = Case.objects.filter(created_at__gte=start).order_by("-created_at")[:200]
    return render(request, "reports.html", {
        "lang": lang,
        "today_cases": today_cases,
    })

def settings_page(request):
    if request.method == "POST":
        ui_lang = request.POST.get("ui_lang", "en")
        if ui_lang in ["en", "ru"]:
            request.session["ui_lang"] = ui_lang
        return redirect("settings")
    return render(request, "settings.html", {
        "lang": _ui_lang(request),
    })

def playbook_page(request, slug: str):
    lang = _ui_lang(request)
    # map slugs to template files
    allowed = {
        "bruteforce": "playbooks/bruteforce.html",
        "sqli": "playbooks/sqli.html",
        "xss": "playbooks/xss.html",
        "path-traversal": "playbooks/path_traversal.html",
        "win-service": "playbooks/win_service.html",
    }
    tpl = allowed.get(slug)
    if not tpl:
        return render(request, "playbooks/not_found.html", {"lang": lang, "slug": slug}, status=404)
    return render(request, tpl, {"lang": lang})
