from fastapi.testclient import TestClient

from fieldservice_errors.service import get_client, service
from fieldservice_errors.work_order_errors import WorkOrderError, capture_payload


SAMPLE = {
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


class RecordingClient:
    def __init__(self) -> None:
        self.payload = None
        self.capture_id = None

    def capture(self, payload, capture_id):
        self.payload = payload
        self.capture_id = capture_id
        return {"event_id": "evt_demo", "error_group_id": "grp_photo_decode"}


def test_photo_error_is_grouped_by_stage_and_exception() -> None:
    payload = capture_payload(WorkOrderError.model_validate(SAMPLE))
    assert payload["fingerprint"] == [
        "field-service",
        "photo_processing",
        "ImageDecodeError",
    ]
    assert payload["context"]["follow_up_required"] is True


def test_route_captures_work_order_context() -> None:
    recorder = RecordingClient()
    service.dependency_overrides[get_client] = lambda: recorder
    try:
        response = TestClient(service).post("/work-order-errors", json=SAMPLE)
    finally:
        service.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["capture"]["error_group_id"] == "grp_photo_decode"
    assert recorder.capture_id == "wo-1842-photo-01"
    assert recorder.payload["context"]["dispatch_status"] == "on_site"

