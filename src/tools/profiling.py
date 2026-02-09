"""Data profiling tool — generates column-level statistics for LLM prompts."""

import pandas as pd


def profile_data(data: dict) -> dict:
    """Compute column-level statistics from sampled data.

    Args:
        data: Dict with "columns", "sample_rows" (as returned by sample_source_data).

    Returns:
        Dict with per-column profile: type, null_rate, unique_count, min, max,
        top_values, and anomaly flags.
    """
    df = pd.DataFrame(data["sample_rows"])

    if df.empty:
        return {"columns": {}, "row_count": 0, "anomalies": []}

    profile = {}
    anomalies = []

    for col in df.columns:
        series = df[col]
        col_profile = {
            "dtype": str(series.dtype),
            "null_count": int(series.isna().sum()),
            "null_rate": round(float(series.isna().mean()), 3),
            "unique_count": int(series.nunique()),
        }

        non_null = series.dropna()
        if len(non_null) > 0:
            if pd.api.types.is_numeric_dtype(series):
                col_profile["min"] = float(non_null.min())
                col_profile["max"] = float(non_null.max())
                col_profile["mean"] = round(float(non_null.mean()), 2)
            else:
                top = non_null.value_counts().head(5)
                col_profile["top_values"] = {str(k): int(v) for k, v in top.items()}

        # Flag anomalies
        if col_profile["null_rate"] > 0.5:
            anomalies.append(f"Column '{col}' has >50% nulls ({col_profile['null_rate']:.0%})")

        if col_profile["unique_count"] == 1 and len(non_null) > 1:
            anomalies.append(f"Column '{col}' has only 1 unique value (constant)")

        profile[col] = col_profile

    return {
        "columns": profile,
        "row_count": len(df),
        "total_columns": len(df.columns),
        "anomalies": anomalies,
    }
