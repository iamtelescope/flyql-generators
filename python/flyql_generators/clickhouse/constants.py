NORMALIZED_TYPE_STRING = 'string'
NORMALIZED_TYPE_INT = 'int'
NORMALIZED_TYPE_FLOAT = 'float'
NORMALIZED_TYPE_BOOL = 'bool'
NORMALIZED_TYPE_DATE = 'date'
NORMALIZED_TYPE_ARRAY = 'array'
NORMALIZED_TYPE_MAP = 'map'
NORMALIZED_TYPE_TUPLE = 'tuple'
NORMALIZED_TYPE_GEOMETRY = 'geometry'
NORMALIZED_TYPE_INTERVAL = 'interval'
NORMALIZED_TYPE_SPECIAL = 'special'

NORMALIZED_TYPE_TO_CLICKHOUSE_TYPES = {
    NORMALIZED_TYPE_STRING: {
        'string', 'fixedstring', 'longtext', 'mediumtext', 'tinytext', 'text',
        'longblob', 'mediumblob', 'tinyblob', 'blob', 'varchar', 'char',
        'char large object', 'char varying', 'character', 'character large object',
        'character varying', 'nchar large object', 'nchar varying',
        'national character large object', 'national character varying',
        'national char varying', 'national character', 'national char',
        'binary large object', 'binary varying', 'clob', 'nchar', 'nvarchar',
        'varchar2', 'binary', 'varbinary', 'bytea', 'uuid', 'ipv4', 'ipv6',
        'enum8', 'enum16', 'json'
    },
    NORMALIZED_TYPE_INT: {
        'int8', 'int16', 'int32', 'int64', 'int128', 'int256',
        'uint8', 'uint16', 'uint32', 'uint64', 'uint128', 'uint256',
        'tinyint', 'smallint', 'mediumint', 'int', 'integer', 'bigint',
        'tinyint signed', 'tinyint unsigned', 'smallint signed', 'smallint unsigned',
        'mediumint signed', 'mediumint unsigned', 'int signed', 'int unsigned',
        'integer signed', 'integer unsigned', 'bigint signed', 'bigint unsigned',
        'int1', 'int1 signed', 'int1 unsigned', 'byte', 'signed', 'unsigned',
        'bit', 'set', 'time'
    },
    NORMALIZED_TYPE_FLOAT: {
        'float32', 'float64', 'float', 'double', 'double precision', 'real',
        'decimal', 'decimal32', 'decimal64', 'decimal128', 'decimal256',
        'dec', 'numeric', 'fixed', 'single'
    },
    NORMALIZED_TYPE_BOOL: {'bool', 'boolean'},
    NORMALIZED_TYPE_DATE: {
        'date', 'date32', 'datetime', 'datetime32', 'datetime64', 'timestamp',
        'year'
    },
    NORMALIZED_TYPE_INTERVAL: {
        'intervalday', 'intervalhour', 'intervalmicrosecond', 'intervalmillisecond',
        'intervalminute', 'intervalmonth', 'intervalnanosecond', 'intervalquarter',
        'intervalsecond', 'intervalweek', 'intervalyear'
    },
    NORMALIZED_TYPE_GEOMETRY: {'geometry', 'point', 'polygon', 'multipolygon', 'linestring', 'ring'},
    NORMALIZED_TYPE_SPECIAL: {'nothing', 'nested', 'object', 'dynamic', 'variant'},
}
