import os
import socket
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import WorkflowActionExecution
from core.services.workflow_action import execute_workflow_action


DEFAULT_LIMIT = 10
STALE_MINUTES = 15


def get_worker_id():
    return f"{socket.gethostname()}:{os.getpid()}"


def get_pending_executions(limit=DEFAULT_LIMIT):
    now = timezone.now()

    return (
        WorkflowActionExecution.objects
        .select_related(
            "workflow_action",
            "workflow_instance",
            "workflow_instance__workflow",
            "workflow_instance__record",
        )
        .filter(
            status="pending",
            workflow_action__is_active=True,
        )
        .filter(
            next_retry_at__isnull=True,
        )
        .order_by("queued_at", "started_at")[:limit]
    )


def recover_stale_executions(minutes=STALE_MINUTES):
    cutoff = timezone.now() - timedelta(minutes=minutes)

    return WorkflowActionExecution.objects.filter(
        status="running",
        claimed_at__lt=cutoff,
    ).update(
        status="pending",
        worker_id="",
        claimed_at=None,
    )


def claim_execution(execution, worker_id=None):
    worker_id = worker_id or get_worker_id()

    with transaction.atomic():
        claimed = (
            WorkflowActionExecution.objects
            .select_for_update()
            .filter(
                pk=execution.pk,
                status="pending",
            )
            .first()
        )

        if claimed is None:
            return None

        claimed.status = "running"
        claimed.claimed_at = timezone.now()
        claimed.worker_id = worker_id
        claimed.save(
            update_fields=[
                "status",
                "claimed_at",
                "worker_id",
            ]
        )

        return claimed


def process_execution(execution, worker_id=None):
    claimed = claim_execution(
        execution,
        worker_id=worker_id,
    )

    if claimed is None:
        return {
            "success": False,
            "skipped": True,
            "reason": "Execution was already claimed.",
        }

    try:
        result = execute_workflow_action(
            action=claimed.workflow_action,
            instance=claimed.workflow_instance,
            execution=claimed,
        )

        claimed.status = "success"
        claimed.completed_at = timezone.now()
        claimed.result = result or {}
        claimed.error = ""
        claimed.save(
            update_fields=[
                "status",
                "completed_at",
                "result",
                "error",
            ]
        )

        return result or {"success": True}

    except Exception as exc:
        claimed.status = "failed"
        claimed.completed_at = timezone.now()
        claimed.error = str(exc)
        claimed.save(
            update_fields=[
                "status",
                "completed_at",
                "error",
            ]
        )

        return {
            "success": False,
            "error": str(exc),
        }


def process_pending(limit=DEFAULT_LIMIT, worker_id=None):
    recover_stale_executions()

    executions = list(
        get_pending_executions(limit=limit)
    )

    results = []

    for execution in executions:
        results.append(
            process_execution(
                execution,
                worker_id=worker_id,
            )
        )

    return results
