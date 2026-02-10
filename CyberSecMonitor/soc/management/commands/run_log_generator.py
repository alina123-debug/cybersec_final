import asyncio
import random
import aiohttp
from django.core.management.base import BaseCommand
from django.utils import timezone

INCIDENTS = ["BRUTE_FORCE","SQL_INJECTION","XSS","PATH_TRAVERSAL","SUSPICIOUS_SERVICE"]
SEVERITIES = ["LOW","MEDIUM","HIGH","CRITICAL"]

def build_event(client_id: int):
    it = random.choice(INCIDENTS)
    sev = random.choices(SEVERITIES, weights=[32,40,20,8], k=1)[0]

    base = {
        "client_id": client_id,
        "incident_type": it,
        "severity": sev,
        "created_at": timezone.now().isoformat(),
        "source_ip": f"185.10.{random.randint(0,255)}.{random.randint(1,254)}",
        "host_ip": f"10.5.{random.randint(0,10)}.{random.randint(10,200)}",
        "hostname": random.choice(["WIN-APP-01","WEB-01","DB-01","AD-01"]),
        # threat map toy fields
        "origin_zone": random.randint(1, 5),
        "target_cluster": random.randint(1, 4),
    }

    if it == "BRUTE_FORCE":
        base |= {
            "title": "Possible Brute-Force",
            "case_title": "Brute-force login attempts",
            "username": random.choice(["admin","root","svc_backup","user1"]),
            "attempts": random.randint(20, 120),
            "tasks": [
                "Check if source IP is known/allowed",
                "Validate authentication logs for the username",
                "Block IP on firewall/WAF (if confirmed)",
                "Check for successful login after attempts",
            ],
            "force_case": sev in ["HIGH","CRITICAL"],
        }
    elif it == "SQL_INJECTION":
        base |= {
            "title": "SQL Injection attempt",
            "case_title": "SQLi attempt on web endpoint",
            "url": "/api/search?q=1%27%20OR%20%271%27=%271",
            "tasks": [
                "Check WAF logs and web access logs",
                "Confirm if request reached database",
                "Search for similar payloads from source IP",
                "Add/adjust WAF rule if needed",
            ],
            "force_case": True,
        }
    elif it == "XSS":
        base |= {
            "title": "XSS attempt detected",
            "case_title": "Reflected XSS attempt",
            "url": "/comments?text=<script>alert(1)</script>",
            "tasks": [
                "Confirm if payload rendered in UI",
                "Check CSP headers and sanitization",
                "Search for repeated attempts",
            ],
            "force_case": sev in ["HIGH","CRITICAL"],
        }
    elif it == "PATH_TRAVERSAL":
        base |= {
            "title": "Path Traversal attempt",
            "case_title": "Path traversal attempt on server",
            "url": "/download?file=../../../../etc/passwd",
            "tasks": [
                "Check server file access logs",
                "Confirm if sensitive file was accessed",
                "Patch/validate path normalization",
            ],
            "force_case": True,
        }
    else:  # SUSPICIOUS_SERVICE
        base |= {
            "title": "Suspicious activity on the system (Windows)",
            "case_title": "Suspicious Windows Service installed",
            "service_name": random.choice(["WinUpdateHelper","SysDriverX","TelemetrySvc"]),
            "service_path": r"C:\ProgramData\sys\svchost-helper.exe",
            "event_start_date": timezone.now().isoformat(),
            "tasks": [
                "Verify service legitimacy and signature",
                "Check persistence mechanisms (registry/run keys)",
                "Isolate host if malicious indicators confirmed",
                "Collect triage artifacts (process tree, hashes)",
            ],
            "force_case": True,
        }

    return base

class Command(BaseCommand):
    help = "Run async log generator that sends events into REST ingest endpoint."

    def add_arguments(self, parser):
        parser.add_argument("--url", default="http://127.0.0.1:8000/api/ingest/")
        parser.add_argument("--client", type=int, default=1)
        parser.add_argument("--interval", type=float, default=2.0)
        parser.add_argument("--count", type=int, default=0, help="If >0, send exactly N events then exit.")

    async def _run(self, url, client_id, interval, count):
        async with aiohttp.ClientSession() as session:
            sent = 0
            while True:
                event = build_event(client_id)
                try:
                    async with session.post(url, json=event, timeout=5) as resp:
                        await resp.text()
                except Exception:
                    pass
                sent += 1
                if count and sent >= count:
                    return
                await asyncio.sleep(interval)

    def handle(self, *args, **opts):
        asyncio.run(self._run(opts["url"], opts["client"], opts["interval"], opts["count"]))
