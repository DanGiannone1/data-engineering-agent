import io, pandas as pd, logging
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, DoubleType, IntegerType, LongType, DateType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("transform")

INPUT_PATH = "abfss://data@deagentstorage2026.dfs.core.windows.net/CLIENT_001/transactions.xlsx"
OUTPUT_PATH = "abfss://output@deagentstorage2026.dfs.core.windows.net/CLIENT_001/20260226_131316"

# --- BEGIN TRANSFORM_CONFIG ---
TRANSFORM_CONFIG = {
    "column_renames": {
        "Account Number": "R_IDFUND",
        "Security ISIN": "A_ISIN",
        "Security Number (CUSIP/CINS)": "A_CUSIP",
        "Trade Date": "T_TRADE_DATE",
        "Transaction Code": "T_TYPE",
        "Currency Code-Trade": "A_CURR",
        "Base Income (All Asset Groups)": "A_AMOUNT",
        "Coupon Rate": "A_COUPON_RATE",
        "Country of Risk Code": "A_GEOG",
        "Transaction Class Code": "T_CLASS",
        "Actual Settle Date": "T_SETTLE_DATE",
        "Shares/Par": "A_SHARES_PAR",
        "Cost-Basis-Transaction": "A_COST_BASIS",
        "Realized Gain and Loss Transaction": "A_REALIZED_GL",
        "Amortization (Local)": "A_AMORTIZATION",
        "Transaction Trade Broker": "A_BROKER",
        "Memo Number": "A_MEMO_NUMBER",
        "Generated Transaction": "A_GEN_TRAN_FLAG",
        "TS-REV-FLAG": "A_REVERSAL_FLAG",
        "Request To Date": "AS_OF_DATE"
    },
    "code_mappings": {
        "A_GEOG": {},
        "T_TYPE": {},
        "A_CURR": {},
        "T_CLASS": {},
        "A_GEN_TRAN_FLAG": {},
        "A_REVERSAL_FLAG": {}
    },
    "calculated_columns": [
        {
            "name": "V_NAV",
            "expr": "(F.col('Base Receivable Current Value').cast(DoubleType()) - F.col('Payable Curr Value (Base)').cast(DoubleType())) / F.when(F.col('Shares Outstanding Total Fund').isNull(), F.lit(1.0)).otherwise(F.col('Shares Outstanding Total Fund').cast(DoubleType()))",
            "requires": ["Base Receivable Current Value", "Payable Curr Value (Base)", "Shares Outstanding Total Fund"]
        }
    ],
    "filters": [
        {
            "desc": "Exclude reversal transactions",
            "expr": "F.col('A_REVERSAL_FLAG').isNull() | ~F.col('A_REVERSAL_FLAG').isin(['R','REV','REVERSE','REVERSAL'])",
            "requires": ["A_REVERSAL_FLAG"]
        }
    ],
    "require_not_null": [
        "R_IDFUND",
        "A_ISIN",
        "A_CUSIP",
        "AS_OF_DATE",
        "A_CURR"
    ],
    "date_columns": {
        "T_TRADE_DATE": "MM/dd/yyyy",
        "T_SETTLE_DATE": "MM/dd/yyyy",
        "AS_OF_DATE": "MM/dd/yyyy"
    },
    "output_columns": "auto"
}
# --- END TRANSFORM_CONFIG ---

# STEP 1: Read input
def clean_column_names(cols):
    seen = {}; result = []
    for c in cols:
        n = seen.get(c, 0)
        result.append(f"{c}_{n}" if n > 0 else c)
        seen[c] = n + 1
    return result

if INPUT_PATH.lower().endswith((".xlsx", ".xlsm", ".xls")):
    raw = spark.read.format("binaryFile").load(INPUT_PATH).collect()[0]["content"]
    pdf = pd.read_excel(io.BytesIO(raw), engine="openpyxl")
    pdf = pdf.dropna(how="all")
    pdf.columns = clean_column_names(list(pdf.columns))
    df = spark.createDataFrame(pdf)
elif INPUT_PATH.lower().endswith(".csv"):
    df = spark.read.csv(INPUT_PATH, header=True, inferSchema=True)
else:
    raise ValueError(f"Unsupported format: {INPUT_PATH}")

logger.info(f"Loaded {df.count()} rows, {len(df.columns)} columns")

# STEP 2: Column renames
for src, tgt in TRANSFORM_CONFIG.get("column_renames", {}).items():
    if src in df.columns:
        df = df.withColumnRenamed(src, tgt)

# STEP 3: Code mappings
def _map_udf(d):
    def fn(v): return None if v is None else d.get(v, v)
    return F.udf(fn, StringType())

for col_name, mapping in TRANSFORM_CONFIG.get("code_mappings", {}).items():
    if col_name in df.columns and mapping:
        df = df.withColumn(col_name, _map_udf(mapping)(F.col(col_name)))

# STEP 4: Calculated columns
_ns = {"F": F, "col": F.col, "lit": F.lit, "StringType": StringType,
       "DoubleType": DoubleType, "IntegerType": IntegerType, "__builtins__": {}}

for calc in TRANSFORM_CONFIG.get("calculated_columns", []):
    req = calc.get("requires", [])
    if all(c in df.columns for c in req):
        df = df.withColumn(calc["name"], eval(calc["expr"], _ns))
    else:
        logger.warning(f"Skipping calc '{calc['name']}': missing {[c for c in req if c not in df.columns]}")

# STEP 5: Filters
for filt in TRANSFORM_CONFIG.get("filters", []):
    req = filt.get("requires", [])
    if all(c in df.columns for c in req):
        df = df.filter(eval(filt["expr"], _ns))

for col_name in TRANSFORM_CONFIG.get("require_not_null", []):
    if col_name in df.columns:
        df = df.filter(F.col(col_name).isNotNull())

# STEP 6: Date formatting
for col_name, src_fmt in TRANSFORM_CONFIG.get("date_columns", {}).items():
    if col_name in df.columns:
        df = df.withColumn(col_name,
            F.date_format(F.to_date(F.col(col_name).cast("string"), src_fmt), "MM/dd/yyyy"))

# STEP 7: Select output columns + write parquet
out_spec = TRANSFORM_CONFIG.get("output_columns", "auto")
if out_spec == "auto":
    out_cols = list(TRANSFORM_CONFIG.get("column_renames", {}).values())
    for calc in TRANSFORM_CONFIG.get("calculated_columns", []):
        if calc["name"] not in out_cols and calc["name"] in df.columns:
            out_cols.append(calc["name"])
else:
    out_cols = out_spec

final_cols = [c for c in out_cols if c in df.columns]
final_df = df.select(final_cols)

logger.info(f"Writing {final_df.count()} rows, {len(final_cols)} columns to {OUTPUT_PATH}")
final_df.write.mode("overwrite").parquet(OUTPUT_PATH)
logger.info("Transform complete.")