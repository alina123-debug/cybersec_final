from django.db import models
from django.utils import timezone

class Severity(models.TextChoices):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class CaseStatus(models.TextChoices):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"

class Verdict(models.TextChoices):
    TRUE_POSITIVE = "TRUE_POSITIVE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    DUPLICATE = "DUPLICATE"
    OTHER = "OTHER"

class DispatchChannel(models.TextChoices):
    TELEGRAM = "TELEGRAM"
    SIEM = "SIEM"  # TheHive-like

class IncidentType(models.TextChoices):
    BRUTE_FORCE = "BRUTE_FORCE"
    SQL_INJECTION = "SQL_INJECTION"
    XSS = "XSS"
    PATH_TRAVERSAL = "PATH_TRAVERSAL"
    SUSPICIOUS_SERVICE = "SUSPICIOUS_SERVICE"
    DDOS_BOT = "DDOS_BOT"
    DATA_THEFT = "DATA_THEFT"
    PHISHING = "PHISHING"
    INSIDER = "INSIDER"
    CRYPTOJACK = "CRYPTOJACK"

class Rule(models.Model):
    name = models.CharField(max_length=160)
    incident_type = models.CharField(max_length=40, choices=IncidentType.choices)
    severity = models.CharField(max_length=16, choices=Severity.choices)
    query_template = models.TextField()
    response_steps = models.TextField()
    enabled = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

class Alert(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    client = models.ForeignKey("core.Client", on_delete=models.CASCADE, related_name="alerts")
    severity = models.CharField(max_length=16, choices=Severity.choices)
    incident_type = models.CharField(max_length=40, choices=IncidentType.choices)
    title = models.CharField(max_length=200)
    raw_event = models.JSONField(default=dict)
    is_false_positive = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"[{self.severity}] {self.title}"

class Case(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    client = models.ForeignKey("core.Client", on_delete=models.CASCADE, related_name="cases")
    severity = models.CharField(max_length=16, choices=Severity.choices)
    incident_type = models.CharField(max_length=40, choices=IncidentType.choices)

    status = models.CharField(max_length=16, choices=CaseStatus.choices, default=CaseStatus.OPEN)
    verdict = models.CharField(max_length=20, choices=Verdict.choices, default=Verdict.OTHER)

    title = models.CharField(max_length=220)
    description = models.TextField(blank=True, default="")
    analyst_name = models.CharField(max_length=80, default="Unassigned")
    analyst_group = models.CharField(max_length=80, default="SOC L1")

    source_ip = models.CharField(max_length=64, blank=True, default="")
    host_ip = models.CharField(max_length=64, blank=True, default="")
    hostname = models.CharField(max_length=120, blank=True, default="")

    evidence = models.JSONField(default=dict)

    def __str__(self) -> str:
        return f"CASE-{self.id} {self.title}"

class Task(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=240)
    done = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.title

class Dispatch(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="dispatches")
    channel = models.CharField(max_length=16, choices=DispatchChannel.choices)
    recipients = models.JSONField(default=list)  # employees or systems
    sent_at = models.DateTimeField(null=True, blank=True)

class AuditLog(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    action = models.CharField(max_length=80)
    actor = models.CharField(max_length=120, default="system")
    object_type = models.CharField(max_length=80)
    object_id = models.IntegerField(null=True, blank=True)
    details = models.JSONField(default=dict)
