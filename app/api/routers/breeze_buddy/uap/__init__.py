from fastapi import APIRouter, Request

from app.api.routers.breeze_buddy.uap import handlers
from app.api.routers.breeze_buddy.uap.handlers import WebhookAck

router = APIRouter()


@router.post("/webhook", response_model=WebhookAck)
async def uap_webhook(request: Request) -> WebhookAck:
    return await handlers.handle_webhook(request)
