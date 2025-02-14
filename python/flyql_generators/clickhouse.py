from enum import Enum
from typing import List, Mapping, Optional, Tuple

from clickhouse_driver.util.escape import escape_param

from flyql.exceptions import FlyqlError
from flyql.expression import Expression
from flyql.constants import Operator
from flyql.tree import Node


OPERATOR_TO_CLICKHOUSE_FUNC = {
    Operator.EQUALS.value: "equals",
    Operator.NOT_EQUALS.value: "notEquals",
    Operator.EQUALS_REGEX.value: "match",
    Operator.NOT_EQUALS_REGEX.value: "match",
    Operator.GREATER_THAN.value: "greater",
    Operator.LOWER_THAN.value: "less",
    Operator.GREATER_OR_EQUALS_THAN.value: "greaterOrEquals",
    Operator.LOWER_OR_EQUALS_THAN.value: "lessOrEquals",
}

LIKE_PATTERN_CHAR = "*"
SQL_LIKE_PATTERN_CHAR = "%"


class Field:
    def __init__(
        self,
        name: str,
        jsonstring: bool,
        values: List[str] = [],
    ):
        self.jsonstring = jsonstring
        self.name = name
        self.values = values


def is_number(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        try:
            int(value)
        except ValueError:
            return False
        else:
            return True
    else:
        return True


def prepare_like_pattern_value(value: str) -> Tuple[bool, str]:
    pattern_found = False
    new_value = ""
    for idx, char in enumerate(value):
        if char == LIKE_PATTERN_CHAR:
            if idx == 0:
                new_value += SQL_LIKE_PATTERN_CHAR
                pattern_found = True
            else:
                if value[idx - 1] == "\\":
                    new_value += LIKE_PATTERN_CHAR
                else:
                    new_value += SQL_LIKE_PATTERN_CHAR
                    pattern_found = True
        elif char == SQL_LIKE_PATTERN_CHAR:
            pattern_found = True
            new_value += "\\"
            new_value += SQL_LIKE_PATTERN_CHAR
        else:
            new_value += char
    return pattern_found, new_value


def expression_to_sql(expression: Expression, fields: Mapping[str, Field]) -> str:
    text = ""

    if ":" in expression.key:
        spl = expression.key.split(":")
        field_name = spl[0]
        if field_name not in fields:
            raise FlyqlError(f"unknown field: {field_name}")
        field = fields[field_name]
        if not field.jsonstring:
            raise FlyqlError("json for non json")

        json_path = spl[1:]
        json_path = ", ".join([escape_param(x, context=None) for x in json_path])

        func = OPERATOR_TO_CLICKHOUSE_FUNC[expression.operator]
        str_value = escape_param(expression.value, context=None)
        multi_if = [
            f"JSONType({field.name}, {json_path}) = 'String', {func}(JSONExtractString({field.name}, {json_path}), {str_value})"
        ]
        if is_number(expression.value) and expression.operator not in [
            Operator.EQUALS_REGEX.value,
            Operator.NOT_EQUALS_REGEX.value,
        ]:
            multi_if.extend(
                [
                    f"JSONType({field.name}, {json_path}) = 'Int64', {func}(JSONExtractInt({field.name}, {json_path}), {expression.value})",
                    f"JSONType({field.name}, {json_path}) = 'Double', {func}(JSONExtractFloat({field.name}, {json_path}), {expression.value})",
                    f"JSONType({field.name}, {json_path}) = 'Bool', {func}(JSONExtractBool({field.name}, {json_path}), {expression.value})",
                ]
            )
        multi_if.append("0")
        multi_if_str = ",".join(multi_if)
        reverse_operator = ""
        if expression.operator == Operator.NOT_EQUALS_REGEX.value:
            reverse_operator = "not "
        text = f"{reverse_operator}multiIf({multi_if_str})"
    else:
        if expression.key not in fields:
            raise FlyqlError(f"unknown field: {expression.key}")

        field = fields[expression.key]
        values = field.values
        operator = expression.operator

        if field.values and expression.value not in field.values:
            raise FlyqlError(f"unnown value: {expression.value}")

        value = escape_param(expression.value, context=None)
        if expression.operator == Operator.EQUALS_REGEX.value:
            text = f"match({field.name}, {value})"
        elif expression.operator == Operator.NOT_EQUALS_REGEX.value:
            text = f"not match({field.name}, {value})"
        elif expression.operator in [Operator.EQUALS.value, Operator.NOT_EQUALS.value]:
            operator = expression.operator
            is_like_pattern, value = prepare_like_pattern_value(expression.value)
            value = escape_param(value, context=None)
            if is_like_pattern:
                if expression.operator == Operator.EQUALS.value:
                    operator = "LIKE"
                else:
                    operator = "NOT LIKE"
            text = f"{field.name} {operator} {value}"
        else:
            text = f"{field.name} {expression.operator} {value}"
    return text


def to_sql(root: Node, fields: Mapping[str, Field]) -> str:
    """
    Returns ClickHouse WHERE clause for given tree and fields
    """
    left = ""
    right = ""
    text = ""

    if root.expression is not None:
        text = expression_to_sql(expression=root.expression, fields=fields)

    if root.left is not None:
        left = to_sql(root=root.left, fields=fields)

    if root.right is not None:
        right = to_sql(root=root.right, fields=fields)

    if len(left) > 0 and len(right) > 0:
        text = f"({left} {root.bool_operator} {right})"
    elif len(left) > 0:
        text = left
    elif len(right) > 0:
        text = right

    return text
