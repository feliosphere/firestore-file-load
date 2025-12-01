# 🔢 Type System Reference

Complete guide to Firestore data type conversion in FirestoreFileLoad.

## Table of Contents

1. [Overview](#overview)
2. [Type Definition Methods](#type-definition-methods)
3. [Automatic Detection](#automatic-detection)
4. [All Data Types](#all-data-types)
5. [Complete Prefix Reference](#complete-prefix-reference)
6. [Special Cases](#special-cases)

## Overview

FirestoreFileLoad supports all 10 Firestore data types with 23 recognized type keywords for maximum flexibility.

### Three Ways to Specify Types

1. **Column Header Hints**: `age:int` - Apply type to entire column
2. **Value-Level Prefixes**: `int: 25` - Override specific values
3. **Auto-Detection**: `25` - Let the tool infer the type

### Type Precedence

When multiple type specifications exist, the tool follows this priority (highest to lowest):

1. **Quoted values** in CSV → Always treated as strings
2. **Value-level prefix** (`str: 123`) → Overrides everything
3. **Column header hint** (`age:int`) → Overrides auto-detection
4. **Auto-detection** → Fallback based on value pattern

## Type Definition Methods

### Method 1: Column Header Hints

Define the type for an entire column by appending `:type` to the column name.

**Format**: `column_name:type`

**Example**:
```csv
DocumentId,age:int,score:float,active:bool,name
user1,25,95.5,true,John
user2,30,88.0,false,Jane
```

All values in the `age` column are converted to integers, `score` to floats, and `active` to booleans.

**Supported Types**:
- `int`, `integer`
- `float`, `double`
- `str`, `string`, `text`
- `bool`, `boolean`
- `timestamp`, `datetime`, `date`
- `geopoint`, `geo`, `location`
- `array`, `list`
- `map`, `dict`, `object`
- `bytes`
- `ref`, `reference`
- `null`, `none`

### Method 2: Value-Level Prefixes

Override the type for specific values using `type: value` format.

**Format**: `type: value`

**Example**:
```csv
DocumentId,phone,age,code
user1,str: 5551234567,int: 25,str: 00123
user2,str: 5559876543,int: 30,str: 00456
```

- `str: 5551234567` → `"5551234567"` (string, preserves all digits)
- `int: 25` → `25` (integer)
- `str: 00123` → `"00123"` (string, preserves leading zeros)

### Method 3: Automatic Detection

Let the tool automatically detect types based on value patterns.

**Example**:
```csv
DocumentId,age,score,active,created_at,name
user1,25,95.5,true,2025-01-15T10:30:00,John
user2,30,88.0,false,2025-01-14T09:00:00,Jane
```

**Detection Results**:
- `25`, `30` → Integers
- `95.5`, `88.0` → Floats
- `true`, `false` → Booleans
- `2025-01-15T10:30:00` → Timestamp (ISO 8601)
- `John`, `Jane` → Strings

## Automatic Detection

The tool analyzes each value and applies the first matching pattern:

### Detection Order

1. **Null**: `null`, `NULL`, `None`, `none`, empty string → `None`
2. **Boolean**: `true`, `false`, `yes`, `no`, `y`, `n` (case-insensitive) → `True`/`False`
3. **Integer**: All digits, optional minus sign → `int`
4. **Float**: Contains decimal point or scientific notation → `float`
5. **Timestamp**: ISO 8601 format (contains `T` or 2+ hyphens) → `datetime`
6. **String**: Everything else → `str` (fallback)

### Detection Examples

| Input Value | Detected Type | Result |
|-------------|---------------|---------|
| `42` | Integer | `42` |
| `-10` | Integer | `-10` |
| `3.14` | Float | `3.14` |
| `1.0` | Float | `1.0` |
| `1e5` | Float | `100000.0` |
| `true` | Boolean | `True` |
| `false` | Boolean | `False` |
| `yes` | Boolean | `True` |
| `no` | Boolean | `False` |
| `null` | Null | `None` |
| `NULL` | Null | `None` |
| `` (empty) | Null | `None` |
| `2025-01-15T10:30:00` | Timestamp | datetime object |
| `2025-01-15` | Timestamp | datetime object |
| `Hello World` | String | `"Hello World"` |
| `00123` | String | `"00123"` (leading zero) |

## All Data Types

### 1. Null

**Use for**: Empty or missing values

**Prefixes**: `null:`, `none:`

**Auto-detection**: `null`, `NULL`, `None`, `none`, empty string

**Examples**:
```csv
DocumentId,optional_field
user1,null:
user2,
user3,NULL
```

All three values → `None` in Firestore

### 2. Boolean

**Use for**: True/false flags

**Prefixes**: `bool:`, `boolean:`

**Auto-detection**: `true`, `false`, `yes`, `no`, `y`, `n` (case-insensitive)

**Examples**:
```csv
DocumentId,active,verified
user1,bool: true,yes
user2,false,no
```

Results:
- `bool: true` → `True`
- `yes` → `True`
- `false` → `False`
- `no` → `False`

### 3. Integer

**Use for**: Whole numbers

**Prefixes**: `int:`, `integer:`

**Auto-detection**: All digits, optional minus sign: `42`, `-10`, `0`

**Examples**:
```csv
DocumentId,age:int,score
user1,25,int: 100
user2,30,95
```

Results:
- Column hint `age:int` → All ages as integers
- `int: 100` → `100`
- `95` → `95` (auto-detected)

### 4. Float

**Use for**: Decimal numbers

**Prefixes**: `float:`, `double:`

**Auto-detection**: Contains decimal point or scientific notation

**Examples**:
```csv
DocumentId,price:float,rating,scientific
item1,29.99,4.5,float: 1e5
item2,19.50,3.7,2.5e-3
```

Results:
- `29.99` → `29.99`
- `4.5` → `4.5`
- `float: 1e5` → `100000.0`
- `2.5e-3` → `0.0025`

### 5. String

**Use for**: Text, forced string representation of numbers

**Prefixes**: `str:`, `string:`, `text:`

**Auto-detection**: Fallback for unmatched values

**Examples**:
```csv
DocumentId,name,phone:str,zip
user1,John,str: 5551234567,str: 00501
user2,Jane,"5559876543","02134"
```

Results:
- `John` → `"John"` (auto-detected)
- `str: 5551234567` → `"5551234567"` (forced string)
- `"5559876543"` → `"5559876543"` (quoted preserves string)
- `str: 00501` → `"00501"` (preserves leading zeros)
- `"02134"` → `"02134"` (quoted preserves leading zero)

### 6. Timestamp

**Use for**: Dates and times

**Prefixes**: `timestamp:`, `datetime:`, `date:`

**Auto-detection**: ISO 8601 format (contains `T` or multiple hyphens)

**Supported Formats**:
- `2025-01-15T10:30:00` (ISO 8601 with time)
- `2025-01-15T10:30:00Z` (UTC)
- `2025-01-15T10:30:00+05:00` (with timezone)
- `2025-01-15` (date only)
- `2025/01/15 10:30:00` (slash format)

**Examples**:
```csv
DocumentId,created_at:timestamp,updated_at
doc1,2025-01-15T10:30:00,timestamp: 2025-01-14T09:00:00
doc2,2025-01-16,2025/01/15 14:00:00
```

All values → `datetime` objects in Firestore

### 7. GeoPoint

**Use for**: Geographic coordinates (latitude, longitude)

**Prefixes**: `geopoint:`, `geo:`, `location:`

**Format**: `latitude,longitude` (comma-separated floats)

**Examples**:
```csv
DocumentId,location:geopoint,office
store1,geopoint: 40.7128,-74.0060,geo: 37.7749,-122.4194
store2,34.0522,-118.2437,location: -33.8688,151.2093
```

Results:
- `geopoint: 40.7128,-74.0060` → `GeoPoint(40.7128, -74.0060)` (New York)
- `geo: 37.7749,-122.4194` → `GeoPoint(37.7749, -122.4194)` (San Francisco)

**Common Errors**:
```
geopoint: -74.0060,40.7128  ❌ Swapped (lng,lat) - should be (lat,lng)
geopoint: 40.7128           ❌ Missing longitude
```

### 8. Array/List

**Use for**: Lists of values

**Prefixes**: `array:`, `list:`

**Format**: JSON array syntax

**Examples**:
```csv
DocumentId,tags:array,roles
user1,array: ["admin" "user"],list: ["editor"]
user2,"[""developer"", ""tester""]",["viewer"]
```

Results:
- `array: ["admin", "user"]` → `["admin", "user"]`
- `list: ["editor"]` → `["editor"]`
- Arrays can contain mixed types: `[1, "text", true]`

**Note**: Must use valid JSON syntax with quoted strings

### 9. Map/Object

**Use for**: Nested objects/dictionaries

**Prefixes**: `map:`, `dict:`, `object:`

**Format**: JSON object syntax

**Examples**:
```csv
DocumentId,metadata:map,config
doc1,map: {"role": "admin" "level": 5},dict: {"theme": "dark"}
doc2,"{""author"": ""John"", ""version"": ""1.0""}",object: {"enabled": true}
```

Results:
- `map: {"role": "admin", "level": 5}` → `{"role": "admin", "level": 5}`
- Supports nested objects: `{"outer": {"inner": "value"}}`

**Note**: Keys must be quoted in JSON syntax

### 10. Bytes

**Use for**: Binary data (images, files, encoded content)

**Prefixes**: `bytes:`

**Format**: Base64-encoded string

**Example**:
```csv
DocumentId,file_content:bytes
file1,bytes: aGVsbG8gd29ybGQ=
```

Result: `bytes: aGVsbG8gd29ybGQ=` → `b'hello world'` (decoded from base64)

**How to encode**:
```python
import base64
encoded = base64.b64encode(b"hello world").decode()
# Use in CSV: bytes: aGVsbG8gd29ybGQ=
```

### 11. Reference

**Use for**: Firestore document references

**Prefixes**: `ref:`, `reference:`

**Format**: Document path (e.g., `collection/document_id`)

**Examples**:
```csv
DocumentId,author_ref:reference,category
post1,ref: users/user123,reference: categories/tech
post2,users/user456,categories/sports
```

Results:
- `ref: users/user123` → `"users/user123"` (path string)
- `reference: categories/tech` → `"categories/tech"`

**Note**: Returns the path as a string (not a DocumentReference object)

## Complete Prefix Reference

All 23 recognized type prefixes across 10 data types:

| Type | All Prefixes | Example Input | Result |
|------|-------------|---------------|---------|
| **Null** | `null:`, `none:` | `null: ` | `None` |
| **Boolean** | `bool:`, `boolean:` | `bool: true` | `True` |
| **Integer** | `int:`, `integer:` | `int: 100` | `100` |
| **Float** | `float:`, `double:` | `float: 3.14` | `3.14` |
| **String** | `str:`, `string:`, `text:` | `str: 00123` | `"00123"` |
| **Timestamp** | `timestamp:`, `datetime:`, `date:` | `timestamp: 2025-01-15T10:30:00` | datetime |
| **GeoPoint** | `geopoint:`, `geo:`, `location:` | `geopoint: 40.7,-74.0` | GeoPoint |
| **Array** | `array:`, `list:` | `array: [1, 2, 3]` | `[1, 2, 3]` |
| **Map** | `map:`, `dict:`, `object:` | `map: {"key": "val"}` | `{"key": "val"}` |
| **Bytes** | `bytes:` | `bytes: aGVsbG8=` | `b'hello'` |
| **Reference** | `ref:`, `reference:` | `ref: users/user123` | `"users/user123"` |

**Total**: 10 types, 23 prefixes

## Special Cases

### Forcing Numbers as Strings

**Problem**: Phone numbers, ZIP codes, and product IDs lose leading zeros or are misinterpreted as numbers.

**Issue Example**:
```csv
DocumentId,phone,zip,product_id
user1,5551234567,00501,007
```

Without intervention:
- `5551234567` → `5551234567` (number, OK)
- `00501` → `501` (❌ lost leading zeros)
- `007` → `7` (❌ lost leading zeros)

**Solution 1: Use `str:` prefix** (Recommended - most explicit)
```csv
DocumentId,phone:str,zip,product_id
user1,5551234567,str: 00501,str: 007
```

Results:
- `5551234567` → `"5551234567"`
- `str: 00501` → `"00501"` ✅
- `str: 007` → `"007"` ✅

**Solution 2: Quote values in CSV**
```csv
DocumentId,phone,zip,product_id
user1,"5551234567","00501","007"
```

Quoted values are always treated as strings.

**Solution 3: Column header hint**
```csv
DocumentId,phone:str,zip:str,product_id:str
user1,5551234567,00501,007
```

Entire columns treated as strings.

### ISO 8601 Timestamps

**Recommended format**: `YYYY-MM-DDTHH:MM:SS`

**Supported Variations**:
```
2025-01-15T10:30:00       ✅ Basic
2025-01-15T10:30:00Z      ✅ UTC
2025-01-15T10:30:00+05:00 ✅ Timezone offset
2025-01-15                ✅ Date only
2025/01/15 10:30:00       ✅ Slash format
```

**Not Supported** (use prefix if needed):
```
01/15/2025                ❌ Ambiguous format
15-Jan-2025               ❌ Month name
Jan 15, 2025              ❌ Text format
```

For non-standard formats, use explicit prefix:
```csv
DocumentId,created_at
doc1,timestamp: 01/15/2025
```

### GeoPoint Format

**Format**: `latitude,longitude` (no space after comma recommended)

**Valid Examples**:
```
geopoint: 40.7128,-74.0060   ✅ New York
geopoint: 37.7749,-122.4194  ✅ San Francisco
geopoint: -33.8688,151.2093  ✅ Sydney (negative lat)
geopoint: 51.5074,-0.1278    ✅ London (negative lng)
```

**Common Mistakes**:
```
geopoint: -74.0060,40.7128  ❌ Swapped! Should be lat,lng not lng,lat
geopoint: 40.7128           ❌ Missing longitude
geopoint: (40.7128,-74.006) ❌ Don't use parentheses
geopoint: 40.7128, -74.006  ⚠️ Space after comma works but not recommended
```

**Latitude Range**: -90 to +90  
**Longitude Range**: -180 to +180

### Arrays and Maps (JSON Syntax)

Must use valid JSON syntax with quoted strings.

**Valid Arrays**:
```csv
tags:array
array: ["tag1", "tag2", "tag3"]     ✅
array: [1, 2, 3]                    ✅
array: ["text", 123, true, null]    ✅ Mixed types
array: []                           ✅ Empty array
```

**Invalid Arrays**:
```csv
tags:array
array: [tag1, tag2]      ❌ Strings must be quoted
array: ['item1']         ❌ Use double quotes, not single
```

**Valid Maps**:
```csv
metadata:map
map: {"name": "John", "age": 30}              ✅
map: {"nested": {"key": "value"}}             ✅
map: {}                                       ✅ Empty object
dict: {"active": true, "score": 95.5}         ✅
```

**Invalid Maps**:
```csv
metadata:map
map: {name: "John"}           ❌ Keys must be quoted
map: {'name': 'John'}         ❌ Use double quotes
map: {"name": John}           ❌ String values must be quoted
```

### Bytes (Base64 Encoding)

**Encoding Process**:
```python
import base64

# Encode bytes to base64 string
data = b"hello world"
encoded = base64.b64encode(data).decode()  # "aGVsbG8gd29ybGQ="

# Use in CSV
# bytes: aGVsbG8gd29ybGQ=
```

**CSV Example**:
```csv
DocumentId,file_data:bytes
doc1,bytes: aGVsbG8gd29ybGQ=
```

**Firestore Result**: `b'hello world'` (decoded binary data)

**Use Cases**:
- Small binary files
- Encrypted data
- Encoded images (though Cloud Storage is better for large images)

## Type Conversion Warnings

When a type conversion fails, the tool:

1. **Logs a warning**: `Cannot convert 'abc' to integer, returning as string`
2. **Returns original value as string**: Graceful degradation
3. **Continues processing**: Doesn't fail entire upload

**Example**:
```csv
DocumentId,age:int,name
user1,25,John
user2,unknown,Jane
```

**Result**:
- `user1.age` → `25` (integer) ✅
- `user2.age` → `"unknown"` (string, with warning) ⚠️
- Upload succeeds for both users

**Best Practice**: Check logs for warnings to catch data quality issues.

## Performance Tips

1. **Prefer column hints over value prefixes**:
   ```csv
   age:int         ✅ Set once for entire column
   int: 25         ⚠️ Repeat for every value
   ```

2. **Use auto-detection when possible**:
   - Simpler CSV files
   - Faster to prepare
   - Only add type hints when auto-detection fails

3. **Quote strings in CSV for leading zeros**:
   ```csv
   "00123"  ✅ Faster than str: 00123
   ```

4. **Avoid complex JSON in CSV when possible**:
   - Use schema-driven transformation instead
   - Flatter CSVs are easier to maintain
