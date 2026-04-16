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
        'json': ['.json'],
        'parquet': ['.parquet'],
        'excel': ['.xlsx', '.xls'],
        'pickle': ['.pkl', '.pickle']
    }
    expected = mapping.get(storage_type, [])

    if ext and ext not in expected:
        console.print(
            f"[bold red]ERROR:[/bold red] Extension mismatch! Storage type is '{storage_type}' but file has '{ext}' extension.")
        console.print("To change formats, use the 'convert' command instead.")
        raise typer.Exit(code=1)


def load_input(source: str):
    """Autodetect format based on extension or stdin."""
    if source == 'stdin':
        return pd.read_csv(sys.stdin)

    if not os.path.exists(source):
        raise FileNotFoundError(f"Source file not found: {source}")

    ext = os.path.splitext(source)[1].lower()
    if ext == '.json':
        return pd.read_json(source)
    elif ext in ['.xls', '.xlsx']:
        return pd.read_excel(source)
    elif ext == '.parquet':
        return pd.read_parquet(source)
    elif ext in ['.pkl', '.pickle']:
        return pd.read_pickle(source)
    else:
        return pd.read_csv(source)


def normalize_timestamp(df: pd.DataFrame):
    """
    Ensures 'timestamp' is the first column, formatted in ISO 8601 UTC.
    Validates existing timestamps or generates a new one if missing.
    """
    if df.empty:
        return df

    if 'timestamp' in df.columns:
        # Convert to datetime objects and handle errors
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

        # Normalize timezone to UTC
        if df['timestamp'].dt.tz is None:
            df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        else:
            df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')

        # Fill unparseable dates with current UTC time
        df['timestamp'] = df['timestamp'].fillna(datetime.now(timezone.utc))
    else:
        # Generate new UTC timestamp if missing
        df.insert(0, 'timestamp', datetime.now(timezone.utc))

    # Force strict ISO 8601 string format
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    # Ensure 'timestamp' is physically the first column
    cols = ['timestamp'] + [c for c in df.columns if c != 'timestamp']
    return df[cols]


def save_output(df: pd.DataFrame, path: str, storage_type: str):
    """Handles persistence logic using Read-Modify-Write or direct Append."""
    file_exists = os.path.isfile(path)

    if storage_type == 'csv':
        df.to_csv(path, mode='a', index=False, header=not file_exists)
        return

    if file_exists:
        # Strict loading based on storage_type
        try:
            if storage_type == 'json':
                existing_df = pd.read_json(path)
            elif storage_type == 'parquet':
                existing_df = pd.read_parquet(path)
            elif storage_type in ['excel', 'xlsx']:
                existing_df = pd.read_excel(path)
            elif storage_type == 'pickle':
                existing_df = pd.read_pickle(path)
            else:
                existing_df = pd.read_csv(path)

            df = pd.concat([existing_df, df], ignore_index=True)
        except Exception as e:
            # Abort operation to prevent overwriting/corrupting existing data
            console.print(f"[bold red]CRITICAL ERROR:[/bold red] Could not read existing database: {e}")
            console.print("Operation aborted to prevent data loss.")
            sys.exit(1)

    if storage_type == 'json':
        df.to_json(path, orient='records', indent=4)
    elif storage_type == 'parquet':
        df.to_parquet(path, index=False)
    elif storage_type in ['excel', 'xlsx']:
        df.to_excel(path, index=False)
    elif storage_type == 'pickle':
        df.to_pickle(path)


@app.command()
def append(
        storage_type: str = typer.Argument(..., help="Target storage format: csv, json, parquet, excel, pickle"),
        input_path: str = typer.Argument(..., help="Path to input file or use 'stdin' for pipes"),
        output_path: str = typer.Argument(..., help="Path to the destination database file"),
):
    """
    Appends new metrics to a storage file with automated timestamp validation and ISO 8601 normalization.
    """
    # --- VALIDATION (Outside try-except to avoid double error tags) ---
    if os.path.exists(input_path) and os.path.abspath(input_path) == os.path.abspath(output_path):
        console.print("[bold red]ERROR:[/bold red] Input and Output paths are identical. Self-appending is prohibited.")
        raise typer.Exit(code=1)

    validate_storage_extension(output_path, storage_type.lower())

    # --- PROCESSING ---
    try:
        new_df = load_input(input_path)

        if new_df.empty:
            console.print("[bold yellow]NOTICE:[/bold yellow] Input is empty. No records to process.")
            return

        new_df = normalize_timestamp(new_df)
        save_output(new_df, output_path, storage_type.lower())

        console.print(
            f"[bold green]SUCCESS:[/bold green] Processed {len(new_df)} records into {storage_type.upper()} store.")

    except Exception as e:
        console.print(f"[bold red]INTERNAL ERROR:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def convert(
        storage_type: str = typer.Argument(..., help="TARGET storage engine: csv, json, parquet, excel, pickle"),
        input_path: str = typer.Argument(..., help="Source database file to convert"),
        output_path: str = typer.Argument(..., help="Destination file path"),
):
    """
    Converts an existing time-series database between different storage formats.
    """
    validate_storage_extension(output_path, storage_type.lower())

    try:
        df = load_input(input_path)
        if df.empty:
            raise ValueError("Source file is empty.")

        save_output(df, output_path, storage_type.lower())
        console.print(f"[bold green]SUCCESS:[/bold green] Database converted to {storage_type.upper()}.")
    except Exception as e:
        console.print(f"[bold red]CONVERSION ERROR:[/bold red] {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()