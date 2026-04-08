# OctoTS Metrics Processor

GitHub Action for collecting and storing code metrics as a time series in a dedicated branch.

This action processes input CSV data and appends it to a persistent dataset stored in a separate branch (default: `metrics-data`).

## Usage

```yaml
- name: Run OctoTS Metrics Processor
  uses: OctoTS/OctoTS-action@v1
  with:
    input: temp.csv
    output: metrics.csv
    branch: my-metrics-branch
```