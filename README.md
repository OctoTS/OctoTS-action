# OctoTS Metrics Processor

GitHub Action for collecting and storing code metrics as a time series in a dedicated branch.

This action processes input data and appends it to a persistent dataset stored in a separate branch (default: `metrics-data`).

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
| `format` | ❌ No     | `csv`          | Output storage format: `csv`, `json`, `parquet`, `excel`, `pickle`                      |
| `input`  | ✅ Yes    | —              | Path to the input file (CSV, JSON, Excel, Parquet, Pickle supported via auto-detection) |
| `output` | ✅ Yes    | —              | Path to the output file where metrics will be stored                                    |
| `branch` | ❌ No     | `metrics-data` | Target branch where metrics are stored                                                  |
