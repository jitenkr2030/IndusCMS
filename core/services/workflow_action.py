import ipaddress
import json
import socket
from datetime import timedelta

from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
    urlopen,
)

from django.db import transaction
from django.utils import timezone

from core.models import (
    WorkflowAction,
    WorkflowActionExecution,
)
from core.services.audit import log_action


VALID_ACTION_TYPES = {
    "audit",
    "notification",
    "webhook",
    "update_record",
}

MAX_WEBHOOK_TIMEOUT = 30
MAX_WEBHOOK_RESPONSE = 2000
MAX_WEBHOOK_PAYLOAD = 256 * 1024
MAX_RETRIES = 10
RETRY_BACKOFF_SECONDS = 30


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError(
            "Webhook redirects are not allowed."
        )


def _is_private_ip(address):
    ip = ipaddress.ip_address(address)
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _validate_webhook_host(url):
    parsed = urlparse(url)
    hostname = parsed.hostname

    if not hostname:
        raise ValueError(
            "Webhook URL must contain a hostname."
        )

    hostname = hostname.strip().lower()

    if hostname in {
        "localhost",
        "localhost.localdomain",
    } or hostname.endswith(".localhost"):
        raise ValueError(
            "Webhook private or local network targets are not allowed."
        )

    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                hostname,
                parsed.port or (
                    443
                    if parsed.scheme == "https"
                    else 80
                ),
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror as exc:
        raise ValueError(
            "Webhook hostname could not be resolved."
        ) from exc

    for address in addresses:
        if _is_private_ip(address):
            raise ValueError(
                "Webhook private or local network targets are not allowed."
            )


def _webhook_idempotency_key(
    config,
    action,
    instance,
    execution,
):
    configured = config.get("idempotency_key")

    if configured:
        return str(configured)

    execution_id = (
        str(execution.pk)
        if execution is not None
        else "direct"
    )

    return (
        f"induscms:"
        f"{instance.pk}:"
        f"{action.pk}:"
        f"{execution_id}"
    )


def _retry_delay(retry_count):
    retry_count = max(int(retry_count), 1)
    return min(
        RETRY_BACKOFF_SECONDS * (2 ** (retry_count - 1)),
        3600,
    )


def _mark_execution(
    *,
    execution,
    status,
    result=None,
    error="",
):
    execution.status = status
    execution.completed_at = timezone.now()
    execution.result = result or {}
    execution.error = str(error or "")

    execution.save(
        update_fields=[
            "status",
            "completed_at",
            "result",
            "error",
        ]
    )


def _build_webhook_payload(
    *,
    config,
    record,
    instance,
):
    payload = config.get("payload")

    if payload is None:
        payload = {
            "event": "workflow.action",
            "record_id": str(record.pk),
            "workflow_instance_id": str(instance.pk),
            "workflow_id": str(instance.workflow_id),
            "entity_id": str(record.entity_id),
            "data": record.data,
        }

    try:
        serialized = json.dumps(
            payload,
            default=str,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Webhook payload must be JSON serializable."
        ) from exc

    if len(serialized) > MAX_WEBHOOK_PAYLOAD:
        raise ValueError(
            "Webhook payload exceeds the 256 KB size limit."
        )

    if not isinstance(payload, dict):
        raise ValueError(
            "Webhook payload must be a JSON object."
        )

    return payload


