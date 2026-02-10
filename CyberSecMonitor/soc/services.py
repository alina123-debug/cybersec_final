from __future__ import annotations
from dataclasses import dataclass
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Alert, Case, Task, Severity
from core.models import Client

@dataclass
class DashboardStats:
    total_alerts_today: int
    severity_percent: dict[str, float]
    last_scan_seconds_ago: int
    incidents_today: list[dict]
    timeline_hourly: list[dict]
    threat_map_points: list[dict]

def now_tz():
    return timezone.now()

def start_of_today():
    n = now_tz()
    return n.replace(hour=0, minute=0, second=0, microsecond=0)

def compute_dashboard(client: Client | None = None) -> DashboardStats:
    qs_alerts = Alert.objects.filter(created_at__gte=start_of_today())
    qs_cases = Case.objects.filter(created_at__gte=start_of_today())
    if client:
        qs_alerts = qs_alerts.filter(client=client)
        qs_cases = qs_cases.filter(client=client)

    total = qs_alerts.count() or 1

    sev_counts = dict(qs_alerts.values_list("severity").annotate(c=Count("id")))
    # Ensure keys exist
    for s in ["CRITICAL","HIGH","MEDIUM","LOW"]:
        sev_counts.setdefault(s, 0)

    severity_percent = {k: round(v * 100.0 / total, 1) for k, v in sev_counts.items()}

    # last scan = newest alert age
    newest = qs_alerts.order_by("-created_at").first()
    last_scan_seconds_ago = int((now_tz() - newest.created_at).total_seconds()) if newest else 9999

    incidents_today = list(
        qs_alerts.values("incident_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # timeline by hour based on cases (hover shows cases at that hour)
    timeline = []
    for h in range(24):
        hour_start = start_of_today() + timedelta(hours=h)
        hour_end = hour_start + timedelta(hours=1)
        c = qs_cases.filter(created_at__gte=hour_start, created_at__lt=hour_end).count()
        timeline.append({"hour": h, "cases": c})
    # threat map (toy meaning): origin zone and target cluster
    points = []
    for a in qs_alerts.order_by("-created_at")[:25]:
        e = a.raw_event or {}
        points.append({
            "x": int(e.get("origin_zone", 1)),
            "y": int(e.get("target_cluster", 1)),
            "severity": a.severity,
            "incident_type": a.incident_type,
        })

    return DashboardStats(
        total_alerts_today=qs_alerts.count(),
        severity_percent=severity_percent,
        last_scan_seconds_ago=last_scan_seconds_ago,
        incidents_today=incidents_today,
        timeline_hourly=timeline,
        threat_map_points=points,
    )

def push_ws(payload: dict):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "monitor",
        {"type": "broadcast", "payload": payload},
    )

def ingest_event(event: dict) -> tuple[Alert, Case | None]:
    client = Client.objects.get(id=event["client_id"])
    alert = Alert.objects.create(
        client=client,
        severity=event["severity"],
        incident_type=event["incident_type"],
        title=event["title"],
        raw_event=event,
    )

    created_case = None
    force_case = bool(event.get("force_case"))
    if alert.severity in [Severity.CRITICAL, Severity.HIGH] or force_case:
        created_case = Case.objects.create(
            client=client,
            severity=alert.severity,
            incident_type=alert.incident_type,
            title=event.get("case_title") or alert.title,
            description=event.get("description", "Auto-generated case from ingested alert."),
            analyst_name=event.get("analyst_name", "Unassigned"),
            analyst_group=event.get("analyst_group", "SOC L1"),
            source_ip=event.get("source_ip", ""),
            host_ip=event.get("host_ip", ""),
            hostname=event.get("hostname", ""),
            evidence=event,
        )
        for t in (event.get("tasks") or [])[:5]:
            Task.objects.create(case=created_case, title=t, done=False)

    push_ws({
        "event": "new_case" if created_case else "new_alert",
        "alert_id": alert.id,
        "case_id": created_case.id if created_case else None,
        "severity": alert.severity,
        "incident_type": alert.incident_type,
        "title": alert.title,
        "created_at": alert.created_at.isoformat(),
    })

    return alert, created_case
