import json

from fastapi import APIRouter, Depends, HTTPException, Request

from core.database import get_database
from integrations.github.config import GitHubConfigurationError, GitHubWebhookSettings
from integrations.github.webhooks import (SUPPORTED_EVENTS, GitHubWebhookError,
                                           validate_delivery, verify_signature)
from repositories.pull_requests import PullRequestRepository
from services.github_webhooks import GitHubWebhookService


router = APIRouter()


def webhook_service(db=Depends(get_database)):
    return GitHubWebhookService(PullRequestRepository(db))


@router.post('/github', status_code=202)
async def github_webhook(request: Request, service=Depends(webhook_service)):
    try:
        settings = GitHubWebhookSettings.from_environment()
    except GitHubConfigurationError as exc:
        raise HTTPException(503, 'GitHub webhooks are not configured') from exc
    content_length = request.headers.get('content-length')
    if content_length:
        try:
            if int(content_length) > settings.max_payload_bytes:
                raise HTTPException(413, 'GitHub webhook payload is too large')
        except ValueError as exc:
            raise HTTPException(400, 'Invalid content length') from exc
    body = await request.body()
    if len(body) > settings.max_payload_bytes:
        raise HTTPException(413, 'GitHub webhook payload is too large')
    try:
        verify_signature(body, request.headers.get('x-hub-signature-256'),
                         settings.secret.get_secret_value())
        delivery_id = validate_delivery(request.headers.get('x-github-delivery'))
    except GitHubWebhookError as exc:
        raise HTTPException(401, str(exc)) from exc
    event_type = request.headers.get('x-github-event', '')
    if event_type not in SUPPORTED_EVENTS:
        return {'accepted': True, 'ignored': True}
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(400, 'GitHub webhook payload is invalid') from exc
    if not isinstance(payload, dict):
        raise HTTPException(400, 'GitHub webhook payload is invalid')
    return await service.process(delivery_id, event_type, payload)
