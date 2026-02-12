"""Local file reading utilities."""

import os
import pandas as pd
from pathlib import Path

# Base path for input data
INPUT_DATA_DIR = Path(__file__).parent.parent.parent / "input_data"


def read_transactions(filename: str = "Effective_Transactions_sample.csv") -> pd.DataFrame:
    """Read the MAF transactions file."""
    path = INPUT_DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Transactions file not found: {path}")
    return pd.read_csv(path)


def read_mapping(filename: str = "JG Copy of DNAV Data Dictionary.xlsx") -> dict:
    """Read the DNAV mapping spreadsheet."""
    path = INPUT_DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Mapping file not found: {path}")

    # Read all sheets
    xlsx = pd.ExcelFile(path)
    sheets = {}
    for sheet_name in xlsx.sheet_names:
        df = pd.read_excel(xlsx, sheet_name=sheet_name)
        sheets[sheet_name] = df.to_dict(orient="records")

    return sheets


def sample_data(df: pd.DataFrame, n_rows: int = 20) -> dict:
    """Get a sample of data for LLM context."""
    return {
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "sample_rows": df.head(n_rows).to_dict(orient="records"),
        "null_counts": df.isnull().sum().to_dict(),
    }


def profile_data(df: pd.DataFrame) -> dict:
    """Generate a data profile for the LLM."""
    profile = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": [],
    }

    for col in df.columns:
        col_profile = {
            "name": col,
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "null_pct": round(df[col].isnull().sum() / len(df) * 100, 1),
            "unique_count": int(df[col].nunique()),
        }

        # Add sample values for non-numeric columns
        if df[col].dtype == "object":
            top_values = df[col].value_counts().head(5).to_dict()
            col_profile["top_values"] = {str(k): v for k, v in top_values.items()}

        profile["columns"].append(col_profile)

    return profile
