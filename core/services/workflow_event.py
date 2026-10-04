"""
IndusCMS Phase 4.4B: Workflow Event Dispatcher.

Dispatches entity-record events to matching active workflow triggers.
Trigger failures are isolated so they do not undo record operations.
"""

import logging

from django.db import IntegrityError, transaction
from django.utils import timezone

from core.models import (
    AuditLog,
    WorkflowDefinition,
    WorkflowHistory,
    WorkflowInstance,
    WorkflowStep,
    WorkflowTrigger,
)

logger = logging.getLogger(__name__)

VALID_EVENT_TYPES = {
    "record_created",
    "record_updated",
    "record_deleted",
}


def _audit(business, action, record, user=None, metadata=None):
    """Write an audit entry without breaking event processing."""
    try:
        AuditLog.objects.create(
            business=business,
            user=user,
            action=action,
            resource="workflow",
            object_id=str(record.pk),
            metadata=metadata or {},
        )
    except Exception:
        logger.exception("Workflow event audit failed: %s", action)


def _start_from_trigger(workflow, record, user, event_type):
    """
    Start a workflow through the trusted internal event path.

    Normal API permission checks remain unchanged. This function is only
    called by the internal dispatcher for an active workflow trigger.
    """
    existing = WorkflowInstance.objects.filter(
        workflow=workflow,
        record=record,
    ).first()

    if existing:
        return existing, False

    initial_step = WorkflowStep.objects.filter(
        workflow=workflow,
        is_initial=True,
        is_active=True,
    ).first()

    if initial_step is None:
        raise ValueError(
            f"Workflow '{workflow.name}' has no active initial step."
        )

    # Recheck the workflow immediately before starting it.
    if not workflow.is_active:
        return None, False

    try:
        with transaction.atomic():
            instance, created = WorkflowInstance.objects.get_or_create(
                workflow=workflow,
                record=record,
                defaults={
                    "current_step": initial_step,
                    "status": "active",
                    "started_by": user,
                },
            )

            if not created:
                return instance, False

            WorkflowHistory.objects.create(
                instance=instance,
                transition=None,
                from_step=None,
                to_step=initial_step,
                action="started",
                performed_by=user,
                note=f"Started by event trigger: {event_type}",
            )

            return instance, True

    except IntegrityError:
        # Another request may have started the same workflow concurrently.
        existing = WorkflowInstance.objects.filter(
            workflow=workflow,
            record=record,
        ).first()

        if existing:
            return existing, False
        raise


def dispatch_record_event(record, event_type, user=None):
    """
    Dispatch an event for an EntityRecord.

    Returns a summary containing started, skipped and failed counts.
    Existing workflow instances are not started again.
    """
    if event_type not in VALID_EVENT_TYPES:
        raise ValueError(
            f"Unsupported event_type '{event_type}'. "
            f"Expected one of: {', '.join(sorted(VALID_EVENT_TYPES))}"
        )

    summary = {
        "event_type": event_type,
        "record_id": str(record.pk),
        "matched": 0,
        "started": 0,
        "skipped": 0,
        "failed": 0,
        "errors": [],
    }

    # A deleted record is allowed here only because this is the trusted
    # internal event path. Normal record APIs retain their own safeguards.
    triggers = WorkflowTrigger.objects.filter(
        event_type=event_type,
        is_active=True,
        workflow__is_active=True,
        workflow__entity_id=record.entity_id,
    ).select_related(
        "workflow",
        "workflow__entity",
    ).order_by("created_at", "id")

    for trigger in triggers:
        summary["matched"] += 1
        workflow = trigger.workflow

        try:
            # Optional trigger config can restrict the event to records
            # whose data matches a configured field/value.
            config = trigger.config or {}
            field = config.get("field")
            expected = config.get("equals")

            if field is not None and record.data.get(field) != expected:
                summary["skipped"] += 1
                continue

            instance, created = _start_from_trigger(
                workflow=workflow,
                record=record,
                user=user,
                event_type=event_type,
            )

            if created:
                summary["started"] += 1
                _audit(
                    business=record.entity.business,
                    action="workflow.trigger.fired",
                    record=record,
                    user=user,
                    metadata={
                        "trigger_id": str(trigger.pk),
                        "workflow_id": str(workflow.pk),
                        "instance_id": str(instance.pk),
                        "event_type": event_type,
                    },
                )
            else:
                summary["skipped"] += 1

        except Exception as exc:
            # One broken workflow must not prevent other triggers running.
            summary["failed"] += 1
            summary["errors"].append({
                "trigger_id": str(trigger.pk),
                "workflow_id": str(workflow.pk),
                "error": str(exc),
            })
            logger.exception(
                "Workflow trigger %s failed for record %s",
                trigger.pk,
                record.pk,
            )

    return summary


def schedule_record_event(record, event_type, user=None):
    """
    Dispatch after the surrounding record transaction commits.

    Exceptions are contained so workflow automation cannot undo a saved
    record or cause a successful record API request to fail.
    """
    record_id = str(record.pk)

    def _dispatch_after_commit():
        try:
            # Refresh so the dispatcher sees the committed record state.
            from core.models import EntityRecord

            committed_record = EntityRecord.objects.get(pk=record_id)
            dispatch_record_event(
                record=committed_record,
                event_type=event_type,
                user=user,
            )
        except Exception:
            logger.exception(
                "Unable to dispatch %s for record %s",
                event_type,
                record_id,
            )

    transaction.on_commit(_dispatch_after_commit)
