import typer
import sys
import os
import pandas as pd
from datetime import datetime, timezone
from typing import Optional
from rich.console import Console

app = typer.Typer(
    help="OctoTS Batch Processor",
    no_args_is_help=True
)
console = Console()


def validate_storage_extension(path: str, storage_type: str):
    """Strictly validates if the file extension matches the storage engine."""
    ext = os.path.splitext(path)[1].lower()
    mapping = {
        'csv': ['.csv', '.txt'],
        'tsv': ['.tsv'],
        'json': ['.json'],
        'jsonl': ['.jsonl', '.ndjson'],
        'excel': ['.xlsx', '.xls'],
        'parquet': ['.parquet'],
        'feather': ['.feather', '.ftr'],
        'hdf5': ['.h5', '.hdf5'],
        'xml': ['.xml'],
        'html': ['.html', '.htm'],
        'md': ['.md', '.markdown'],
        'sql': ['.sql', '.db', '.sqlite'],
        'pickle': ['.pkl', '.pickle'],
        'latex': ['.tex']
    }
    expected = mapping.get(storage_type, [])

    if ext and ext not in expected:
        console.print(
            f"[bold red]ERROR:[/bold red] Extension mismatch! Storage is '{storage_type}' but file is '{ext}'.")
        console.print("To change formats, use the 'convert' command.")
        raise typer.Exit(code=1)


def load_input(source: str):
    """Autodetect format and load into a DataFrame."""
    if source == 'stdin':
        return pd.read_csv(sys.stdin)

    if not os.path.exists(source):
        raise FileNotFoundError(f"Source file not found: {source}")

    ext = os.path.splitext(source)[1].lower()

    if ext == '.json':
        return pd.read_json(source)
    elif ext in ['.jsonl', '.ndjson']:
        return pd.read_json(source, lines=True)
    elif ext in ['.xls', '.xlsx']:
        return pd.read_excel(source)
    elif ext == '.parquet':
        return pd.read_parquet(source)
    elif ext in ['.pkl', '.pickle']:
        return pd.read_pickle(source)
    elif ext in ['.feather', '.ftr']:
        return pd.read_feather(source)
    elif ext in ['.h5', '.hdf5']:
        return pd.read_hdf(source, key='metrics')
    elif ext == '.xml':
        return pd.read_xml(source)
    elif ext == '.tsv':
        return pd.read_csv(source, sep='\t')
    else:
        return pd.read_csv(source)


def normalize_timestamp(df: pd.DataFrame):
    """Ensures strict ISO 8601 UTC format as the first column (Index 0)."""
    if df.empty:
        return df

    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        if df['timestamp'].dt.tz is None:
            df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        else:
            df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
        df['timestamp'] = df['timestamp'].fillna(datetime.now(timezone.utc))
    else:
        df.insert(0, 'timestamp', datetime.now(timezone.utc))

    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    cols = ['timestamp'] + [c for c in df.columns if c != 'timestamp']
    return df[cols]


def save_output(df: pd.DataFrame, path: str, storage_type: str):
    """Persistence layer using direct append or Read-Modify-Write logic."""
    file_exists = os.path.isfile(path)

    # Native append for text-based time series
    if storage_type == 'csv':
        df.to_csv(path, mode='a', index=False, header=not file_exists)
        return
    if storage_type == 'tsv':
        df.to_csv(path, mode='a', index=False, sep='\t', header=not file_exists)
        return
    if storage_type == 'jsonl':
        # Ensure file ends with newline before appending new JSON objects
        if storage_type == 'jsonl':
            # Simple append for JSON Lines
            df.to_json(path, mode='a', orient='records', lines=True)
            return

    # Read-Modify-Write for binary/structured formats
    if file_exists:
        try:
            existing_df = load_input(path)
            df = pd.concat([existing_df, df], ignore_index=True)
        except Exception as e:
            console.print(f"[bold red]CRITICAL ERROR:[/bold red] Database corrupted: {e}")
            sys.exit(1)

    if storage_type == 'json':
        df.to_json(path, orient='records', indent=4)
    elif storage_type == 'parquet':
        df.to_parquet(path, index=False)
    elif storage_type in ['excel', 'xlsx']:
        df.to_excel(path, index=False)
    elif storage_type == 'xml':
        df.to_xml(path, index=False)
    elif storage_type == 'feather':
        df.to_feather(path)
    elif storage_type == 'hdf5':
        df.to_hdf(path, key='metrics', mode='w')
    elif storage_type == 'pickle':
        df.to_pickle(path)
    elif storage_type == 'html':
        df.to_html(path, index=False)
    elif storage_type == 'md':
        df.to_markdown(path, index=False)
    elif storage_type == 'latex':
        df.to_latex(path, index=False)
    elif storage_type == 'sql':
        # Uses SQLite as a local file-based SQL database
        import sqlite3
        conn = sqlite3.connect(path)
        df.to_sql('metrics', conn, if_exists='replace', index=False)
        conn.close()


@app.command()
def append(
        storage_type: str = typer.Argument(..., help="Engine: csv, tsv, json, jsonl, excel, parquet, etc."),
        input_path: str = typer.Argument(..., help="Input source (file path or 'stdin')"),
        output_path: str = typer.Argument(..., help="Destination database file path"),
):
    """Process incoming metrics and append them to a persistent time-series storage."""
    if os.path.exists(input_path) and os.path.abspath(input_path) == os.path.abspath(output_path):
        console.print("[bold red]ERROR:[/bold red] Cannot append a file to itself.")
        raise typer.Exit(code=1)

    validate_storage_extension(output_path, storage_type.lower())

    try:
        new_df = load_input(input_path)
        if new_df.empty:
            console.print("[yellow]NOTICE:[/yellow] Input empty. Skipping.")
            return

        new_df = normalize_timestamp(new_df)
        save_output(new_df, output_path, storage_type.lower())
        console.print(f"[bold green]SUCCESS:[/bold green] Added to {storage_type.upper()} storage.")
    except Exception as e:
        console.print(f"[bold red]INTERNAL ERROR:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def convert(
        storage_type: str = typer.Argument(..., help="Target storage format"),
        input_path: str = typer.Argument(..., help="Source database to convert"),
        output_path: str = typer.Argument(..., help="Path for the new database"),
):
    """Convert an existing database to a new format while preserving timestamp integrity."""
    validate_storage_extension(output_path, storage_type.lower())
    try:
        df = load_input(input_path)
        if df.empty: raise ValueError("Source is empty.")
        df = normalize_timestamp(df)
        save_output(df, output_path, storage_type.lower())
        console.print(f"[bold green]SUCCESS:[/bold green] Converted to {storage_type.upper()}.")
    except Exception as e:
        console.print(f"[bold red]CONVERSION ERROR:[/bold red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()