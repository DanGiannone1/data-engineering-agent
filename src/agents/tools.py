"""MAF tools for data access - Fund Transactions transformation."""

import json
from typing import Annotated
from pathlib import Path

import pandas as pd
from agent_framework import tool

# Base path for input data
INPUT_DIR = Path(__file__).parent.parent.parent / "input_data"


@tool
def read_fund_transactions_mapping() -> str:
    """Read the Fund Transactions field mapping from DNAV Data Dictionary.
    Returns mapping of DNAV fields to client fields with transformation notes."""
    df = pd.read_excel(
        INPUT_DIR / "JG Copy of DNAV Data Dictionary.xlsx",
        sheet_name="Fund Transactions",
        header=6,
    )

    mappings = []
    for _, row in df.iterrows():
        dnav_field = row.get("DNAV Field", "")
        if pd.isna(dnav_field) or not dnav_field:
            continue

        mapping = {
            "dnav_field": str(dnav_field).strip(),
            "description": str(row.get("DNAV Field Description", "")).strip(),
            "data_type": str(row.get("Data Type", "")).strip(),
            "client_field": str(row.get("Client Field", "")).strip(),
            "source_file": str(row.get("Field Source File ", "")).strip(),
            "formula_notes": str(row.get("Field Notes", "")).strip(),
            "required": str(row.get("Requirement Level", "")).strip(),
        }
        mappings.append(mapping)

    return json.dumps(mappings, indent=2, default=str)


@tool
def read_a_type_lookup() -> str:
    """Read A_TYPE lookup table - maps client asset types to DNAV asset types.
    Example: 'COMMON STOCK' -> 'EQT', 'CORPORATE BONDS' -> 'BON'"""
    df = pd.read_excel(
        INPUT_DIR / "JG Copy of DNAV Data Dictionary.xlsx",
        sheet_name="A_TYPE",
    )

    lookups = []
    for _, row in df.iterrows():
        client_type = row.get("Unnamed: 4", "")
        dnav_type = row.get("Unnamed: 5", "")

        if pd.notna(client_type) and pd.notna(dnav_type) and client_type and dnav_type:
            if client_type not in ["Client A_TYPE", "Client Field A_TYPE Mapping"]:
                lookups.append({
                    "client_a_type": str(client_type).strip(),
                    "dnav_a_type": str(dnav_type).strip(),
                })

    return json.dumps(lookups, indent=2)


@tool
def read_t_type_lookup() -> str:
    """Read T_TYPE lookup table - maps client transaction codes to DNAV transaction types.
    Example: 'BUY' -> 'DT_BUY', 'SELL' -> 'DT_SELL'"""
    df = pd.read_excel(
        INPUT_DIR / "JG Copy of DNAV Data Dictionary.xlsx",
        sheet_name="T_TYPE",
    )

    lookups = []
    for _, row in df.iterrows():
        client_type = row.get("Unnamed: 4", "")
        dnav_type = row.get("Unnamed: 6", "")

        if pd.notna(client_type) and pd.notna(dnav_type) and client_type and dnav_type:
            if client_type not in ["T_TYPE_CLIENT", "Client T_TYPE Mapping"]:
                lookups.append({
                    "client_t_type": str(client_type).strip(),
                    "dnav_t_type": str(dnav_type).strip(),
                })

    return json.dumps(lookups, indent=2)


@tool
def read_reversal_codes() -> str:
    """Read REVERSALS - transaction codes that indicate cancelled/reversed transactions.
    If T_TYPE_CLIENT starts with any of these codes, DT_FL_CANCELLED = 1."""
    df = pd.read_excel(
        INPUT_DIR / "JG Copy of DNAV Data Dictionary.xlsx",
        sheet_name="REVERSALS",
    )

    codes = df["Name"].dropna().tolist()
    return json.dumps({"reversal_codes": codes, "count": len(codes)})


@tool
def read_source_data_sample(
    n_rows: Annotated[int, "Number of rows to sample"] = 10
) -> str:
    """Read sample rows from Effective_Transactions source file."""
    df = pd.read_csv(INPUT_DIR / "Effective_Transactions_sample.csv", nrows=n_rows)

    result = {
        "columns": list(df.columns),
        "column_count": len(df.columns),
        "row_count": n_rows,
        "sample_rows": df.head(n_rows).to_dict(orient="records"),
    }
    return json.dumps(result, indent=2, default=str)


@tool
def list_source_columns() -> str:
    """List all column names in the source file with their data types."""
    df = pd.read_csv(INPUT_DIR / "Effective_Transactions_sample.csv", nrows=5)

    columns = []
    for col in df.columns:
        columns.append({
            "name": col,
            "dtype": str(df[col].dtype),
            "sample_value": str(df[col].iloc[0]) if len(df) > 0 else None,
        })

    return json.dumps({"columns": columns, "count": len(columns)}, indent=2)


@tool
def get_data_profile() -> str:
    """Get a statistical profile of the source data (nulls, uniques, distributions)."""
    df = pd.read_csv(INPUT_DIR / "Effective_Transactions_sample.csv")

    profile = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": [],
    }

    for col in df.columns[:50]:  # Limit to first 50 columns
        col_info = {
            "name": col,
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "null_pct": round(df[col].isnull().sum() / len(df) * 100, 1),
            "unique_count": int(df[col].nunique()),
        }

        if df[col].dtype == "object":
            top_values = df[col].value_counts().head(3).to_dict()
            col_info["top_values"] = {str(k): v for k, v in top_values.items()}

        profile["columns"].append(col_info)

    return json.dumps(profile, indent=2, default=str)
