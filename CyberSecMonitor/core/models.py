from django.db import models

class Client(models.Model):
    name = models.CharField(max_length=120, unique=True)
    # SLA in minutes (simple)
    sla_critical_min = models.IntegerField(default=60)     # 15-60
    sla_high_min = models.IntegerField(default=240)        # 1-4h
    sla_medium_min = models.IntegerField(default=480)      # 4-8h
    sla_low_min = models.IntegerField(default=1440)        # 24-72h

    def __str__(self) -> str:
        return self.name


class Employee(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="employees")
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    telegram_handle = models.CharField(max_length=64, blank=True, default="")
    role = models.CharField(max_length=80, default="SOC Analyst")

    def __str__(self) -> str:
        return f"{self.full_name} ({self.client.name})"
