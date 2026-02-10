from django.contrib import admin
from .models import Rule, Alert, Case, Task, Dispatch, AuditLog

@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "incident_type", "severity", "enabled")
    list_filter = ("incident_type", "severity", "enabled")
    search_fields = ("name",)

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "client", "severity", "incident_type", "title")
    list_filter = ("client", "severity", "incident_type")
    search_fields = ("title",)

class TaskInline(admin.TabularInline):
    model = Task
    extra = 0

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "client", "severity", "incident_type", "status", "verdict", "title")
    list_filter = ("client", "severity", "incident_type", "status", "verdict")
    search_fields = ("title", "hostname", "source_ip", "host_ip")
    inlines = [TaskInline]

@admin.register(Dispatch)
class DispatchAdmin(admin.ModelAdmin):
    list_display = ("id", "case", "channel", "sent_at")

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "action", "actor", "object_type", "object_id")
