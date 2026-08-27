from __future__ import annotations

import json

from .provider import AwsStrandsContactBriefProvider

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
}


def lambda_handler(event, _context):
    request_context = event.get("requestContext", {}) if isinstance(event, dict) else {}
    http = request_context.get("http", {}) if isinstance(request_context, dict) else {}
    method = None
    if isinstance(event, dict):
        method = http.get("method") or event.get("httpMethod")
    if method == "OPTIONS":
        return {"statusCode": 204, "headers": CORS_HEADERS, "body": ""}
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)
    missing = [field for field in ("student_id", "date_from", "date_to") if not body.get(field)]
    if missing:
        return {
            "statusCode": 400,
            "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
            "body": json.dumps({"error": f"Missing fields: {', '.join(missing)}"}),
        }
    try:
        result = AwsStrandsContactBriefProvider().generate(
            student_id=body["student_id"],
            date_from=body["date_from"],
            date_to=body["date_to"],
            include_notes=body.get("include_notes", True),
        )
        return {
            "statusCode": 200,
            "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
            "body": json.dumps(result),
        }
    except Exception as error:
        return {
            "statusCode": 500,
            "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
            "body": json.dumps({"error": str(error)}),
        }
