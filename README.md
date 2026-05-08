# OctoTS Metrics Processor

GitHub Action for collecting and storing code metrics as a time series in a dedicated branch.

This action processes input data and appends it to a persistent dataset stored in a separate empty branch (default: `metrics-data`).

## Usage

```yaml
- name: Run OctoTS Metrics Processor
  uses: OctoTS/OctoTS-action@v1
  with:
    format: csv
    input: temp.csv
    output: metrics.csv
    branch: my-metrics-branch
```
## Inputs

| Name     | Required | Default        | Description                                                                             |
| -------- | -------- | -------------- | --------------------------------------------------------------------------------------- |
| `format` | ❌ No     | `csv`          | Storage engine (see supported formats below)                                            |
| `input`  | ✅ Yes    | —              | Path to the input file                                                                  |
| `output` | ✅ Yes    | —              | Path to the output file where metrics will be stored                                    |
| `branch` | ❌ No     | `metrics-data` | Target branch where metrics are stored                                                  |

## Supported Storage Engines
| Category | Formats |
| :--- | :--- |
| Time Series | CSV, TSV, JSON, JSONL |
| Documents | HTML, XML, YAML |
| Spreadsheet | Excel |
| Big Data | Parquet, Feather, HDF5, Pickle, NetCDF, MessagePack, CBOR, ORC |
| Databases | SQL / SQLite |

## Input File Requirements
The input data must be in a tabular format with a header row (column names). If a CSV/Excel file does not contain a header, the first row will be treated as column names (which may result in data loss).

The action will automatically:
  - add a `timestamp` column (ISO 8601 UTC)
  - place it as the first column

Supported input formats (auto-detected by file extension):
  - .csv (default)
  - .txt
  - .tsv
  - .json
  - .jsonl, .ndjson
  - .yaml, .yml
  - .xlsx, .xls
  - .parquet
  - .feather, .ftr
  - .h5, .hdf5
  - .xml
  - .html, .htm
  - .nc, .nc4, .cdf
  - .msgpack, .mpack
  - .sql, .db, .sqlite
  - .pkl, .pickle
  - .orc

**Example of valid input:**
CSV
```csv
author,lines_of_code
John Doe,120
Jane Smith,45
```
JSON
```json
[
  {"author": "John Doe", "lines_of_code": 125},
  {"author": "Jane Smith", "lines_of_code": 42}
]
```
JSONL
```json
{"author": "John Doe", "lines_of_code": 125}
{"author": "Jane Smith", "lines_of_code": 42}
```
