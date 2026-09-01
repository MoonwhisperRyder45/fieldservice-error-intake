from typing import Literal

from pydantic import BaseModel, Field


WorkflowStage = Literal["photo_processing", "dispatch_sync", "technician_follow_up"]


class WorkOrderError(BaseModel):
    capture_id: str = Field(min_length=8)
    work_order_id: str = Field(min_length=1)
    stage: WorkflowStage
    exception_type: str = Field(min_length=1)
    message: str = Field(min_length=1)
    photo_count: int = Field(default=0, ge=0)
    dispatch_status: Literal["unassigned", "assigned", "en_route", "on_site", "completed"]
    technician_id: str | None = None
    follow_up_required: bool = False


def capture_payload(report: WorkOrderError) -> dict[str, object]:
    """Group recurring backend failures by workflow stage and exception class."""
    return {
        "title": f"Field service {report.stage} failed",
        "message": report.message,
        "exception": {
            "type": report.exception_type,
            "message": report.message,
        },
        "level": "error",
        "fingerprint": ["field-service", report.stage, report.exception_type],
        "context": {
            "work_order_id": report.work_order_id,
            "photo_count": report.photo_count,
            "dispatch_status": report.dispatch_status,
            "technician_id": report.technician_id,
            "follow_up_required": report.follow_up_required,
        },
        "tags": {
            "workflow_stage": report.stage,
            "dispatch_status": report.dispatch_status,
        },
    }