def _execute_webhook(
    *,
    config,
    record,
    instance,
    action,
    execution,
):
    url = str(
        config.get("url", "")
    ).strip()

    if not url:
        raise ValueError(
            "Webhook action requires url."
        )

    parsed = urlparse(url)

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
    ):
        raise ValueError(
            "Webhook url must be a valid http or https URL."
        )

    if parsed.username or parsed.password:
        raise ValueError(
            "Webhook URL credentials are not allowed."
        )

    _validate_webhook_host(url)

    method = str(
        config.get("method", "POST")
    ).upper().strip()

    if method not in {
        "POST",
        "PUT",
        "PATCH",
    }:
        raise ValueError(
            "Webhook method must be POST, PUT, or PATCH."
        )

    try:
        timeout = float(
            config.get("timeout", 10)
        )
    except (TypeError, ValueError):
        raise ValueError(
            "Webhook timeout must be a number."
        )

    timeout = min(
        max(timeout, 1),
        MAX_WEBHOOK_TIMEOUT,
    )

    payload = _build_webhook_payload(
        config=config,
        record=record,
        instance=instance,
    )

    headers = config.get(
        "headers",
        {},
    )

    if not isinstance(headers, dict):
        raise ValueError(
            "Webhook headers must be a JSON object."
        )

    safe_headers = {
        str(key): str(value)
        for key, value in headers.items()
    }

    safe_headers.setdefault(
        "Content-Type",
        "application/json",
    )

    safe_headers.setdefault(
        "Accept",
        "application/json",
    )

    safe_headers.setdefault(
        "User-Agent",
        "IndusCMS-Workflow/1.0",
    )

    safe_headers.setdefault(
        "X-IndusCMS-Idempotency-Key",
        _webhook_idempotency_key(
            config,
            action,
            instance,
            execution,
        ),
    )

    body = json.dumps(
        payload,
        default=str,
    ).encode("utf-8")

    if len(body) > MAX_WEBHOOK_PAYLOAD:
        raise ValueError(
            "Webhook payload exceeds the 256 KB size limit."
        )

    request = Request(
        url,
        data=body,
        headers=safe_headers,
        method=method,
    )

    try:
        opener = build_opener(
            _NoRedirectHandler()
        )

        with opener.open(
            request,
            timeout=timeout,
        ) as response:

            status_code = getattr(
                response,
                "status",
                None,
            )

            response_body = response.read(
                MAX_WEBHOOK_RESPONSE
            ).decode(
                "utf-8",
                errors="replace",
            )

    except HTTPError as exc:
        response_body = exc.read(
            MAX_WEBHOOK_RESPONSE
        ).decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Webhook returned HTTP {exc.code}: "
            f"{response_body}"
        ) from exc

    except URLError as exc:
        raise RuntimeError(
            f"Webhook delivery failed: "
            f"{exc.reason}"
        ) from exc

    if status_code is None:
        status_code = 200

    if not (
        200 <= int(status_code) < 300
    ):
        raise RuntimeError(
            f"Webhook returned HTTP "
            f"{status_code}: {response_body}"
        )

    return {
        "delivered": True,
        "status_code": int(status_code),
        "response_body": response_body,
        "method": method,
        "url": url,
    }


def execute_workflow_action(
    *,
    action,
    instance,
    execution=None,
    user=None,
    ip_address=None,
):
    if not action.is_active:
        return {
            "success": True,
            "skipped": True,
            "reason": "Action is inactive.",
        }

    record = instance.record
    business = instance.workflow.business
    config = action.config or {}

    if action.action_type == "audit":

        audit_action = config.get(
            "action",
            "workflow.action.executed",
        )

        log_action(
            business=business,
            user=user,
            action=audit_action,
            resource="workflow_action",
            object_id=action.pk,
            ip_address=ip_address,
            metadata={
                "workflow_instance_id": str(
                    instance.pk
                ),
                "record_id": str(
                    record.pk
                ),
                "action_id": str(
                    action.pk
                ),
                "message": config.get(
                    "message",
                    action.name,
                ),
            },
        )

        return {
            "success": True,
            "action": "audit",
        }

    if action.action_type == "notification":

        message = config.get(
            "message",
            action.name,
        )

        channel = config.get(
            "channel",
            "in_app",
        )

        recipient = config.get(
            "recipient",
            "",
        )

        log_action(
            business=business,
            user=user,
            action="workflow.notification.triggered",
            resource="workflow_action",
            object_id=action.pk,
            ip_address=ip_address,
            metadata={
                "workflow_instance_id": str(
                    instance.pk
                ),
                "record_id": str(
                    record.pk
                ),
                "recipient": recipient,
                "message": message,
                "channel": channel,
            },
        )

        return {
            "success": True,
            "action": "notification",
            "channel": channel,
            "recipient": recipient,
            "message": message,
        }

    if action.action_type == "update_record":

        field_slug = config.get(
            "field_slug"
        )

        value = config.get(
            "value"
        )

        if not field_slug:
            raise ValueError(
                "update_record action requires "
                "field_slug."
            )

        record.data[field_slug] = value

        record.save(
            update_fields=[
                "data",
                "updated_at",
            ]
        )

        log_action(
            business=business,
            user=user,
            action="workflow.record.updated",
            resource="entity_record",
            object_id=record.pk,
            ip_address=ip_address,
            metadata={
                "workflow_instance_id": str(
                    instance.pk
                ),
                "action_id": str(
                    action.pk
                ),
                "field_slug": field_slug,
                "value": value,
            },
        )

        return {
            "success": True,
            "action": "update_record",
            "field_slug": field_slug,
        }

    if action.action_type == "webhook":

        result = _execute_webhook(
            config=config,
            record=record,
            instance=instance,
            action=action,
            execution=execution,
        )

        log_action(
            business=business,
            user=user,
            action="workflow.webhook.delivered",
            resource="workflow_action",
            object_id=action.pk,
            ip_address=ip_address,
            metadata={
                "workflow_instance_id": str(
                    instance.pk
                ),
                "record_id": str(
                    record.pk
                ),
                **result,
            },
        )

        return {
            "success": True,
            "action": "webhook",
            **result,
        }

    raise ValueError(
        "Invalid workflow action type."
    )


