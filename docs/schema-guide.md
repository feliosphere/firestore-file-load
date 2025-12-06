# 📐 Schema Guide

Transform flat CSV rows into complex, hierarchical Firestore documents using `schema.json` configuration.

## Table of Contents

1. [When to Use Schemas](#when-to-use-schemas)
2. [Automatic Grouping (No Schema)](#automatic-grouping-no-schema)
3. [Schema-Driven Transformation](#schema-driven-transformation)
4. [Multi-Level Nested Maps (Advanced)](#multi-level-nested-maps-advanced)
5. [Configuration Reference](#configuration-reference)
6. [Dynamic List Filtering](#dynamic-list-filtering)
7. [Complete Example](#complete-example)

## When to Use Schemas

Choose your approach based on your data structure needs:

| Approach | Use When | Result Structure |
|----------|----------|------------------|
| **No Schema** | Simple flat documents | 1 CSV row = 1 Firestore document |
| **No Schema + Same DocumentId** | Grouping related rows | Multiple rows → single document with `items` array |
| **Schema-Driven** | Complex nested structures | Flat CSV → hierarchical JSON with custom fields |

## Automatic Grouping (No Schema)

When multiple CSV rows share the same `DocumentId`, they're automatically grouped into an `items` array within a single Firestore document.

### Example: Order Items

**CSV Input** (`orders.csv`):
```csv
DocumentId,item_name,price
order_101,Apple,1.50
order_101,Banana,0.80
order_102,Cherry,2.00
```

**Command**:
```bash
ffload orders.csv
```

**Firestore Result**:

Document `order_101`:
```json
{
  "items": [
    {"item_name": "Apple", "price": 1.50},
    {"item_name": "Banana", "price": 0.80}
  ]
}
```

Document `order_102`:
```json
{
  "items": [
    {"item_name": "Cherry", "price": 2.00}
  ]
}
```

## Schema-Driven Transformation

For complex data structures (nested maps, custom arrays, literal values), create a JSON schema file. The tool automatically looks for a schema file matching your CSV filename (e.g., `data.csv` → `data.json`), or you can specify a custom path with the `-s` flag.

### Basic Schema Structure

```json
{
  "key_column": "id",
  "structure": {
    "field_name": "csv_column"
  }
}
```

### Real-World Example: Quiz Questions

**Problem**: Transform flat quiz data into nested question objects with variable-length option arrays.

**CSV** (`questions.csv`):
```csv
DocumentId,id,question,option_a,option_b,option_c,option_d,correct_option_id
quiz_1,Q1,What is 2+2?,3,4,5,,b
quiz_1,Q2,Capital of France?,London,Paris,Berlin,Madrid,b
```

**Schema** (`questions.json`):
```json
{
  "key_column": "id",
  "structure": {
    "question": "question",
    "options": [
      {"id": "literal:a", "text": "option_a"},
      {"id": "literal:b", "text": "option_b"},
      {"id": "literal:c", "text": "option_c"},
      {"id": "literal:d", "text": "option_d"}
    ],
    "correct_option_id": "correct_option_id"
  }
}
```

**Command**:
```bash
# Auto-detects questions.json
ffload questions.csv

# Or explicitly specify
ffload questions.csv -s questions.json
```

**Firestore Result** (Document `quiz_1`):
```json
{
  "Q1": {
    "question": "What is 2+2?",
    "options": [
      {"id": "a", "text": "3"},
      {"id": "b", "text": "4"},
      {"id": "c", "text": "5"}
      // option_d empty → automatically filtered out
    ],
    "correct_option_id": "b"
  },
  "Q2": {
    "question": "Capital of France?",
    "options": [
      {"id": "a", "text": "London"},
      {"id": "b", "text": "Paris"},
      {"id": "c", "text": "Berlin"},
      {"id": "d", "text": "Madrid"}
    ],
    "correct_option_id": "b"
  }
}
```

## Multi-Level Nested Maps (Advanced)

For complex hierarchical data, you can create deeply nested map structures using recursive `key_column` definitions. This enables map-within-map structures with arbitrary depth.

### When to Use

Multi-level nesting is ideal for:
- **Hierarchical taxonomies**: Categories → Subcategories → Items
- **Game/education levels**: Worlds → Levels → Content
- **Geographic data**: Countries → States → Cities
- **Product catalogs**: Departments → Categories → Products

### Basic Concept

Instead of having a single `key_column` that creates one level of nesting, you can nest `key_column` definitions within the `structure` to create multiple levels.

**Single-level nesting**:
```json
{
  "key_column": "id",
  "structure": { "name": "name" }
}
```
Result: `{id_value: {name: ...}}`

**Two-level nesting**:
```json
{
  "key_column": "category",
  "structure": {
    "key_column": "item_id",
    "structure": { "name": "name" }
  }
}
```
Result: `{category_value: {item_id_value: {name: ...}}}`

### Example: World Levels

**CSV** (`tests/fixtures/worlds.csv`):
```csv
DocumentId,worlds,world_num,title,questions_list:list
toyCL,world_a,1,World 11,"[""q1"", ""q2"", ""q3""]"
toyCL,world_a,2,World 12,"[""q4"", ""q5""]"
toyCL,world_b,1,World 21,"[""q6""]"
toyCL,world_b,2,World 22,"[""q7"", ""q8""]"
```

**Schema** (`worlds.json`):
```json
{
  "key_column": "worlds",
  "structure": {
    "key_column": "world_num",
    "structure": {
      "course_id": "DocumentId",
      "title": "title",
      "questions_list": "questions_list"
    }
  }
}
```

**Command**:
```bash
ffload tests/fixtures/worlds.csv
```

**Firestore Result** (Document `toyCL`):
```json
{
  "world_a": {
    "1": {
      "course_id": "toyCL",
      "title": "World 11",
      "questions_list": ["q1", "q2", "q3"]
    },
    "2": {
      "course_id": "toyCL",
      "title": "World 12",
      "questions_list": ["q4", "q5"]
    }
  },
  "world_b": {
    "1": {
      "course_id": "toyCL",
      "title": "World 21",
      "questions_list": ["q6"]
    },
    "2": {
      "course_id": "toyCL",
      "title": "World 22",
      "questions_list": ["q7", "q8"]
    }
  }
}
```

### Example: Three-Level Hierarchy

**CSV** (`products.csv`):
```csv
DocumentId,category,subcategory,item_id,name,price:float
store1,electronics,phones,p1,iPhone,999.99
store1,electronics,phones,p2,Samsung,899.99
store1,electronics,laptops,l1,MacBook,1999.99
store1,clothing,shirts,s1,T-Shirt,19.99
```

**Schema** (`products.json`):
```json
{
  "key_column": "category",
  "structure": {
    "key_column": "subcategory",
    "structure": {
      "key_column": "item_id",
      "structure": {
        "name": "name",
        "price": "price"
      }
    }
  }
}
```

**Firestore Result** (Document `store1`):
```json
{
  "electronics": {
    "phones": {
      "p1": {"name": "iPhone", "price": 999.99},
      "p2": {"name": "Samsung", "price": 899.99}
    },
    "laptops": {
      "l1": {"name": "MacBook", "price": 1999.99}
    }
  },
  "clothing": {
    "shirts": {
      "s1": {"name": "T-Shirt", "price": 19.99}
    }
  }
}
```

### Combining with Lists and Other Features

Multi-level nesting works seamlessly with all schema features:

**CSV**:
```csv
DocumentId,category,item_id,question,opt_a,opt_b,opt_c
quiz1,math,q1,What is 2+2?,3,4,5
quiz1,math,q2,What is 3+3?,5,6,7
quiz1,science,q3,Boiling point?,90,100,110
```

**Schema**:
```json
{
  "key_column": "category",
  "structure": {
    "key_column": "item_id",
    "structure": {
      "question": "question",
      "options": [
        {"id": "literal:a", "text": "opt_a"},
        {"id": "literal:b", "text": "opt_b"},
        {"id": "literal:c", "text": "opt_c"}
      ]
    }
  }
}
```

**Result** (Document `quiz1`):
```json
{
  "math": {
    "q1": {
      "question": "What is 2+2?",
      "options": [
        {"id": "a", "text": "3"},
        {"id": "b", "text": "4"},
        {"id": "c", "text": "5"}
      ]
    },
    "q2": {
      "question": "What is 3+3?",
      "options": [
        {"id": "a", "text": "5"},
        {"id": "b", "text": "6"},
        {"id": "c", "text": "7"}
      ]
    }
  },
  "science": {
    "q3": {
      "question": "Boiling point?",
      "options": [
        {"id": "a", "text": "90"},
        {"id": "b", "text": "100"},
        {"id": "c", "text": "110"}
      ]
    }
  }
}
```

### Key Conversion to Strings

**Important**: Firestore requires all map keys to be strings. The tool automatically converts all keys to strings, regardless of their original type in the CSV.

**CSV**:
```csv
DocumentId,category,level:int,name
game1,world_a,1,Easy Level
game1,world_a,2,Medium Level
```

**Result** (keys converted to strings):
```json
{
  "world_a": {
    "1": {"name": "Easy Level"},    // String key "1", not integer 1
    "2": {"name": "Medium Level"}   // String key "2", not integer 2
  }
}
```

**Note**: Even if you use type hints like `level:int`, the value will be an integer but the **key** will always be a string when used in nested maps.

### Best Practices

1. **Plan your hierarchy**: Sketch out the desired JSON structure before creating the schema
2. **Use meaningful key columns**: Choose columns that logically represent each nesting level
3. **Order matters in CSV**: While not strictly required, organizing rows by hierarchy makes debugging easier
4. **Test incrementally**: Start with 2-level nesting, verify it works, then add more levels if needed
5. **Remember keys are strings**: All map keys in Firestore are strings, so `1` becomes `"1"` in the final document

### Common Patterns

#### Two-level: Category → Items
```json
{
  "key_column": "category",
  "structure": {
    "key_column": "item_id",
    "structure": { "data": "value" }
  }
}
```

#### Three-level: Department → Category → Products
```json
{
  "key_column": "department",
  "structure": {
    "key_column": "category",
    "structure": {
      "key_column": "product_id",
      "structure": { "data": "value" }
    }
  }
}
```

## Configuration Reference

### `key_column`

Specifies which CSV column to use as the key for nested objects within each document.

```json
{
  "key_column": "id"
}
```

- The value in this column becomes the key in the Firestore document
- Multiple rows with the same `DocumentId` but different `key_column` values create nested objects
- **Required** when using schema-driven transformation

**Example**:
```csv
DocumentId,id,name
doc1,item_a,Apple
doc1,item_b,Banana
```

With `"key_column": "id"` → Document `doc1`:
```json
{
  "item_a": {"name": "Apple"},
  "item_b": {"name": "Banana"}
}
```

### `structure`

Defines the desired output shape. Supports strings, maps, lists, and literal values.

#### String Mapping

Map a target field name to a CSV column:

```json
{
  "structure": {
    "question_text": "question",
    "answer": "correct_answer"
  }
}
```

CSV column `question` → Firestore field `question_text`

#### Nested Maps

Create hierarchical object structures:

```json
{
  "structure": {
    "metadata": {
      "created_date": "date",
      "author": "author_name",
      "version": "version"
    },
    "content": {
      "title": "title",
      "body": "body_text"
    }
  }
}
```

**CSV**:
```csv
DocumentId,id,date,author_name,version,title,body_text
doc1,item1,2025-01-15,John,1.0,Hello,World
```

**Result**:
```json
{
  "item1": {
    "metadata": {
      "created_date": "2025-01-15",
      "author": "John",
      "version": "1.0"
    },
    "content": {
      "title": "Hello",
      "body": "World"
    }
  }
}
```

#### Arrays/Lists

Define lists with optional literal values:

```json
{
  "structure": {
    "tags": ["tag_1", "tag_2", "tag_3"],
    "options": [
      {"id": "literal:a", "text": "opt_a"},
      {"id": "literal:b", "text": "opt_b"}
    ]
  }
}
```

**Simple Array** (just values):
```json
{"tags": ["tag_1", "tag_2"]}
```

CSV columns `tag_1`, `tag_2` → Array `["value1", "value2"]`

**Array of Objects**:
```json
{"options": [
  {"id": "literal:a", "text": "opt_a"},
  {"id": "literal:b", "text": "opt_b"}
]}
```

Creates objects with fixed `id` values and dynamic `text` values from CSV.

#### Literal Values

Use `literal:value` to hardcode fixed values in your output:

```json
{
  "structure": {
    "type": "literal:question",
    "version": "literal:1.0",
    "options": [
      {"id": "literal:a", "text": "option_a"}
    ]
  }
}
```

**Key Points**:
- `"literal:question"` → Always outputs `"question"` (string)
- Useful for fixed IDs in arrays: `{"id": "literal:a"}` → `{"id": "a"}`
- Literal fields are never considered empty in filtering logic

## Dynamic List Filtering

The tool automatically removes empty items from arrays to handle variable-length data.

### Filtering Logic

An array item is removed if **all its non-literal fields are empty**.

**Example Schema**:
```json
{
  "structure": {
    "options": [
      {"id": "literal:a", "text": "opt_a"},
      {"id": "literal:b", "text": "opt_b"},
      {"id": "literal:c", "text": "opt_c"},
      {"id": "literal:d", "text": "opt_d"}
    ]
  }
}
```

**CSV with 2 Options**:
```csv
DocumentId,id,opt_a,opt_b,opt_c,opt_d
quiz_1,Q1,True,False,,
```

**Result** (only 2 options, not 4):
```json
{
  "Q1": {
    "options": [
      {"id": "a", "text": "True"},
      {"id": "b", "text": "False"}
      // Options c and d filtered out (text fields empty)
    ]
  }
}
```

### Why This Matters

- **Single CSV schema** for questions with 2, 3, 4, or 5 options
- No "ghost" empty objects in Firestore
- Keeps data clean and query-efficient

### What Counts as Empty?

- Empty strings: `""`
- `None`/`null` values
- Whitespace-only strings (after stripping)

### What's Never Empty?

- Literal values: `"literal:a"` → Always `"a"` (not empty)
- The number `0`
- The boolean `false`

## Complete Example

This example demonstrates the full power of schema-driven transformation using real project files.

### Scenario: Educational Quiz Upload

**Goal**: Upload 2 quiz questions with different numbers of options (Q1 has 3 options, Q2 has 2 options).

**CSV** (`toy_csv.csv`):
```csv
DocumentId,id,world_num,in_world_index,question,option_a,option_b,option_c,option_d,correct_option_id,element_1,element_2
RL,RL1,1,0,¿Cuál es el precio original?,§\$100§,§\$90§,§\$120§,§\$150§,a,M1RL,
RL,RL2,1,1,¿Cuál es la dosis diaria?,"§0,7 mg§","§1,4 mg§","§2,0 mg§",,b,M2RL,T1RL
```

**Schema** (`toy_csv.json`):
```json
{
  "key_column": "id",
  "structure": {
    "world_num": "world_num",
    "in_world_index": "in_world_index",
    "question": "question",
    "options": [
      { "id": "literal:a", "text": "option_a" },
      { "id": "literal:b", "text": "option_b" },
      { "id": "literal:c", "text": "option_c" },
      { "id": "literal:d", "text": "option_d" }
    ],
    "correct_option_id": "correct_option_id",
    "content_element_ids": ["element_1", "element_2"]
  }
}
```

**Command**:
```bash
# Auto-detects toy_csv.json, uses custom collection name
ffload toy_csv.csv -c quiz_collection

# Explicitly specify all options
ffload toy_csv.csv -s toy_csv.json -c quiz_collection
```

**Firestore Result** (Collection: `quiz_collection`, Document: `RL`):
```json
{
  "RL1": {
    "world_num": "1",
    "in_world_index": "0",
    "question": "¿Cuál es el precio original?",
    "options": [
      {"id": "a", "text": "§$100§"},
      {"id": "b", "text": "§$90§"},
      {"id": "c", "text": "§$120§"},
      {"id": "d", "text": "§$150§"}
    ],
    "correct_option_id": "a",
    "content_element_ids": ["M1RL"]
  },
  "RL2": {
    "world_num": "1",
    "in_world_index": "1",
    "question": "¿Cuál es la dosis diaria?",
    "options": [
      {"id": "a", "text": "§0,7 mg§"},
      {"id": "b", "text": "§1,4 mg§"},
      {"id": "c", "text": "§2,0 mg§"}
      // Option d filtered out (empty)
    ],
    "correct_option_id": "b",
    "content_element_ids": ["M2RL", "T1RL"]
  }
}
```

### Key Features Demonstrated

1. **Multiple rows → single document**: 2 CSV rows with `DocumentId: RL` → 1 Firestore document
2. **Key column mapping**: `id` column values (`RL1`, `RL2`) become object keys
3. **Nested structure**: Flat CSV columns → structured objects with `world_num`, `question`, `options`, etc.
4. **Dynamic list filtering**: 
   - Q1: 4 options (all filled) → 4 options in Firestore
   - Q2: 3 options filled, 1 empty → 3 options in Firestore (option_d filtered out)
5. **Literal values**: `"literal:a"` → `"a"` in output
6. **Array of strings**: `element_1`, `element_2` → `["M1RL"]` and `["M2RL", "T1RL"]`
   - Q1: element_2 empty → only element_1 in array
   - Q2: both elements → both in array

## Best Practices

### Schema Design

1. **Start simple**: Test without schema first, add schema only when you need nested structures
2. **Use meaningful key_column**: Choose a column that uniquely identifies each sub-object
3. **Leverage literals for fixed values**: Use `literal:` for IDs, types, versions
4. **Design for variable lengths**: Use array filtering for optional fields

### CSV Preparation

1. **Include all potential columns**: Even if some rows leave them empty
2. **Consistent naming**: Use predictable patterns like `option_a`, `option_b`, `option_c`
3. **DocumentId for grouping**: Same DocumentId for all rows that belong to one document

### Testing

1. **Test locally first**: Use `--local` flag with Firestore emulator
2. **Start with small datasets**: Test with 2-3 rows before uploading hundreds
3. **Verify filtering**: Check that empty options/elements are properly removed

## Troubleshooting

### Schema Not Applied

**Symptom**: Data uploads but stays flat (no nested structure)

**Solutions**:
1. Verify schema file exists with correct name:
   - Auto-detected: `[csv_filename].json` (e.g., `data.csv` → `data.json`)
   - Or use `-s` flag to specify custom path
2. Validate JSON syntax: `python -m json.tool schema.json`
3. Ensure `key_column` value exists in your CSV
4. Check logs for schema loading messages (use `-v` or `-d` flags)

### Missing Key Column Error

**Error**: `Skipping row: Missing key column 'id'`

**Solution**: Verify your CSV has a column matching the `key_column` value in schema.json

**schema.json**:
```json
{"key_column": "id"}  ← Requires "id" column
```

**CSV**:
```csv
DocumentId,id,name  ✅ Has "id"
DocumentId,question_id,name  ❌ Missing "id"
```

### All Items Filtered Out

**Symptom**: Array exists but is empty `[]`

**Cause**: All array items have empty non-literal fields

**Example**:
```csv
DocumentId,id,opt_a,opt_b
q1,Q1,,,  ← All options empty
```

**Result**:
```json
{"Q1": {"options": []}}  ← Empty array
```

**Solution**: Ensure at least one item has non-empty data
