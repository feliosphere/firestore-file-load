# 🔥 FirestoreFileLoad

Transform CSV files into structured Firestore documents with schema-driven data mapping.

## 🎯 What It Does

FirestoreFileLoad is a CLI tool that uploads CSV data to Google Firestore with powerful transformation capabilities. It automatically groups related rows, supports all Firestore data types, and can restructure flat CSV data into complex nested documents using a simple JSON schema.

**Current Support**: CSV files only. JSON, Excel, and other formats planned for future releases.

## ✨ Key Features

- **Schema Transformation** - Convert flat CSV rows into nested JSON structures with `schema.json`
- **Smart Type System** - Supports all 10 Firestore data types with 23 prefix keywords and automatic detection
- **Automatic Grouping** - Multiple CSV rows with the same DocumentId merge into a single document
- **Local Emulator Support** - Test uploads safely before deploying to production
- **Type Safety** - Column-level type hints, value-level prefixes, or automatic type detection

## 🚀 Quick Start

### CLI Installation

1. Create a Python virtual environment of your choice (e.g., `venv`, `conda`, `pipenv`). For example, using `venv`:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install the package:
   ```bash
   pip install .
   ```

3. Authenticate with Google Cloud (see also [Google Cloud Setup](#-google-cloud-setup)):
   ```bash
   gcloud auth application-default login
   ```

### Your First Upload

**Simple CSV** (`products.csv`):
```csv
DocumentId,name,price:float,in_stock:bool
prod_1,Widget,19.99,true
prod_2,Gadget,29.99,false
```

**Upload to Firestore**:
```bash
ffload products.csv
```

**Result**: Collection `products` with 2 documents, each containing name, price (float), and in_stock (boolean) fields.

### With Schema Transformation

Transform flat CSV data into nested structures using a JSON schema file. The schema file name should match your CSV file (e.g., `questions.json` for `questions.csv`), or you can specify a custom path with `-s`.

**CSV** (`questions.csv`):
```csv
DocumentId,id,question,option_a,option_b,option_c,option_d,correct
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
    "correct_option_id": "correct"
  }
}
```

**Upload**:
```bash
# Schema file auto-detected as questions.json
ffload questions.csv

# Or explicitly specify schema
ffload questions.csv -s questions.json
```

**Result** - Document `quiz_1`:
```json
{
  "Q1": {
    "question": "What is 2+2?",
    "options": [
      {"id": "a", "text": "3"},
      {"id": "b", "text": "4"},
      {"id": "c", "text": "5"}
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

Notice: Q1's empty option_d was automatically filtered out!

### Multi-Level Nested Maps (Advanced)

Create deeply nested map structures using recursive `key_column` definitions in your schema. This is perfect for hierarchical data like categories, world levels, or nested taxonomies.

**CSV** (`worlds.csv`):
```csv
DocumentId,worlds,world_num,title,questions_list
toyCL,world_a,1,World 11,question_list1
toyCL,world_a,2,World 12,question_list2
toyCL,world_b,1,World 21,question_list3
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

**Result** - Document `toyCL`:
```json
{
  "world_a": {
    "1": {
      "course_id": "toyCL",
      "title": "World 11",
      "questions_list": "question_list1"
    },
    "2": {
      "course_id": "toyCL",
      "title": "World 12",
      "questions_list": "question_list2"
    }
  },
  "world_b": {
    "1": {
      "course_id": "toyCL",
      "title": "World 21",
      "questions_list": "question_list3"
    }
  }
}
```

**Key Features**:
- Supports arbitrary nesting depth (2, 3, or more levels)
- Keys maintain their original type (integers stay as integers, strings as strings)
- Combine with lists and all other schema features
- Perfect for hierarchical data structures

## 📖 Documentation

- **[Schema Guide](docs/schema-guide.md)** - Transform flat CSV into nested Firestore structures
- **[Type System](docs/type-system.md)** - Complete reference for all 10 data types and 23 type prefixes
- **[Examples & Best Practices](docs/examples.md)** - Real-world use cases and troubleshooting

## 🔧 CLI Reference

```bash
ffload [OPTIONS] csv_file_path
```

### Options

#### File Inputs
| Option | Description |
|--------|-------------|
| `csv_file_path` | Path to the CSV file (required) |
| `-s, --schema PATH` | Path to JSON schema file (defaults to `[csv_filename].json`) |

#### Collection Options
| Option | Description |
|--------|-------------|
| `-c, --collection NAME` | Collection name (defaults to CSV filename without extension) |
| `--merge` / `--no-merge` | Merge with existing documents or overwrite (default: `--merge`) |

#### Connection Options
| Option | Description |
|--------|-------------|
| `--local` | Use Firestore emulator at localhost:8080 instead of Cloud Firestore |

#### Logging and Debugging Options
| Option | Description |
|--------|-------------|
| `-v, --verbose` | Enable verbose logging (INFO level) |
| `-d, --debug` | Enable debug logging (DEBUG level with full tracebacks) |
| `-h, --help` | Show help message and exit |

### Examples

```bash
# Basic upload (auto-detects data.json as schema)
ffload data.csv

# Custom collection name
ffload data.csv -c my_collection

# Explicit schema file
ffload data.csv -s custom_schema.json

# Overwrite existing documents instead of merging
ffload data.csv --no-merge

# Test with local emulator
ffload data.csv --local

# Verbose logging
ffload data.csv -v

# Debug mode (detailed logs)
ffload data.csv -d

# Combine options
ffload data.csv -c products -s product_schema.json --merge --local -v
```

## 🔐 Google Cloud Setup

### Prerequisites

1. **Create a Service Account** in Google Cloud Console:
   - Navigate to IAM & Admin → Service Accounts
   - Create a new service account with Firestore access
   - Grant the "Cloud Datastore User" role

2. **Install gcloud CLI**: Follow the [official installation guide](https://cloud.google.com/sdk/docs/install)

3. **Set Your Project**:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

4. **Authenticate**:
   ```bash
   gcloud auth application-default login
   ```

### Troubleshooting Authentication

If you see `TypeError: 'str' object is not callable` or authentication errors, refresh your credentials:

```bash
gcloud auth application-default login
```

For more detailed troubleshooting, see the [Examples & Best Practices](docs/examples.md#troubleshooting) documentation.

## 📋 CSV Requirements

1. **DocumentId Column** (required): First column must be named `DocumentId` (case-sensitive)
   ```csv
   DocumentId,name,value
   doc1,Alice,100
   ```

2. **Type Hints** (optional): Specify types in column headers or values
   ```csv
   DocumentId,age:int,price:float,active:bool
   user1,25,29.99,true
   ```

3. **Schema File** (optional): 
   - Auto-detected: `[csv_filename].json` (e.g., `data.csv` → `data.json`)
   - Custom path: Use `-s` flag (e.g., `-s custom_schema.json`)
   - Enables transformation of flat CSV into nested Firestore structures

## 💡 Common Use Cases

### Simple Data Upload
One CSV row = one Firestore document (flat structure)

### Automatic Grouping
Multiple CSV rows with the same `DocumentId` → single document with `items` array

### Schema-Driven Transformation
Flat CSV columns → nested Firestore documents with custom structure defined in `schema.json`

See [Examples & Best Practices](docs/examples.md) for detailed use cases.

## 📄 License

MIT License - Copyright (c) 2025 Felipe Paucar

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 🔗 Links

- **Documentation**: [Schema Guide](docs/schema-guide.md) | [Type System](docs/type-system.md) | [Examples](docs/examples.md)
- **Repository**: [GitHub](https://github.com/feliosphere/firestore-file-load)
- **Issues**: [Report a bug](https://github.com/feliosphere/firestore-file-load/issues)
