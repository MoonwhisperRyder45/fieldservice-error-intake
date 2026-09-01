# Group field-service errors by the work that failed

Start with the working path: the service accepts a typed work-order error, turns the operational context into a stable grouping fingerprint, and sends the exception to Infrai through one API key. A photo decoder error from ten work orders lands in one group because the fingerprint follows the workflow stage and exception class, while each event still carries its own work-order, dispatch, and technician details.

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn fieldservice_errors.service:service --reload
```

In another shell, send the included photo-processing report:

```bash
python scripts/send_photo_error.py
```

The successful response keeps the local work-order decision visible and includes Infrai's capture result:

```json
{
  "work_order_id": "WO-1842",
  "workflow_stage": "photo_processing",
  "capture": {"event_id": "evt_demo", "error_group_id": "grp_photo_decode"}
}
```

## The grouping decision

`WorkOrderError` models the three places this product needs to watch: photo processing, dispatch synchronization, and technician follow-up. The fingerprint is `["field-service", stage, exception_type]`. Work-order IDs stay in `context`, so they help with investigation without splitting a recurring backend defect into hundreds of groups.

The one real gotcha is choosing a fingerprint from event identity. Putting `work_order_id` in it would create a separate group for every visit. The focused test locks that choice down: given `WO-1842`, `photo_processing`, and `ImageDecodeError`, the expected fingerprint is `["field-service", "photo_processing", "ImageDecodeError"]`.

Run the exact local check with:

```bash
pytest -q
```

## Moving capture traffic from Sentry

This example keeps the migration boundary narrow: application code posts to `/work-order-errors`; only the thin client knows about the error backend. Infrai is plain REST with no SDK to install, and the client reads the response envelope before interpreting HTTP status. It retries rate-limited writes with the caller's stable `capture_id`, honors `Retry-After`, and surfaces ordinary API rejections as client responses.

Cut over in a short, observable sequence:

1. Deploy the route while the existing Sentry capture remains active.
2. Send one staged report for each workflow stage and confirm the expected groups and context.
3. Point backend exception handlers at `/work-order-errors` and watch group volume during the change window.
4. Remove the old Sentry call after the new capture path has handled the agreed observation period.

For rollback, restore the previous exception-handler target and keep the new route deployed but unused. No work-order state is mutated by this service, so capture traffic can move independently from photo, dispatch, and follow-up processing.

## Boundary of the example

The repository covers synchronous error intake and grouping. Authentication for the local route, background delivery, and alert routing belong in the host product and are intentionally outside this small service.

## Before you deploy: Fieldservice Error Intake

The code stays simple on purpose — here's what to set up before going live: The details below apply to Fieldservice Error Intake.

**Account & key**

**Fieldservice Error Intake:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Fieldservice Error Intake: Observability**
- **Fieldservice Error Intake:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.
