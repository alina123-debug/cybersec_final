from django.core.management.base import BaseCommand
from core.models import Client, Employee
from soc.models import Rule, IncidentType, Severity

class Command(BaseCommand):
    help = "Seed demo clients, employees (responsible people), and rules."

    def handle(self, *args, **opts):
        c1, _ = Client.objects.get_or_create(
            name="Aster Bank",
            defaults={
                "sla_critical_min": 60,
                "sla_high_min": 240,
                "sla_medium_min": 480,
                "sla_low_min": 1440,
            },
        )

        employees = [
            ("Aruzhan K.", "aruzhan@asterbank.local", "@aruzhan_soc", "Client Owner"),
            ("Timur S.", "timur@asterbank.local", "@timur_ir", "IR Lead"),
            ("Dana M.", "dana@asterbank.local", "@dana_blue", "SOC L2"),
            ("Nursultan A.", "nursultan@asterbank.local", "@nursultan_net", "Network Eng"),
            ("Amina R.", "amina@asterbank.local", "@amina_appsec", "AppSec"),
        ]
        for full_name, email, tg, role in employees:
            Employee.objects.get_or_create(
                client=c1,
                full_name=full_name,
                defaults={"email": email, "telegram_handle": tg, "role": role},
            )

        def add_rule(name, itype, sev, query, steps):
            Rule.objects.get_or_create(
                name=name,
                defaults={
                    "incident_type": itype,
                    "severity": sev,
                    "query_template": query,
                    "response_steps": steps,
                    "enabled": True,
                },
            )

        add_rule(
            "Brute-force detection",
            IncidentType.BRUTE_FORCE,
            Severity.HIGH,
            "auth.failed | where src_ip == <IP> and attempts > 20 | last 1h",
            "1) Check false positive (scanner/VPN).\n"
            "2) Search auth.success after failures.\n"
            "3) Block IP if malicious.\n"
            "4) Force MFA/password reset.\n"
            "SLA: High 1-4h, Critical 15-60m.",
        )

        add_rule(
            "SQL injection detection",
            IncidentType.SQL_INJECTION,
            Severity.CRITICAL,
            "web.access | where url contains \"UNION\" or url contains \"' OR '1'='1\" | last 24h",
            "1) Confirm if request reached DB.\n"
            "2) Check WAF action.\n"
            "3) Patch parameterized queries.\n"
            "4) Add WAF rule.\n"
            "SLA: Critical 15-60m.",
        )

        add_rule(
            "XSS detection",
            IncidentType.XSS,
            Severity.MEDIUM,
            "web.access | where url contains \"<script\" or url contains \"onerror=\" | last 24h",
            "1) Check reflected vs stored.\n"
            "2) Validate sanitization + CSP.\n"
            "3) Patch encoding.\n"
            "SLA: Medium 4-8h.",
        )

        add_rule(
            "Path traversal detection",
            IncidentType.PATH_TRAVERSAL,
            Severity.CRITICAL,
            "web.access | where url contains \"../\" or url contains \"%2e%2e%2f\" | last 24h",
            "1) Confirm access to sensitive files.\n"
            "2) Patch allow-list path validation.\n"
            "3) Block IP.\n"
            "SLA: Critical 15-60m.",
        )

        add_rule(
            "Suspicious Windows service install",
            IncidentType.SUSPICIOUS_SERVICE,
            Severity.HIGH,
            "windows.service_install | where service_path contains \"ProgramData\" | last 24h",
            "1) Verify signature + hash.\n"
            "2) Check persistence.\n"
            "3) Isolate host if malicious.\n"
            "SLA: High 1-4h.",
        )

        self.stdout.write(self.style.SUCCESS("Seeded demo data: 1 client, 5 employees, 5 rules."))
