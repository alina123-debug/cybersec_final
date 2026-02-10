from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def broadcast_event(event_name: str, obj=None):
    payload = {"event": event_name}

    if obj is not None:
        payload.update({
            "id": getattr(obj, "id", None),
            "severity": getattr(obj, "severity", None),
            "incident_type": getattr(obj, "incident_type", None),
            "title": getattr(obj, "title", None),
        })

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        "monitor",
        {
            "type": "broadcast",  #consumers.py -> broadcast()
            "payload": payload
        }
    )
