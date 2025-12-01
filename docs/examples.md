# 💡 Examples & Use Cases

Real-world examples, best practices, and troubleshooting for FirestoreFileLoad.

## Table of Contents

1. [Simple Product Catalog](#simple-product-catalog)
2. [Quiz Questions with Variable Options](#quiz-questions-with-variable-options)
3. [User Profiles with Nested Data](#user-profiles-with-nested-data)
4. [Geospatial Store Locations](#geospatial-store-locations)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

## Simple Product Catalog

**Use Case**: Upload product inventory without complex nesting

### CSV File (`products.csv`)

```csv
DocumentId,name,price:float,in_stock:bool,sku,category
prod_001,Premium Widget,29.99,true,WDG-001,Electronics
prod_002,Standard Gadget,19.99,false,GDG-002,Tools
prod_003,Deluxe Tool,49.99,true,TL-003,Tools
```

### Command

```bash
ffload products.csv
```

### Firestore Result

Collection: `products`

Document `prod_001`:
```json
{
  "name": "Premium Widget",
  "price": 29.99,
  "in_stock": true,
  "sku": "WDG-001",
  "category": "Electronics"
}
```

Document `prod_002`:
```json
{
  "name": "Standard Gadget",
  "price": 19.99,
  "in_stock": false,
  "sku": "GDG-002",
  "category": "Tools"
}
```

### When to Use

- Simple, flat data structures
- One CSV row = one Firestore document
- No nested objects or arrays needed

## Quiz Questions with Variable Options

**Use Case**: Educational app with multiple-choice questions where different questions have different numbers of options (2-5 options)

**Challenge**: Avoid empty option objects in Firestore when a question has fewer than the maximum options.

### CSV File (`questions.csv`)

```csv
DocumentId,id,question,option_a,option_b,option_c,option_d,correct_option_id,difficulty:int
quiz_math,Q1,What is 2+2?,3,4,5,,b,1
quiz_math,Q2,What is 10/2?,3,4,5,6,c,1
quiz_geo,G1,Capital of France?,London,Paris,,,b,2
quiz_geo,G2,Largest ocean?,Atlantic,Pacific,Indian,Arctic,b,3
```

### Schema File (`questions.json`)

```json
{
  "key_column": "id",
  "structure": {
    "question_text": "question",
    "options": [
      {"id": "literal:a", "text": "option_a"},
      {"id": "literal:b", "text": "option_b"},
      {"id": "literal:c", "text": "option_c"},
      {"id": "literal:d", "text": "option_d"}
    ],
    "correct_option_id": "correct_option_id",
    "difficulty": "difficulty"
  }
}
```

### Command

```bash
# Auto-detects questions.json schema
ffload questions.csv

# Or explicitly specify
ffload questions.csv -s questions.json
```

### Firestore Result

Collection: `questions`

Document `quiz_math`:
```json
{
  "Q1": {
    "question_text": "What is 2+2?",
    "options": [
      {"id": "a", "text": "3"},
      {"id": "b", "text": "4"},
      {"id": "c", "text": "5"}
      // option_d empty → filtered out
    ],
    "correct_option_id": "b",
    "difficulty": 1
  },
  "Q2": {
    "question_text": "What is 10/2?",
    "options": [
      {"id": "a", "text": "3"},
      {"id": "b", "text": "4"},
      {"id": "c", "text": "5"},
      {"id": "d", "text": "6"}
    ],
    "correct_option_id": "c",
    "difficulty": 1
  }
}
```

Document `quiz_geo`:
```json
{
  "G1": {
    "question_text": "Capital of France?",
    "options": [
      {"id": "a", "text": "London"},
      {"id": "b", "text": "Paris"}
      // options c and d empty → filtered out
    ],
    "correct_option_id": "b",
    "difficulty": 2
  },
  "G2": {
    "question_text": "Largest ocean?",
    "options": [
      {"id": "a", "text": "Atlantic"},
      {"id": "b", "text": "Pacific"},
      {"id": "c", "text": "Indian"},
      {"id": "d", "text": "Arctic"}
    ],
    "correct_option_id": "b",
    "difficulty": 3
  }
}
```

### Key Features Demonstrated

- **Multiple rows → single document**: Multiple questions with same `DocumentId` grouped into one document
- **Dynamic list filtering**: Empty options automatically removed
- **Literal values**: `literal:a` becomes `"a"` in output
- **Type conversion**: `difficulty:int` ensures integer type
- **Schema-driven structure**: Flat CSV columns transformed into nested objects

## User Profiles with Nested Data

**Use Case**: User management system with preferences and metadata

### CSV File (`users.csv`)

```csv
DocumentId,name,email,age:int,preferences,metadata
user_001,John Doe,john@example.com,30,map: {"theme": "dark" "notifications": true},map: {"created": "2025-01-15" "role": "admin"}
user_002,Jane Smith,jane@example.com,25,map: {"theme": "light" "notifications": false},map: {"created": "2025-01-14" "role": "user"}
```

### Command

```bash
ffload users.csv -c user_profiles
```

### Firestore Result

Collection: `user_profiles`

Document `user_001`:
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "age": 30,
  "preferences": {
    "theme": "dark",
    "notifications": true
  },
  "metadata": {
    "created": "2025-01-15",
    "role": "admin"
  }
}
```

### Key Features

- **Map type**: Nested objects for preferences and metadata
- **Custom collection name**: `-c user_profiles` flag
- **Type hints**: `age:int` ensures integer conversion

## Geospatial Store Locations

**Use Case**: Store locations for a restaurant chain with geographic coordinates

### CSV File (`stores.csv`)

```csv
DocumentId,name,address,location:geopoint,rating:float,open:bool
store_nyc,NYC Flagship,"123 5th Ave, New York",geopoint: 40.7128,-74.0060,4.8,true
store_sf,SF Branch,"456 Market St, San Francisco",geopoint: 37.7749,-122.4194,4.6,true
store_la,LA Location,"789 Sunset Blvd, Los Angeles",geopoint: 34.0522,-118.2437,4.9,false
```

### Command

```bash
# Test locally first with merge (default)
ffload stores.csv --local -v

# Deploy to production
ffload stores.csv

# Overwrite existing documents instead of merging
ffload stores.csv --no-merge
```

### Firestore Result

Collection: `stores`

Document `store_nyc`:
```json
{
  "name": "NYC Flagship",
  "address": "123 5th Ave, New York",
  "location": GeoPoint(40.7128, -74.0060),
  "rating": 4.8,
  "open": true
}
```

### Querying GeoPoint Data

Once uploaded, you can query by location:

```python
# Python example
from google.cloud import firestore

db = firestore.Client()

# Find stores near a point
center = firestore.GeoPoint(40.7128, -74.0060)
# Note: Firestore doesn't have built-in geoqueries
# Use geohashing library like python-geohash or geofire
```

### Key Features

- **GeoPoint type**: Geographic coordinates for maps
- **Local testing**: `--local` flag tests with emulator first
- **Verbose logging**: `-v` flag shows upload progress

## Best Practices

### CSV Preparation

#### 1. Always Include DocumentId Column

```csv
DocumentId,name,value  ✅ Correct
id,name,value          ❌ Won't work - must be "DocumentId"
```

The `DocumentId` column is required and case-sensitive.

#### 2. Use Consistent Type Hints

**Good** (column-level):
```csv
DocumentId,age:int,score:float,active:bool
user1,25,95.5,true
user2,30,88.0,false
```

**Also Good** (auto-detection):
```csv
DocumentId,age,score,active
user1,25,95.5,true
user2,30,88.0,false
```

**Avoid** (mixing styles unnecessarily):
```csv
DocumentId,age,score
user1,int: 25,float: 95.5
user2,int: 30,float: 88.0
```

#### 3. Validate Data Before Upload

**Check for**:
- Missing `DocumentId` values
- Valid GeoPoint format (`lat,lng`)
- Valid JSON for arrays/maps
- Correct date formats for timestamps

**Validation Script**:
```bash
# Check for missing DocumentIds
awk -F',' 'NR>1 && $1=="" {print "Row " NR ": Missing DocumentId"}' data.csv

# Validate CSV structure
python -c "import csv; list(csv.DictReader(open('data.csv')))"
```

### Schema Design

#### 1. Start Without Schema

Upload flat CSV first to verify data:

```bash
# First upload - no schema
ffload data.csv --local

# Verify in emulator, then add schema if needed
```

#### 2. Use literal: for Fixed Values

**Good**:
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

This hardcodes `"type": "question"` in every document.

#### 3. Test Schema with Small Dataset

```bash
# Create test.csv with 2-3 rows and test.json schema
# Upload to local emulator
ffload test.csv --local

# Verify structure in emulator UI
# Then upload full dataset with corresponding schema
ffload full_data.csv -s full_data.json
```

### Type Safety

#### 1. Prefer Column Hints

```csv
age:int,phone:str,price:float  ✅ Clear and concise
```

Better than:
```csv
age,phone,price
int: 25,str: 5551234,float: 29.99  ⚠️ More verbose
```

#### 2. Quote Numbers That Should Be Strings

**Leading Zeros**:
```csv
DocumentId,zip_code,product_id
user1,"00501","007"  ✅ Preserves zeros
user1,00501,007      ❌ Becomes 501 and 7
```

**Phone Numbers**:
```csv
DocumentId,phone:str
user1,5551234567     ✅ Column hint
user1,"5551234567"   ✅ Quoted
```

#### 3. Use ISO 8601 for Timestamps

```csv
created_at
2025-01-15T10:30:00      ✅ Will auto-detect
01/15/2025               ❌ Won't auto-detect
```

### Performance

#### 1. Group Related Rows Efficiently

**Efficient**:
```csv
DocumentId,id,question,answer
quiz_1,Q1,Question 1,Answer 1
quiz_1,Q2,Question 2,Answer 2
quiz_1,Q3,Question 3,Answer 3
```

3 rows → 1 document (efficient batching)

#### 2. Use Schema to Reduce Query Complexity

Transform data at upload time instead of in queries:

**Without Schema** (harder to query):
```json
{
  "items": [
    {"option_a": "Yes", "option_b": "No"}
  ]
}
```

**With Schema** (easier to query):
```json
{
  "options": [
    {"id": "a", "text": "Yes"},
    {"id": "b", "text": "No"}
  ]
}
```

#### 3. Test Locally First

```bash
# Start local emulator in your Firebase project
firebase emulators:start

# Upload to emulator
ffload data.csv --local

# Verify in emulator UI (http://localhost:4000)
# Then deploy to production
ffload data.csv
```

## Troubleshooting

### Authentication Error: "TypeError: 'str' object is not callable"

**Full Error**:
```
TypeError: 'str' object is not callable
grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with:
    status = StatusCode.UNAVAILABLE
    details = "Getting metadata from plugin failed with error: 'str' object is not callable"
```

**Cause**: Google Cloud Application Default Credentials (ADC) are corrupted or invalid.

**Solution**:
```bash
gcloud auth application-default login
```

This refreshes your credentials and saves them to:
- **Linux/Mac**: `~/.config/gcloud/application_default_credentials.json`
- **Windows**: `%APPDATA%\gcloud\application_default_credentials.json`

After re-authenticating, retry your upload.

---

### Empty Collections After Upload

**Symptom**: Command succeeds with no errors, but Firestore collection is empty.

**Cause**: Missing or misnamed `DocumentId` column in CSV.

**Solution**:

1. **Check column name** (case-sensitive):
   ```csv
   DocumentId,name  ✅ Correct
   documentid,name  ❌ Wrong case
   document_id,name ❌ Wrong name
   id,name          ❌ Wrong name
   ```

2. **Check for empty DocumentIds**:
   ```csv
   DocumentId,name
   doc1,Alice  ✅
   ,Bob        ❌ Empty DocumentId
   ```

3. **Verify CSV structure**:
   ```bash
   head -1 data.csv  # Should show "DocumentId,..." as first column
   ```

---

### Type Conversion Warnings

**Warning in Logs**:
```
2025-01-15 10:30 - WARNING: Cannot convert 'abc123' to integer, returning as string
```

**Cause**: Type prefix or column hint doesn't match value format.

**Example CSV**:
```csv
DocumentId,age:int,name
user1,25,John      ✅ OK
user2,unknown,Jane ⚠️ Warning
```

**Solutions**:

1. **Fix data**: Change `unknown` to a number or remove type hint
2. **Accept as string**: If intentional, ignore warning (upload succeeds)
3. **Use correct type**:
   ```csv
   DocumentId,age,name      # Remove :int
   user1,25,John
   user2,unknown,Jane       # Now treated as string
   ```

---

### Schema Not Applied

**Symptom**: Data uploads successfully but in flat structure (no nesting from schema).

**Possible Causes**:

#### 1. Schema File Not Found

**Check**:
```bash
# For data.csv, schema should be data.json
ls data.json

# Or check if you're using custom schema path
ffload data.csv -s custom_schema.json  # Verify path is correct
```

**Solution**: Ensure schema file exists with correct name or path:
```bash
# Option 1: Use auto-detected name
mv schema.json data.json  # Rename to match CSV
ffload data.csv

# Option 2: Use -s flag for custom path
ffload data.csv -s /path/to/custom_schema.json
```

#### 2. Invalid JSON Syntax

**Validate**:
```bash
python -m json.tool schema.json
# Should print formatted JSON
# If error, fix JSON syntax
```

**Common JSON Errors**:
```json
{
  "key_column": "id",  # ❌ No comments in JSON
  "structure": {
    "name": "name"     # ❌ Missing comma (if more fields follow)
  }
}
```

**Correct**:
```json
{
  "key_column": "id",
  "structure": {
    "name": "name"
  }
}
```

#### 3. Missing key_column in CSV

**schema.json**:
```json
{
  "key_column": "id"  ← Requires "id" column in CSV
}
```

**CSV**:
```csv
DocumentId,question_id,name  ❌ No "id" column
DocumentId,id,name           ✅ Has "id" column
```

**Solution**: Ensure CSV has the column specified in `key_column`.

---

### Missing Key Column Error

**Error in Logs**:
```
Skipping row in doc_1: Missing key column 'id'
```

**Cause**: Schema references a `key_column` that doesn't exist in CSV.

**Example**:

**schema.json**:
```json
{"key_column": "id"}
```

**CSV**:
```csv
DocumentId,question_id,text
doc1,Q1,Hello  ❌ Has "question_id" not "id"
```

**Solutions**:

1. **Rename CSV column**:
   ```csv
   DocumentId,id,text  ✅
   ```

2. **Update schema.json**:
   ```json
   {"key_column": "question_id"}  ✅ Match CSV
   ```

---

### GeoPoint Conversion Errors

**Warning**:
```
Invalid GeoPoint format 'New York', expected 'lat,lng'
```

**Cause**: GeoPoint value not in `latitude,longitude` numeric format.

**Incorrect**:
```csv
location:geopoint
New York           ❌ City name
40.7128            ❌ Missing longitude
-74.0060,40.7128   ❌ Swapped (lng,lat)
(40.7128,-74.006)  ❌ Parentheses
```

**Correct**:
```csv
location:geopoint
40.7128,-74.0060   ✅ lat,lng format
```

**Solution**: Use numeric coordinates in `latitude,longitude` order.

**Finding Coordinates**:
- Google Maps: Right-click location → "Copy coordinates"
- Format: `40.7128,-74.0060` (lat,lng)

---

### Arrays Not Parsing

**Symptom**: Array appears as string in Firestore:
```json
{"tags": "[\"admin\", \"user\"]"}  ❌ String, not array
```

**Cause**: Missing `array:` prefix or invalid JSON syntax.

**Incorrect**:
```csv
tags
[admin, user]                    ❌ Not valid JSON (missing quotes)
["admin", "user"]                ⚠️ Might need prefix
```

**Correct**:
```csv
tags:array
array: ["admin", "user"]         ✅ Prefix + valid JSON
```

Or:
```csv
tags:array
"[""admin"", ""user""]"          ✅ Escaped quotes in CSV
```

**Solution**: Use `array:` prefix and valid JSON syntax with quoted strings.

---

### Permission Denied Errors

**Error**:
```
google.api_core.exceptions.PermissionDenied: 403 Missing or insufficient permissions
```

**Cause**: Service account lacks Firestore write permissions.

**Solution**:

1. **Check Firestore Rules** (for emulator/development):
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /{document=**} {
         allow read, write: if true;  // ⚠️ Development only!
       }
     }
   }
   ```

2. **Grant IAM Permissions** (for production):
   ```bash
   # Grant Firestore User role to service account
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com" \
     --role="roles/datastore.user"
   ```

3. **Verify Service Account**:
   ```bash
   gcloud auth application-default login --project YOUR_PROJECT_ID
   ```

---

### Large File Upload Issues

**Symptom**: Upload times out or fails with large CSV files (>10,000 rows).

**Solutions**:

1. **Split into smaller files**:
   ```bash
   # Split CSV into 1000-row chunks
   split -l 1000 large_file.csv chunk_
   
   # Upload each chunk
   for file in chunk_*; do
     ffload "$file" -c my_collection
   done
   ```

2. **Use verbose logging** to track progress:
   ```bash
   ffload large_file.csv -v
   ```

3. **Test with subset first**:
   ```bash
   head -100 large_file.csv > test.csv
   ffload test.csv --local
   ```

---

### Debug Mode

For any issue, enable debug logging to see detailed information:

```bash
ffload data.csv -d
```

**Debug output includes**:
- Full stack traces for errors
- Type conversion decisions
- Row-by-row processing details
- Firestore API calls

**Example debug output**:
```
2025-01-15 10:30 - DEBUG: Starting CLI execution...
2025-01-15 10:30 - DEBUG: Reading CSV file: data.csv
2025-01-15 10:30 - DEBUG: Found 3 rows
2025-01-15 10:30 - DEBUG: Converting value '25' to type int
2025-01-15 10:30 - DEBUG: Uploading document: user_001
```

---

## Getting Help

If you encounter issues not covered here:

1. **Enable debug mode**: `ffload data.csv -d`
2. **Check logs** for specific error messages
3. **Verify CSV structure**: Ensure `DocumentId` column exists
4. **Test locally**: Use `--local` flag with emulator
5. **Report issues**: [GitHub Issues](https://github.com/feliosphere/firestore-file-load/issues)

## Quick Reference

**Common Commands**:
```bash
# Basic upload (auto-detects data.json schema)
ffload data.csv

# Custom collection name
ffload data.csv -c my_collection

# Custom schema file
ffload data.csv -s custom_schema.json

# Merge mode (default - adds/updates fields)
ffload data.csv --merge

# Overwrite mode (replaces entire documents)
ffload data.csv --no-merge

# Local emulator
ffload data.csv --local

# Verbose logging
ffload data.csv -v

# Debug mode
ffload data.csv -d

# Combine flags
ffload data.csv -c products -s product_schema.json --merge --local -v
```

**File Requirements**:
- CSV must have `DocumentId` column (case-sensitive)
- Schema file optional:
  - Auto-detected: `[csv_filename].json` (e.g., `data.csv` → `data.json`)
  - Custom path: Use `-s` flag
- Valid CSV format (commas, proper quoting)

**Type Hints**:
- Column: `age:int`, `price:float`, `active:bool`
- Value: `int: 25`, `str: 00123`, `geopoint: 40.7,-74.0`
- Auto-detect: Works for most common types
