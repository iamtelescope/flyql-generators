import pytest
from .field import Field, normalize_clickhouse_type


@pytest.mark.parametrize("input_type,expected", [
    ("String", "string"),
    ("Nullable(String)", "string"),
    ("LowCardinality(String)", "string"),
    ("VARCHAR(255)", "string"),
    ("CHAR(10)", "string"),
    ("TEXT", "string"),
    ("UUID", "string"),
    ("IPv4", "string"),
    ("Int64", "int"),
    ("UInt32", "int"),
    ("Nullable(Int8)", "int"),
    ("TINYINT", "int"),
    ("BIGINT(20)", "int"),
    ("Float64", "float"),
    ("Decimal(10,2)", "float"),
    ("DOUBLE PRECISION", "float"),
    ("Bool", "bool"),
    ("Boolean", "bool"),
    ("Date", "date"),
    ("DateTime64(3)", "date"),
    ("TIMESTAMP", "date"),
    ("Array(String)", "array"),
    ("Map(String, Int64)", "map"),
    ("Tuple(String, Int64)", "tuple"),
    ("Point", "geometry"),
    ("IntervalDay", "interval"),
    ("Nothing", "special"),
    ("UnknownType", None),
    ("", None),
])
def test_normalize_clickhouse_type(input_type, expected):
    result = normalize_clickhouse_type(input_type)
    assert result == expected


class TestField:

    def test_field_creation_basic(self):
        field = Field("test_field", False, "String")
        assert field.name == "test_field"
        assert field.jsonstring is False
        assert field.type == "String"
        assert field.values == []
        assert field.normalized_type == "string"
        assert field.is_map is False
        assert field.is_array is False

    def test_field_creation_with_values(self):
        values = ["value1", "value2"]
        field = Field("enum_field", False, "Enum8", values)
        assert field.values == values

    def test_field_creation_nullable_string(self):
        field = Field("nullable_field", False, "Nullable(String)")
        assert field.normalized_type == "string"
        assert field.is_map is False
        assert field.is_array is False

    def test_field_creation_map(self):
        field = Field("map_field", False, "Map(String, Int64)")
        assert field.normalized_type == "map"
        assert field.is_map is True
        assert field.is_array is False

    def test_field_creation_array(self):
        field = Field("array_field", False, "Array(String)")
        assert field.normalized_type == "array"
        assert field.is_map is False
        assert field.is_array is True

    def test_field_creation_json_field(self):
        field = Field("json_field", True, "String")
        assert field.jsonstring is True
        assert field.normalized_type == "string"

    def test_field_creation_int_types(self):
        int_types = ["Int64", "UInt32", "BIGINT", "Nullable(Int8)"]
        for int_type in int_types:
            field = Field("int_field", False, int_type)
            assert field.normalized_type == "int"
            assert field.is_map is False
            assert field.is_array is False

    def test_field_creation_float_types(self):
        float_types = ["Float64", "Decimal(10,2)", "DOUBLE PRECISION"]
        for float_type in float_types:
            field = Field("float_field", False, float_type)
            assert field.normalized_type == "float"

    def test_field_creation_json(self):
        field = Field("json_field", False, "JSON")
        assert field.normalized_type == "json"
        assert field.is_json is True
        assert field.is_map is False
        assert field.is_array is False

    def test_field_creation_json_with_params(self):
        field = Field("json_field", False, "JSON(a.b UInt32)")
        assert field.normalized_type == "json"
        assert field.is_json is True

    def test_field_values_empty_list(self):
        field = Field("test", False, "String", [])
        assert field.values == []

    def test_field_creation_unknown_type(self):
        field = Field("unknown_field", False, "SomeUnknownType")
        assert field.normalized_type is None
        assert field.is_map is False
        assert field.is_array is False
        assert field.is_json is False