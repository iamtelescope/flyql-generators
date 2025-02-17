# FlyQL to ClickHouse SQL generator

Documentation for FlyQL itself can be found in the FlyQL [repository](https://github.com/iamtelescope/flyql/blob/main/README.md).

## Operators and Their SQL Transformation

### Operators `=` (EQUALS) and `!=` (NOT EQUALS)

If the value of the operator contains `*` (asterisk) and it is not escaped, it results in SQL generation using `LIKE`. For example:

```flyql
key=val*ue
```

Transforms into SQL:

```sql
WHERE key LIKE 'val%ue'
```

Similarly:

```flyql
key!=val*ue
```

Transforms into SQL:

```sql
WHERE key NOT LIKE 'val%ue'
```

### Operators `=~` (REGEX) and `!~` (NOT REGEX)

If the `=~` operator is used, it is converted into the ClickHouse `match()` function:

FlyQL:
```flyql
key=~regex_pattern
```

Transforms into SQL:

```sql
WHERE match(key, 'regex_pattern')
```

If the `!~` operator is used, it is converted into `NOT match()`:

FlyQL:
```flyql
key!~regex_pattern
```

Transforms into SQL:

```sql
WHERE NOT match(key, 'regex_pattern')
```

## Interpretation of Keys with a Colon (`:`)

If a key contains a colon (`:`), it is interpreted as a JSONPath. For example:

**FlyQL:**
```flyql
data:field=value
```

Transforms into SQL:

```sql
WHERE JSONExtractString(data, 'field') = 'value'
```

Similarly, for all the operators described above, if the key contains a colon, the transformation will be applied using ClickHouse's `JSONExtract*` functions.

### Support for `Map` and `Array` Types

- **Map Support**: Single-level maps (`Map(key, value)`) are supported. If the values contain another map, it cannot be accessed in the same way.
- **Array Support**: Accessing array elements by index is supported. If an array contains nested arrays, only the first level can be accessed.

## Examples

FlyQL:
```flyql
host=localhost
```

Transforms into SQL:

```sql
WHERE host = 'localhost'
```
---
FlyQL:
```flyql
host=localhost and message=2024* or (host=remote and message=2025*)
```

Transforms into SQL:

```sql
WHERE ((host = 'localhost' AND message LIKE '2024%') OR (host = 'remote' AND message LIKE '2025%'))
```
---
FlyQL:
```flyql
host=local*t
```

Transforms into SQL:

```sql
WHERE host LIKE 'local%t'
```
---
FlyQL:
```flyql
host!=localhost
```

Transforms into SQL:

```sql
WHERE host != 'localhost'
```
---
FlyQL:
```flyql
host!=local*t
```

Transforms into SQL:

```sql
WHERE host NOT LIKE 'local%t'
```
---
FlyQL:
```flyql
host=~local.*t
```

Transforms into SQL:

```sql
WHERE match(host, 'local.*t')
```
---
FlyQL:
```flyql
host!~local.*t
```

Transforms into SQL:

```sql
WHERE NOT match(host, 'local.*t')
```
---
FlyQL:
```flyql
rest:bytes=25
```

Transforms into SQL:

```sql
WHERE multiIf(JSONType(rest, 'bytes') = 'String', equals(JSONExtractString(rest, 'bytes'), '25'),
              JSONType(rest, 'bytes') = 'Int64', equals(JSONExtractInt(rest, 'bytes'), 25),
              JSONType(rest, 'bytes') = 'Double', equals(JSONExtractFloat(rest, 'bytes'), 25),
              JSONType(rest, 'bytes') = 'Bool', equals(JSONExtractBool(rest, 'bytes'), 25),
              0)
```
---
FlyQL:
```flyql
rest:bytes>=33
```

Transforms into SQL:

```sql
WHERE multiIf(JSONType(rest, 'bytes') = 'String', greaterOrEquals(JSONExtractString(rest, 'bytes'), '33'),
              JSONType(rest, 'bytes') = 'Int64', greaterOrEquals(JSONExtractInt(rest, 'bytes'), 33),
              JSONType(rest, 'bytes') = 'Double', greaterOrEquals(JSONExtractFloat(rest, 'bytes'), 33),
              JSONType(rest, 'bytes') = 'Bool', greaterOrEquals(JSONExtractBool(rest, 'bytes'), 33),
              0)
```
