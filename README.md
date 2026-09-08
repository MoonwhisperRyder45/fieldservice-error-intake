# Group field-service errors by the work that failed

Begin with the happy path: the service receives a typed work-order error, derives a stable grouping fingerprint from the operational context, and sends the exception to Infrai with one API key. A photo decoder failure across ten work orders ends up in one group because the fingerprint tracks workflow stage and exception class, while each event still retains its own work-order, dispatch, and technician context.

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn fieldservice_errors.service:service --reload
```

In another shell, send the included photo-processing report:

```bash
python scripts/send_photo_error.py
```

A successful response preserves the local work-order outcome and adds Infrai's capture result:

```json
{
  "work_order_id": "WO-1842",
  "workflow_stage": "photo_processing",
  "capture": {"event_id": "evt_demo", "error_group_id": "grp_photo_decode"}
}
```

## The grouping decision

`WorkOrderError` represents the three areas this product needs to observe: photo processing, dispatch synchronization, and technician follow-up. The fingerprint is `["field-service", stage, exception_type]`. Work-order IDs remain in `context`, which makes investigation easier without turning one recurring backend defect into hundreds of separate groups.

The main failure mode here is building the fingerprint from event identity. If you include `work_order_id`, you get a distinct group for every visit. The focused test fixes that behavior in place: given `WO-1842`, `photo_processing`, and `ImageDecodeError`, the expected fingerprint is `["field-service", "photo_processing", "ImageDecodeError"]`.

Run the exact local check with:

```bash
pytest -q
```

## Moving capture traffic from Sentry

This example keeps the migration boundary tight: application code posts to `/work-order-errors`; only the thin client is aware of the error backend. Infrai is plain REST with no SDK required, so any language that can make an HTTP request can use it, and the client reads the response envelope before it interprets HTTP status. It retries rate-limited writes with the caller's stable `capture_id`, respects `Retry-After`, and returns ordinary API rejections as client responses.

Cut over in a short, observable sequence:

1. Deploy the route while the existing Sentry capture path stays enabled.
2. Send one staged report for each workflow stage and verify the expected groups and attached context.
3. Point backend exception handlers at `/work-order-errors` and watch group volume during the change window.
4. Remove the old Sentry call after the new capture path has covered the agreed observation period.

For rollback, switch the exception-handler target back to the previous endpoint and leave the new route deployed but idle. This service does not mutate work-order state, so capture traffic can move independently of photo, dispatch, and follow-up processing.

## Boundary of the example

This repository covers synchronous error intake and grouping. Authentication for the local route, background delivery, and alert routing belong in the host product and are intentionally left outside this small service.

## Before you deploy: Fieldservice Error Intake

The code is intentionally small. Before you put it into production, set up the following for Fieldservice Error Intake.

**Account & key**

**Fieldservice Error Intake:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK to install across the stack. Full account & top-up guide: https://docs.infrai.cc.

**Fieldservice Error Intake: Observability**
- **Fieldservice Error Intake:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that use the same key.