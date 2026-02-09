"""ADLS tools for reading mapping spreadsheets, sampling data, and reading output."""

import io
import openpyxl
import pandas as pd
from clients.adls import download_file, list_files


def read_mapping_spreadsheet(path: str) -> dict:
    """Download Excel mapping from ADLS and return structured column mappings.

    Args:
        path: Path within the 'mappings' container (e.g. "CLIENT_001/mapping.xlsx").

    Returns:
        Dict with sheet names as keys, each containing columns and sample rows.
    """
    data = download_file("mappings", path)
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)

    result = {}
    for sheet_name in wb.sheetnames:
        df = pd.read_excel(io.BytesIO(data), sheet_name=sheet_name)
        result[sheet_name] = {
            "columns": list(df.columns),
            "row_count": len(df),
            "sample_rows": df.head(10).to_dict(orient="records"),
        }

    return result


def sample_source_data(path: str, n_rows: int = 100) -> dict:
    """Read first N rows from source data file in ADLS.

    Args:
        path: Path within the 'data' container (e.g. "CLIENT_001/transactions.csv").

    Returns:
        Dict with columns, row_count, and sample rows.
    """
    data = download_file("data", path)

    if path.endswith(".parquet"):
        df = pd.read_parquet(io.BytesIO(data))
    elif path.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(data), nrows=n_rows)
    else:
        df = pd.read_excel(io.BytesIO(data), nrows=n_rows)

    sample = df.head(n_rows)
    return {
        "columns": list(sample.columns),
        "dtypes": {col: str(dtype) for col, dtype in sample.dtypes.items()},
        "row_count": len(df),
        "sample_rows": sample.to_dict(orient="records"),
    }


def read_spark_output(path: str, n_rows: int = 50) -> dict:
    """Read Spark output from ADLS for validation.

    Handles both single files and Spark output directories (multiple part files).

    Args:
        path: Path within the 'output' container (e.g. "CLIENT_001/20260207").

    Returns:
        Dict with columns, row_count, and sample rows.
    """
    # Try to list files in the path (Spark typically writes a directory of part files)
    try:
        files = list_files("output", prefix=path)
        parquet_files = [f for f in files if f.endswith(".parquet") and not f.startswith("_")]

        if parquet_files:
            # Read the first parquet part file for validation
            data = download_file("output", parquet_files[0])
            df = pd.read_parquet(io.BytesIO(data))
            sample = df.head(n_rows)
            return {
                "columns": list(sample.columns),
                "dtypes": {col: str(dtype) for col, dtype in sample.dtypes.items()},
                "row_count": len(df),
                "sample_rows": sample.to_dict(orient="records"),
                "part_file_count": len(parquet_files),
            }
    except Exception:
        pass

    # Fallback: try reading as a single file
    data = download_file("output", path)
    if path.endswith(".parquet"):
        df = pd.read_parquet(io.BytesIO(data))
    else:
        df = pd.read_csv(io.BytesIO(data))

    sample = df.head(n_rows)
    return {
        "columns": list(sample.columns),
        "dtypes": {col: str(dtype) for col, dtype in sample.dtypes.items()},
        "row_count": len(df),
        "sample_rows": sample.to_dict(orient="records"),
    }
