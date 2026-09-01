from fastapi import Depends, FastAPI, HTTPException

from .infrai_client import InfraiClient, InfraiError
from .work_order_errors import WorkOrderError, capture_payload


service = FastAPI(title="Field-service error intake")


def get_client() -> InfraiClient:
    return InfraiClient()


@service.post("/work-order-errors", status_code=201)
def record_work_order_error(
    report: WorkOrderError,
    client: InfraiClient = Depends(get_client),
) -> dict[str, object]:
    try:
        captured = client.capture(capture_payload(report), report.capture_id)
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    return {
        "work_order_id": report.work_order_id,
        "workflow_stage": report.stage,
        "capture": captured,
    }

