import pytest
from flyql.exceptions import FlyqlError
from flyql.expression import Expression
from flyql.constants import Operator
from flyql.tree import Node
from .field import Field
from .generator import (
    expression_to_sql,
    to_sql,
    escape_param,
    is_number,
    prepare_like_pattern_value
)


@pytest.fixture
def fields():
    return {
        "message": Field("message", False, "String"),
        "count": Field("count", False, "Int64"),
        "price": Field("price", False, "Float64"),
        "active": Field("active", False, "Bool"),
        "created_at": Field("created_at", False, "Date"),
        "json_field": Field("json_field", True, "String"),
        "tags": Field("tags", False, "Array(String)"),
        "metadata": Field("metadata", False, "Map(String, String)"),
        "enum_field": Field("enum_field", False, "Enum8", ["value1", "value2"]),
    }


class TestEscapeParam:

    def test_escape_string(self):
        assert escape_param("hello") == "'hello'"
        assert escape_param("test'quote") == "'test\\'quote'"
        assert escape_param("test\\backslash") == "'test\\\\backslash'"
        assert escape_param("test\nNewline") == "'test\\nNewline'"

    def test_escape_none(self):
        assert escape_param(None) == "NULL"

    def test_escape_numbers(self):
        assert escape_param(123) == "123"
        assert escape_param(12.34) == "12.34"
        assert escape_param(True) == "True"
        assert escape_param(False) == "False"


class TestIsNumber:

    def test_is_number_string(self):
        assert is_number("123") is True
        assert is_number("12.34") is True
        assert is_number("-5") is True
        assert is_number("hello") is False
        assert is_number("") is False

    def test_is_number_actual_numbers(self):
        assert is_number(123) is True
        assert is_number(12.34) is True
        assert is_number(-5) is True

    def test_is_number_other_types(self):
        assert is_number(None) is False
        assert is_number([]) is False


class TestPrepareLikePattern:

    def test_no_pattern(self):
        pattern_found, result = prepare_like_pattern_value("hello")
        assert pattern_found is False
        assert result == "hello"

    def test_star_pattern(self):
        pattern_found, result = prepare_like_pattern_value("hello*")
        assert pattern_found is True
        assert result == "hello%"

    def test_multiple_stars(self):
        pattern_found, result = prepare_like_pattern_value("*hello*world*")
        assert pattern_found is True
        assert result == "%hello%world%"

    def test_escaped_star(self):
        pattern_found, result = prepare_like_pattern_value("hello\\*world")
        assert pattern_found is False
        assert result == "hello\\*world"

    def test_percent_escaping(self):
        pattern_found, result = prepare_like_pattern_value("hello%world")
        assert pattern_found is True
        assert result == "hello\\%world"


class TestExpressionToSQL:

    def test_string_equals(self, fields):
        expr = Expression("message", Operator.EQUALS.value, "hello", True)
        result = expression_to_sql(expr, fields)
        assert result == "message = 'hello'"

    def test_string_not_equals(self, fields):
        expr = Expression("message", Operator.NOT_EQUALS.value, "hello", True)
        result = expression_to_sql(expr, fields)
        assert result == "message != 'hello'"

    def test_string_regex(self, fields):
        expr = Expression("message", Operator.EQUALS_REGEX.value, "test.*", True)
        result = expression_to_sql(expr, fields)
        assert result == "match(message, 'test.*')"

    def test_string_not_regex(self, fields):
        expr = Expression("message", Operator.NOT_EQUALS_REGEX.value, "test.*", True)
        result = expression_to_sql(expr, fields)
        assert result == "not match(message, 'test.*')"

    def test_int_comparison(self, fields):
        expr = Expression("count", Operator.GREATER_THAN.value, 10, False)
        result = expression_to_sql(expr, fields)
        assert result == "count > 10.0"

    def test_float_comparison(self, fields):
        expr = Expression("price", Operator.LOWER_THAN.value, 99.99, False)
        result = expression_to_sql(expr, fields)
        assert result == "price < 99.99"

    def test_bool_equals(self, fields):
        expr = Expression("active", Operator.EQUALS.value, True, False)
        result = expression_to_sql(expr, fields)
        assert result == "active = '1.0'"

    def test_like_pattern(self, fields):
        expr = Expression("message", Operator.EQUALS.value, "hello*", True)
        result = expression_to_sql(expr, fields)
        assert result == "message LIKE 'hello%'"

    def test_not_like_pattern(self, fields):
        expr = Expression("message", Operator.NOT_EQUALS.value, "hello*", True)
        result = expression_to_sql(expr, fields)
        assert result == "message NOT LIKE 'hello%'"

    def test_enum_field_valid_value(self, fields):
        expr = Expression("enum_field", Operator.EQUALS.value, "value1", True)
        result = expression_to_sql(expr, fields)
        assert result == "enum_field = 'value1'"

    def test_enum_field_invalid_value(self, fields):
        expr = Expression("enum_field", Operator.EQUALS.value, "invalid", True)
        with pytest.raises(FlyqlError, match="unknown value"):
            expression_to_sql(expr, fields)

    def test_unknown_field(self, fields):
        expr = Expression("unknown_field", Operator.EQUALS.value, "test", True)
        with pytest.raises(FlyqlError, match="unknown field"):
            expression_to_sql(expr, fields)

    def test_forbidden_operation(self, fields):
        expr = Expression("count", Operator.EQUALS_REGEX.value, "test", True)
        with pytest.raises(FlyqlError, match="operation not allowed"):
            expression_to_sql(expr, fields)


