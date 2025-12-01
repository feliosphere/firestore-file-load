# FirestoreFileLoad

_A personalized tool to load your CSV (more options to come...) files into Firestore._

## Why?
I initially built this as a script for my team to manage secure Firestore batch uploads, as the existing solutions didn't meet our specific requirements. I'm now sharing it and adding more features, hoping it becomes a useful utility for others in the developer community!

## How it works?
This script will create or overwrite (if permissions are correctly set in the Firebase Console) a collection in your Firestore DB. Your filename will be used as the collection name, and each row in your CSV will be a document in the collection. Label your data correctly as described in the [Prepare the data](#prepare-the-data) subsection.

## Setup

### Python Virtual Environment

You can use your proferred Virtual Environment to manage dependencies (e.g., `venv`, `conda`, `pipenv`), just make sure to install the dependencies listed in [requirements.txt](requirements.txt) and activate it before running the script. For example, if you're using `venv`:

1. Create a Python virtual environment using `venv`:
```
python3 -m venv .venv
```
2. Activate the virtual environment:
```
source .venv/bin/activate
```
3. Prepare pip
```
python3 -m pip install --upgrade pip
python3 -m pip --version
```
4. Install the required dependencies:
```
python3 -m pip install -r requirements.txt
```

### Google Cloud Certificates

5. Create a [service account](https://cloud.google.com/iam/docs/service-accounts-create#creating) in the Google Cloud console to be used as a data loader.
1. Install `gcloud CLI` following the [Install the gcloud CLI](https://cloud.google.com/sdk/docs/install) instructions.
1. Verify you are using the correct Google Cloud project:
   ```bash
   gcloud config get-value project
   ```
   If you need to change the project:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```
1. Set local dev environment using the [Service Account Credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc#service-account).

\* Aletratively you can attempt to use a user account, but I found the service account a more straight forward and team reusable process.

## Prepare the data

1. Organize your data in a spread sheet with the following structure:
   - The first row must be the labels of your _DocumentIds_ and _fields_
   - The column with the **DocumentIds** must be called `DocumentId`
1. Download the data as a CSV file.
1. Name de CSV file as the desired `CollectionId` (no need to remove the .csv extension).

### 🚀 Advanced Data Grouping

**FFLoad** supports powerful data grouping capabilities. This allows you to turn flat CSV rows into complex, hierarchical Firestore documents without writing custom code.

#### 1. Automatic Grouping (Default Behavior)

If you do not provide a schema, the tool automatically detects when multiple rows share the same `DocumentId`. Instead of overwriting the document, it groups the rows into a list called `items`.

**CSV Input:**
```csv
DocumentId, item_name, price
order_101,  Apple,     1.50
order_101,  Banana,    0.80
order_102,  Cherry,    2.00
```

**Firestore Result:** Document: `order_101`
```json
{
  "items": [
    { "item_name": "Apple", "price": 1.50 },
    { "item_name": "Banana", "price": 0.80 }
  ]
}
```
#### 2. Schema-Driven Structure (Advanced)

For complex data structures (nested maps, dynamic lists), you can define a `schema.json` file in your root directory. This tells the tool how to restructure your flat CSV columns into a nested JSON tree.

How to use:

    Create a `schema.json` file in the folder where you run the script.

    Define your structure using the configuration options below.

**Example** `schema.json`:

```json
{
  "key_column": "id",
  "structure": {
    "question_text": "question",
    "options": [
      { "id": "literal:a", "text": "opt_a" },
      { "id": "literal:b", "text": "opt_b" },
      { "id": "literal:c", "text": "opt_c" }
    ],
    "tags": ["tag_1", "tag_2"]
  }
}
```

#### Schema Configuration Options

- `key_column`: Specifies which column in the CSV is used as the key for the map inside the document.

- `structure`: A JSON object defining the desired output shape.

  - `Maps`: Define nested dictionaries to create maps in Firestore.

  - `Lists`: Define arrays to create lists in Firestore.

  - `Strings`: Map a target field name to a CSV column header.

- `literal`: *Prefix*: Use `literal:value` to hardcode a string in your output. This is essential for fixed IDs in lists (e.g., `{"id": "literal:a"}`).

#### ✨ Dynamic List Filtering

The tool is smart enough to handle variable-length lists from a fixed CSV structure.

If you define a list in your schema (e.g., 4 potential options), but a specific CSV row only has data for 2 of them, the tool will **automatically drop the empty items**.

- **Logic**: An item is dropped if all its non-literal fields are empty.

- **Benefit**: You can use a single CSV schema to upload questions with 2, 3, 4, or 5 options without creating empty "ghost" objects in Firestore.

### Data Type Support

The script now supports all Firestore data types! You can use explicit type prefixes in your CSV values or rely on automatic type detection.
Define the type for the whole column by appending the type (_e.g._ `age:int`) or for speific fields by using a prefix (_e.g._ `str: 45`)

**Automatic Type Detection:**
- `42` → Integer
- `3.14` → Float
- `true`, `false`, `yes`, `no` → Boolean
- `null`, `NULL`, `None` → Null
- `2025-01-15T10:30:00` → Timestamp (ISO 8601 format)
- `Hello World` → String (default)

**Forcing Numbers as Strings:**

Sometimes you need to store numbers as strings (e.g., phone numbers, ZIP codes, IDs with leading zeros). You have two options:

1. **Use the `str:` prefix** (Recommended - most explicit):
   ```csv
   DocumentId,phone,zip_code,product_id
   user1,str: 5551234567,str: 00501,str: 007
   ```

2. **Quote the value in your CSV**:
   ```csv
   DocumentId,phone,zip_code,product_id
   user1,"5551234567","00501","007"
   ```
   Note: Both methods preserve leading zeros and prevent numeric conversion.

**Explicit Type Prefixes:**

Use type prefixes to ensure correct data types or to use advanced types:

| Type | Prefix | Example | Result |
|------|--------|---------|--------|
| Null | `null:` or `none:` | `null: ` | None |
| Boolean | `bool:` or `boolean:` | `bool: true` | True |
| Integer | `int:` or `integer:` | `int: 100` | 100 |
| Float | `float:` or `double:` | `float: 3.14` | 3.14 |
| String | `str:` or `string:` | `str: 123` | "123" (as string) |
| Timestamp | `timestamp:` or `datetime:` | `timestamp: 2025-01-15T10:30:00` | Datetime object |
| GeoPoint | `geopoint:` or `geo:` | `geopoint: 37.7749,-122.4194` | GeoPoint(37.7749, -122.4194) |
| Array | `array:` or `list:` | `array: [1, 2, 3]` | [1, 2, 3] |
| Map/Object | `map:` or `dict:` | `map: {"name": "John"}` | {"name": "John"} |
| Bytes | `bytes:` | `bytes: aGVsbG8=` | b'hello' (base64 decoded) |
| Reference | `ref:` or `reference:` | `ref: users/user123` | "users/user123" |

**Example CSV:**

```csv
DocumentId,name,age,active,score,location,tags,metadata,created_at
user1,John Doe,int: 30,bool: true,float: 95.5,geopoint: 40.7128,-74.0060,array: ["admin" "user"],map: {"role": "admin"},timestamp: 2025-01-15T10:30:00
user2,Jane Smith,25,true,88.3,geo: 34.0522,-118.2437,list: ["user"],dict: {"role": "user"},2025-01-14T09:00:00
```

### Running the app

You can run the package with the `-m` flag:

```
py -m firebase_uploader [-h] [-d] [-v] [-c COLLECTION] [--mode {collection,document}] [--local] csv_file_path
```

or (**Recommended**) install the cli package in your environment buy running (from root directory):

```
pip install .
```
and then run with the cli command:

```
ffload [-h] [-d] [-v] [-c COLLECTION] [--mode {collection,document}] [--local] csv_file_path
```

#### For local emulator
1. Start your Firestore emulators from your project.
1. Run the Python script providing the desire options:

   ```
   usage: __main__.py [-h] [-d] [-v] [-c COLLECTION] [--mode {collection,document}] [--local] csv_file_path
   
   A simple CLI tool for csv to Firestore
   
   positional arguments:
     csv_file_path         Path to the CSV file.
   
   options:
     -h, --help            show this help message and exit
     -c COLLECTION, --collection COLLECTION
                           Target Firestore collection name. Defaults to CSV filename.
     --mode {collection,document}
                           Upload mode: "collection" (one collection per file) or "document" (one document per file).
     --local               Use the Firestore emulator instead of Cloud Firestore
   
   Logging and Debugging Options:
     -d, --debug           print debug messages
     -v, --verbose         verbose output (INFO level)
   ```

   **Note:** The file name is required. You can specify the whole path if it's in a different location.

1. Verify the data has being uploaded.


## Troubleshooting

### Authentication Error: "TypeError: 'str' object is not callable"

If you encounter repeated authentication errors with the message:
```
TypeError: 'str' object is not callable
grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with:
    status = StatusCode.UNAVAILABLE
    details = "Getting metadata from plugin failed with error: 'str' object is not callable"
```

**Cause**: Your Google Cloud Application Default Credentials (ADC) are corrupted or in an invalid state.

**Solution**: Re-authenticate using the gcloud CLI:
```bash
gcloud auth application-default login
```

This will refresh your credentials and save them to `~/.config/gcloud/application_default_credentials.json` (Linux/Mac) or `%APPDATA%\gcloud\application_default_credentials.json` (Windows).

After re-authenticating, try running your command again.