def retry_workflow_action_execution(
    *,
    execution,
    user=None,
    ip_address=None,
):
    """
    Retry a failed workflow action execution.

    A retry reuses the same execution record so the full lifecycle
    remains visible in one persistent execution entry.
    """

    if execution.status != "failed":
        raise ValueError(
            "Only failed action executions can be retried."
        )

    if execution.retry_count >= execution.max_retries:
        raise ValueError(
            "Maximum retry limit has been reached."
        )

    action = execution.workflow_action

    if not action:
        raise ValueError(
            "The workflow action no longer exists."
        )

    if not action.is_active:
        raise ValueError(
            "The workflow action is inactive."
        )

    now = timezone.now()

    if (
        execution.next_retry_at
        and execution.next_retry_at > now
    ):
        raise ValueError(
            "Retry is not available yet."
        )

    execution.retry_count += 1
    execution.last_retry_at = now
    execution.next_retry_at = None
    execution.status = "pending"
    execution.completed_at = None
    execution.error = ""
    execution.save(
        update_fields=[
            "retry_count",
            "last_retry_at",
            "next_retry_at",
            "status",
            "completed_at",
            "error",
        ]
    )

    try:
        result = execute_workflow_action(
            action=action,
            instance=execution.workflow_instance,
            execution=execution,
            user=user,
            ip_address=ip_address,
        )

        _mark_execution(
            execution=execution,
            status="success",
            result=result,
        )

        return {
            "success": True,
            "execution_id": str(execution.pk),
            "retry_count": execution.retry_count,
            **result,
        }

    except Exception as exc:
        error = str(exc)

        if execution.retry_count < execution.max_retries:
            execution.status = "failed"
            execution.error = error
            execution.next_retry_at = (
                timezone.now()
                + timedelta(
                    seconds=_retry_delay(
                        execution.retry_count
                    )
                )
            )
            execution.completed_at = timezone.now()
            execution.save(
                update_fields=[
                    "status",
                    "error",
                    "next_retry_at",
                    "completed_at",
                ]
            )
        else:
            _mark_execution(
                execution=execution,
                status="failed",
                error=error,
            )

        log_action(
            business=execution.workflow_instance.workflow.business,
            user=user,
            action="workflow.action.retry_failed",
            resource="workflow_action",
            object_id=action.pk,
            ip_address=ip_address,
            metadata={
                "workflow_instance_id": str(
                    execution.workflow_instance_id
                ),
                "execution_id": str(
                    execution.pk
                ),
                "retry_count": execution.retry_count,
                "error": error,
            },
        )

        return {
            "success": False,
            "failed": True,
            "execution_id": str(execution.pk),
            "retry_count": execution.retry_count,
            "error": error,
        }


def execute_transition_actions(
    *,
    transition,
    instance,
    user=None,
    ip_address=None,
):
    results = []

    actions = transition.actions.filter(
        is_active=True,
    ).order_by(
        "position",
        "created_at",
    )

    for action in actions:

        execution = (
            WorkflowActionExecution.objects.create(
                workflow_instance=instance,
                workflow_action=action,
                status="pending",
            )
        )

        config = action.config or {}
        execution_mode = str(
            config.get("execution_mode", "sync")
        ).lower()

        if execution_mode == "async":
            execution.queued_at = timezone.now()
            execution.next_retry_at = None
            execution.save(
                update_fields=[
                    "queued_at",
                    "next_retry_at",
                ]
            )

            results.append(
                {
                    "action_id": str(action.pk),
                    "execution_id": str(execution.pk),
                    "success": True,
                    "queued": True,
                }
            )
            continue

        try:

            result = execute_workflow_action(
                action=action,
                instance=instance,
                execution=execution,
                user=user,
                ip_address=ip_address,
            )

            _mark_execution(
                execution=execution,
                status="success",
                result=result,
            )

            results.append(
                {
                    "action_id": str(
                        action.pk
                    ),
                    "execution_id": str(
                        execution.pk
                    ),
                    **result,
                }
            )

        except Exception as exc:

            error = str(exc)

            _mark_execution(
                execution=execution,
                status="failed",
                error=error,
            )

            log_action(
                business=instance.workflow.business,
                user=user,
                action="workflow.action.failed",
                resource="workflow_action",
                object_id=action.pk,
                ip_address=ip_address,
                metadata={
                    "workflow_instance_id": str(
                        instance.pk
                    ),
                    "record_id": str(
                        instance.record_id
                    ),
                    "action_id": str(
                        action.pk
                    ),
                    "error": error,
                },
            )

            results.append(
                {
                    "action_id": str(
                        action.pk
                    ),
                    "execution_id": str(
                        execution.pk
                    ),
                    "success": False,
                    "failed": True,
                    "error": error,
                }
            )

    return results