class TestJSONFields:

    def test_json_field_string_extraction(self, fields):
        expr = Expression("json_field:name", Operator.EQUALS.value, "test", True)
        result = expression_to_sql(expr, fields)
        expected = "multiIf(JSONType(json_field, 'name') = 'String', equals(JSONExtractString(json_field, 'name'), 'test'),0)"
        assert result == expected

    def test_json_field_nested_path(self, fields):
        expr = Expression("json_field:user:name", Operator.EQUALS.value, "john", True)
        result = expression_to_sql(expr, fields)
        expected = "multiIf(JSONType(json_field, 'user', 'name') = 'String', equals(JSONExtractString(json_field, 'user', 'name'), 'john'),0)"
        assert result == expected

    def test_json_field_number_value(self, fields):
        expr = Expression("json_field:age", Operator.EQUALS.value, 25, False)
        result = expression_to_sql(expr, fields)
        assert "JSONExtractInt" in result
        assert "JSONExtractFloat" in result
        assert "JSONExtractBool" in result


class TestMapFields:

    def test_map_field_access(self, fields):
        expr = Expression("metadata:key1", Operator.EQUALS.value, "value1", True)
        result = expression_to_sql(expr, fields)
        assert result == "equals(metadata['key1'], 'value1')"

    def test_map_field_nested_key(self, fields):
        expr = Expression("metadata:nested:key", Operator.EQUALS.value, "value", True)
        result = expression_to_sql(expr, fields)
        assert result == "equals(metadata['nested:key'], 'value')"


class TestArrayFields:

    def test_array_field_access(self, fields):
        expr = Expression("tags:0", Operator.EQUALS.value, "tag1", True)
        result = expression_to_sql(expr, fields)
        assert result == "equals(tags[0], 'tag1')"

    def test_array_field_invalid_index(self, fields):
        expr = Expression("tags:invalid", Operator.EQUALS.value, "tag1", True)
        with pytest.raises(FlyqlError, match="invalid array index"):
            expression_to_sql(expr, fields)


class TestTreeToSQL:

    def test_simple_expression(self, fields):
        expr = Expression("message", Operator.EQUALS.value, "hello", True)
        node = Node("", expr, None, None)
        result = to_sql(node, fields)
        assert result == "message = 'hello'"

    def test_and_operation(self, fields):
        left_expr = Expression("message", Operator.EQUALS.value, "hello", True)
        right_expr = Expression("count", Operator.GREATER_THAN.value, 10, False)

        left_node = Node("", left_expr, None, None)
        right_node = Node("", right_expr, None, None)
        root_node = Node("and", None, left_node, right_node)

        result = to_sql(root_node, fields)
        assert result == "(message = 'hello' and count > 10.0)"

    def test_or_operation(self, fields):
        left_expr = Expression("message", Operator.EQUALS.value, "hello", True)
        right_expr = Expression("message", Operator.EQUALS.value, "world", True)

        left_node = Node("", left_expr, None, None)
        right_node = Node("", right_expr, None, None)
        root_node = Node("or", None, left_node, right_node)

        result = to_sql(root_node, fields)
        assert result == "(message = 'hello' or message = 'world')"

    def test_complex_tree(self, fields):
        expr1 = Expression("message", Operator.EQUALS.value, "hello", True)
        expr2 = Expression("count", Operator.GREATER_THAN.value, 10, False)
        expr3 = Expression("active", Operator.EQUALS.value, True, False)

        node1 = Node("", expr1, None, None)
        node2 = Node("", expr2, None, None)
        node3 = Node("", expr3, None, None)

        and_node = Node("and", None, node1, node2)
        root_node = Node("or", None, and_node, node3)

        result = to_sql(root_node, fields)
        assert result == "((message = 'hello' and count > 10.0) or active = '1.0')"


@pytest.mark.parametrize("field_name,operator,value,value_is_string,expected", [
    ("message", Operator.EQUALS.value, "test", True, "message = 'test'"),
    ("count", Operator.NOT_EQUALS.value, 42, False, "count != '42.0'"),
    ("price", Operator.GREATER_OR_EQUALS_THAN.value, 10.5, False, "price >= 10.5"),
    ("active", Operator.EQUALS.value, True, False, "active = '1.0'"),
    ("created_at", Operator.LOWER_OR_EQUALS_THAN.value, "2023-01-01", True, "created_at <= '2023-01-01'"),
])
def test_various_field_operations(fields, field_name, operator, value, value_is_string, expected):
    expr = Expression(field_name, operator, value, value_is_string)
    result = expression_to_sql(expr, fields)
    assert result == expected
