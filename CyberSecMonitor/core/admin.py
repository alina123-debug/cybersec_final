from django.contrib import admin
from .models import Client, Employee

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sla_critical_min", "sla_high_min", "sla_medium_min", "sla_low_min")

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "client", "role", "email", "telegram_handle")
    list_filter = ("client", "role")
