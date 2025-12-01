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

### Installation

1. Create a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install the package:
   ```bash
   pip install .
   ```

3. Authenticate with Google Cloud:
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

Transform flat CSV data into nested structures using `schema.json`.

**CSV** (`questions.csv`):
```csv
DocumentId,id,question,option_a,option_b,option_c,option_d,correct
quiz_1,Q1,What is 2+2?,3,4,5,,b
quiz_1,Q2,Capital of France?,London,Paris,Berlin,Madrid,b
```

**Schema** (`schema.json`):
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
ffload questions.csv
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

## 📖 Documentation

- **[Schema Guide](docs/schema-guide.md)** - Transform flat CSV into nested Firestore structures
- **[Type System](docs/type-system.md)** - Complete reference for all 10 data types and 23 type prefixes
- **[Examples & Best Practices](docs/examples.md)** - Real-world use cases and troubleshooting

## 🔧 CLI Reference

```bash
ffload [OPTIONS] csv_file_path
```

### Options

| Option | Description |
|--------|-------------|
| `csv_file_path` | Path to the CSV file (required) |
| `-c, --collection NAME` | Collection name (defaults to CSV filename without extension) |
| `--local` | Use Firestore emulator at localhost:8080 instead of Cloud Firestore |
| `-v, --verbose` | Enable verbose logging (INFO level) |
| `-d, --debug` | Enable debug logging (DEBUG level with full tracebacks) |
| `-h, --help` | Show help message and exit |

### Examples

```bash
# Basic upload
ffload data.csv

# Custom collection name
ffload data.csv -c my_collection

# Test with local emulator
ffload data.csv --local

# Verbose logging
ffload data.csv -v

# Debug mode (detailed logs)
ffload data.csv -d

# Combine options
ffload data.csv -c products --local -v
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

3. **Schema File** (optional): Create `schema.json` in your working directory for nested structures

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
