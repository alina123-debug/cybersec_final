from datetime import timedelta
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import Case, Alert, Rule, Task, Dispatch, DispatchChannel, Verdict, CaseStatus
from core.models import Client, Employee
from .serializers import CaseSerializer, AlertSerializer, RuleSerializer, EmployeeSerializer, ClientSerializer
from .filters import CaseFilter, AlertFilter
from .services import compute_dashboard, ingest_event

class CaseListAPI(generics.ListAPIView):
    queryset = Case.objects.all().order_by("-created_at")
    serializer_class = CaseSerializer
    filterset_class = CaseFilter
    permission_classes = [AllowAny]

class CaseDetailAPI(generics.RetrieveUpdateAPIView):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = [AllowAny]

    def patch(self, request, *args, **kwargs):
        case = self.get_object()
        # Allowed updates from UI
        allowed = {"status","verdict","title","description","analyst_name","analyst_group"}
        for k,v in request.data.items():
            if k in allowed:
                setattr(case, k, v)
        case.updated_at = timezone.now()
        case.save()
        return Response(CaseSerializer(case).data)

@api_view(["POST"])
def case_add_task(request, case_id: int):
    case = Case.objects.get(id=case_id)
    title = (request.data.get("title") or "").strip()
    if not title:
        return Response({"ok": False, "error": "title required"}, status=400)
    t = Task.objects.create(case=case, title=title, done=False)
    return Response({"ok": True, "task_id": t.id})

@api_view(["POST"])
def case_toggle_task(request, case_id: int, task_id: int):
    t = Task.objects.get(id=task_id, case_id=case_id)
    t.done = not t.done
    t.save()
    return Response({"ok": True, "done": t.done})

class AlertListAPI(generics.ListAPIView):
    queryset = Alert.objects.all().order_by("-created_at")
    serializer_class = AlertSerializer
    filterset_class = AlertFilter
    permission_classes = [AllowAny]

class RuleListAPI(generics.ListAPIView):
    queryset = Rule.objects.filter(enabled=True).order_by("incident_type")
    serializer_class = RuleSerializer
    permission_classes = [AllowAny]

class ClientListAPI(generics.ListAPIView):
    queryset = Client.objects.all().order_by("name")
    serializer_class = ClientSerializer
    permission_classes = [AllowAny]

class EmployeeListAPI(generics.ListAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        client_id = self.request.query_params.get("client")
        qs = Employee.objects.all()
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs.order_by("full_name")

@api_view(["GET"])
def dashboard_api(request):
    client_id = request.query_params.get("client")
    client = Client.objects.filter(id=client_id).first() if client_id else None
    stats = compute_dashboard(client)
    return Response({
        "total_alerts_today": stats.total_alerts_today,
        "severity_percent": stats.severity_percent,
        "last_scan_seconds_ago": stats.last_scan_seconds_ago,
        "incidents_today": stats.incidents_today,
        "timeline_hourly": stats.timeline_hourly,
        "threat_map_points": stats.threat_map_points,
    })

@api_view(["POST"])
def ingest_api(request):
    alert, case = ingest_event(request.data)
    return Response({"ok": True, "alert_id": alert.id, "case_id": case.id if case else None})

@api_view(["POST"])
def dispatch_case(request, case_id: int):
    case = Case.objects.get(id=case_id)
    channel = request.data.get("channel")
    recipients = request.data.get("recipients", [])
    if channel not in DispatchChannel.values:
        return Response({"ok": False, "error": "invalid channel"}, status=400)
    d = Dispatch.objects.create(case=case, channel=channel, recipients=recipients, sent_at=timezone.now())
    return Response({"ok": True, "dispatch_id": d.id})

@api_view(["GET"])

@api_view(["GET"])
def export_today_cases_csv(request):
    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    qs = Case.objects.filter(created_at__gte=start).order_by("-created_at")
    lines = ["case_id,created_at,client,severity,incident_type,status,verdict,title,source_ip,host_ip,hostname"]
    for c in qs:
        safe_title = (c.title or "").replace('"', '""')
        lines.append(
            f'{c.id},{c.created_at.isoformat()},{c.client.name},{c.severity},{c.incident_type},{c.status},{c.verdict},"{safe_title}",{c.source_ip},{c.host_ip},{c.hostname}'
        )
    content = "\n".join(lines)
    resp = HttpResponse(content, content_type="text/csv")
    resp["Content-Disposition"] = "attachment; filename=today_cases.csv"
    return resp
