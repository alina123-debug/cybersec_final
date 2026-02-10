import threading
import time
import random
from django.utils import timezone
from django.db import transaction

from soc.models import Alert, Case
from soc.ws import broadcast_event

from core.models import Client

SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
INCIDENTS = ["BRUTE_FORCE", "SQL_INJECTION", "XSS", "PATH_TRAVERSAL", "WINDOWS_SERVICE"]

def _sleep_realistic():
    #иногда часто, иногда редко
    delay = random.choice([
        random.randint(10, 25),      # быстрый демо-режим: 10–25 сек
        random.randint(60, 180),     # 1–3 мин
        random.randint(300, 600),    # 5–10 мин
        random.randint(900, 1800),   # 15–30 мин
        random.randint(3600, 7200),  # 1–2 часа
    ])
    time.sleep(delay)

def _create_event():
    sev = random.choices(SEVERITIES, weights=[10, 20, 40, 30])[0]
    inc = random.choice(INCIDENTS)
    title = f"{inc.replace('_',' ').title()} detected"

    now = timezone.now()

    client = Client.objects.first()
    if client is None:
        return


    with transaction.atomic():
        alert = Alert.objects.create(
            client=client,
            severity=sev,
            incident_type=inc,
            title=title,
            created_at=now,
        )

        # кейс создаётся не всегда 
        if sev in ("CRITICAL", "HIGH") or random.random() < 0.35:
            case = Case.objects.create(
                client=client,
                severity=sev,
                incident_type=inc,
                title=title,
                status="OPEN",
                created_at=now,
            )

            broadcast_event("new_case", case)

        else:
            broadcast_event("new_alert", alert)

def generator_loop():
    while True:
        try:
            _create_event()
            _sleep_realistic()
        except Exception as e:
            print("Background generator error:", e)
            time.sleep(10)

_started = False

def start_generator_once():
    global _started
    if _started:
        return
    _started = True
    t = threading.Thread(target=generator_loop, daemon=True)
    t.start()
    print(">>> Background log generator: ON")
