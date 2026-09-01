import os

import httpx


payload = {
    "capture_id": "wo-1842-photo-01",
    "work_order_id": "WO-1842",
    "stage": "photo_processing",
    "exception_type": "ImageDecodeError",
    "message": "HEIC preview could not be decoded",
    "photo_count": 4,
    "dispatch_status": "on_site",
    "technician_id": "TECH-22",
    "follow_up_required": True,
}

response = httpx.request(
    method="POST",
    url=os.environ.get("FIELD_SERVICE_URL", "http://127.0.0.1:8000")
    + "/work-order-errors",
    json=payload,
    timeout=10.0,
)
response.raise_for_status()
print(response.json())

