from decimal import Decimal, InvalidOperation

from core.models import WorkflowCondition


VALID_OPERATORS = {
    "equals",
    "not_equals",
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
    "contains",
    "is_true",
    "is_false",
}


def _to_decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def evaluate_condition(condition, record):
    """
    Evaluate one workflow condition against an EntityRecord.
    """

    if not condition.is_active:
        return True

    field_slug = condition.field_slug

    if field_slug not in record.data:
        return False

    actual = record.data.get(field_slug)
    expected = condition.value
    operator = condition.operator

    if operator == "equals":
        return actual == expected

    if operator == "not_equals":
        return actual != expected

    if operator == "is_true":
        return actual is True

    if operator == "is_false":
        return actual is False

    if operator == "contains":
        if isinstance(actual, str):
            return str(expected).lower() in actual.lower()

        if isinstance(actual, (list, tuple)):
            return expected in actual

        return False

    actual_number = _to_decimal(actual)
    expected_number = _to_decimal(expected)

    if actual_number is None or expected_number is None:
        return False

    if operator == "greater_than":
        return actual_number > expected_number

    if operator == "greater_than_or_equal":
        return actual_number >= expected_number

    if operator == "less_than":
        return actual_number < expected_number

    if operator == "less_than_or_equal":
        return actual_number <= expected_number

    return False


def evaluate_transition_conditions(transition, record):
    """
    All active conditions must pass.
    """

    conditions = transition.conditions.filter(
        is_active=True
    )

    for condition in conditions:
        if not evaluate_condition(condition, record):
            return False

    return True
