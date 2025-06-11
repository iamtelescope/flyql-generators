import pytest
from flyql.exceptions import FlyqlError
from flyql.constants import Operator
from .helpers import (
    get_value_type,
    validate_operation
)


@pytest.mark.parametrize("value,expected", [
    ("hello", "string"),
    (123, "int"),
    (12.34, "float"),
    (True, "bool"),
    (False, "bool"),
    (None, ""),
    ([], ""),
])
def test_get_value_type(value, expected):
    result = get_value_type(value)
    assert result == expected


@pytest.mark.parametrize("value,field_normalized_type,operator", [
    ("hello", "string", Operator.EQUALS.value),
    ("hello", "string", Operator.EQUALS_REGEX.value),
    (123, "int", Operator.GREATER_THAN.value),
    (12.34, "float", Operator.LOWER_THAN.value),
    (True, "bool", Operator.EQUALS.value),
    ("test", "string", Operator.NOT_EQUALS_REGEX.value),
    (42, "int", Operator.EQUALS.value),
    (3.14, "float", Operator.EQUALS.value),
])
def test_validate_operation_allowed(value, field_normalized_type, operator):
    validate_operation(value, field_normalized_type, operator)


@pytest.mark.parametrize("value,field_normalized_type,operator", [
    # String vs numbers comparison
    (123, "string", Operator.GREATER_THAN.value),
    (12.34, "string", Operator.LOWER_THAN.value),
    (10, "string", Operator.GREATER_OR_EQUALS_THAN.value),
    (5.5, "string", Operator.LOWER_OR_EQUALS_THAN.value),

    # Numbers with regex
    ("test", "int", Operator.EQUALS_REGEX.value),
    ("pattern", "float", Operator.NOT_EQUALS_REGEX.value),

    # Bool with comparison
    (True, "bool", Operator.GREATER_THAN.value),
    (False, "bool", Operator.LOWER_THAN.value),
    (True, "bool", Operator.GREATER_OR_EQUALS_THAN.value),
    (False, "bool", Operator.LOWER_OR_EQUALS_THAN.value),
])
def test_validate_operation_forbidden(value, field_normalized_type, operator):
    with pytest.raises(FlyqlError, match="operation not allowed"):
        validate_operation(value, field_normalized_type, operator)


def test_validate_operation_unknown_type():
    # unknown type bypass
    validate_operation("test", None, Operator.EQUALS.value)
    validate_operation(123, "unknown_type", Operator.GREATER_THAN.value)