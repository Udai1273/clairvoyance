import json
from typing import Literal

from fastapi import Request
from pydantic import BaseModel

from app.core.logger import logger
from app.services.redis import get_redis_service, is_redis_configured

_DEDUPE_TTL_SECONDS = 7 * 24 * 3600
_MAX_BODY_BYTES = 1024 * 1024


class WebhookAck(BaseModel):
    status: Literal["ignored", "success"]


async def _is_duplicate(event_key: str) -> bool:
    if not is_redis_configured():
        return False
    try:
        redis = await get_redis_service()
        client = await redis.get_client()
        was_set = await client.set(
            f"uap:webhook:{event_key}", "1", nx=True, ex=_DEDUPE_TTL_SECONDS
        )
    except Exception as e:
        logger.error(f"UAP webhook dedupe unavailable, processing anyway: {e}")
        return False
    return not was_set


async def handle_webhook(request: Request) -> WebhookAck:
    raw = b""
    async for chunk in request.stream():
        raw += chunk
        if len(raw) > _MAX_BODY_BYTES:
            logger.error(f"UAP webhook body exceeds {_MAX_BODY_BYTES} bytes")
            return WebhookAck(status="ignored")

    try:
        event = json.loads(raw)
    except ValueError:
        logger.error(f"UAP webhook non-JSON body ({len(raw)} bytes)")
        return WebhookAck(status="ignored")
    if not isinstance(event, dict):
        logger.error("UAP webhook body is not a JSON object")
        return WebhookAck(status="ignored")

    event_id = str(event.get("id") or "")
    event_name = str(event.get("event_name") or "")
    content = event.get("content")
    order = content.get("order") if isinstance(content, dict) else None
    if not isinstance(order, dict):
        order = {}
    order_id = str(order.get("order_id") or order.get("id") or "")

    dedupe_key = event_id or f"{order_id}:{event_name}:{order.get('status', '')}"
    if dedupe_key and await _is_duplicate(dedupe_key):
        logger.info(f"UAP webhook duplicate skipped id={event_id} order={order_id}")
        return WebhookAck(status="success")

    logger.info(
        f"UAP webhook event={event_name} order_id={order_id} "
        f"status={order.get('status')} id={event_id}"
    )

    return WebhookAck(status="success")
