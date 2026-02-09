import io
import pandas as pd
import logging
from pyspark.sql import functions as F
from pyspark.sql.types import StringType
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CLIENT_001_Transactions_Transform")

input_path = "abfss://data@deagentstorage.dfs.core.windows.net/CLIENT_001/transactions.xlsx"
output_path = "abfss://output@deagentstorage.dfs.core.windows.net/CLIENT_001/20260208_034059"

expected_columns = [
    "UserBank", "Client Id", "Account Requested", "Request To Date", "Request From Date", "Security Ticker Symbol",
    "Purchased/Sold Interest Option", "Security Distribution SEDOL", "Local Receivable Current Value", "Security ISIN",
    "Payable Curr Value (Local)", "Asset Event Reference", "Security Number (CUSIP/CINS)", "Base Receivable Current Value",
    "Payable Curr Value (Base)", "Base Income (All Asset Groups)", "Tax Rate", "Ex-Date Payment", "Shares/Par (Ex-Date)",
    "Transaction Dividend Interest Rate", "Security Asset Group Base", "Accrued Income Gross Local", "Account Number",
    "Amortization (Local)", "Actual Settle Date", "Advisor Code", "Advisor Descrption", "Transaction Trade Broker",
    "Settle Currency Code Recv", "Settle Currency Code Pay", "Base Receivable", "Payable (base)", "Local Receivable",
    "Cost Amortized Base", "Cost-Basis-Transaction", "Amortization Transaction (Basis Currency)", "Payable (Local)",
    "Transaction Code", "CGT Country", "Enhanced Currency Contract Contract Rate", "Commission (Local)",
    "Country of Risk Code", "Cost-Local-Transaction", "Coupon Rate", "Contractual Settle Date", "Security Contract Type",
    "Security Number", "Shares/Par", "Security Contract Size", "Security Long Description Line 01", "Dealing Expense",
    "Income/Expense Main Category", "Income Category Code Main And Sub", "Effective Date Transaction", "Expiration Date",
    "Income Equalization-Transaction", "Total Realized FX Gain/Loss", "Realized Exchange Gain/Loss on Debt Securities-Transaction",
    "Realized Exchange Gain/Loss on Income-Transaction", "Realized Exchange Gain/Loss on Amort/Accret", "Trade Expense",
    "Franked/Unfranked Indicator", "Trade Exchange Rate (Base)", "Settle Base Exchange Rate (Rounded 6)", "Trade Base Amount",
    "Settle Base Amount", "Currency Code-Settle", "Settle Amount", "Commission (Base)", "Principal Base", "Income Base Transaction",
    "Realized Gain and Loss Transaction", "Realized Gain and Loss (Base)", "General Ledger Code", "Realized Exchange Gain and Loss Non Bifurcated",
    "Realized Gain and Loss Total", "Security User Defined Field 33", "Hedge Type", "Income Local Transaction",
    "Security User Defined Field 44", "Currency Code-Income", "Corporate Action Description 2", "Corporate Action Type",
    "Corporate Action Ex-Date", "Corporate Action Payable Date", "Corporatate Action Effective Date", "Corporate Action Receiving/Deliver Security",
    "Trade Date Exchange Rate", "Trade Date Equalization Rate", "Realized Capital Gain/Loss", "Realized Exchange Gain/Loss",
    "Currency Contract Type", "Security Category Code Level (Segment)", "Category Code Level (Category)", "Category Code Level Sector",
    "Security Category Code", "Bond Maturity Date", "Market Value Traded", "Underlying Security Number", "Over-the-Counter Flag",
    "Price-Base-Transaction", "Price-Local-Transaction", "Trade Expense (BASE)", "Rebook Cross Reference Memo",
    "Reversal Cross Reference Memo Number", "Security Short Name", "Class Of Shares (Expense)", "Long or Short Position",
    "Security Number Full", "Securities Sold Receivable-Basis-Transaction", "Security Qualifier", "Securities Purchased Payable Basis",
    "Broker Code (Executing)", "Currency Code-Trade", "Trade Date", "Transaction Class Code", "Memo Number", "Principal Local",
    "Realized Gain and Loss", "Country of Taxation", "Rate", "Unrealized Exchange Gain/Loss on Principal (Transaction)",
    "Unrealized Exchange Gain/Loss on Income (Transaction)", "Real FX GL on Rec Pay", "Shares Outstanding Total Fund",
    "Segment Description", "Category Description", "Sector Description", "Industry Description", "Transaction Average Unit Cost (Base)",
    "Cost Amortized Local", "Security Long Description Line 02", "Subscriptions-Transaction", "Subscriptions Exchanged-Transaction",
    "Dividends Reinvested-Transaction", "Redemptions-Transaction", "Redemptions Exchanged-Transaction",
    "Realized Exchange Gain/Loss on Currencies-Transaction", "Issue Currency", "Security User Defined Field 70",
    "Issue Currency Exchange Rate", "Security User Defined Field 79", "Unrealized Exchange Gain/Loss on Other Receivables",
    "Unrealized Exchange Gain/Loss on Other Payables (Transaction)", "Security User Defined Field 123", "Income and Other Payables",
    "Income and Other Receivables", "Reclaim Receivable Basis Transaction", "Total Unrealized Exchange Gain/Loss (Transaction)",
    "Inflation Comp Purch/Sold", "Tran User Defined Afield 10", "Traded MV (Base)", "Bond Code", "Currency Contract Receivables",
    "Currency Contract Payables", "CCT Trading Currency", "Security Description (Long 3)", "Security Description (Long 4)",
    "Tran User Defined Date 1", "Tran User Defined Flag 1", "Tran User Defined Nfield 6", "Request To Date.1",
    "External Memo Number", "Request From Date.1", "Generated Transaction", "Settle Unrounded FX Rate (Base)",
    "Total Realized FX Gain/Loss on To Date", "Currency Realized FX Gain/Loss on To Date", "Rec/Pay Realized FX Gain/Loss on To Date",
    "Income Currency FX Rate (Position)", "Corp Action Mandatory/Optional", "Corp Action Cost Factor", "Corp Action Pro-Ration Rate",
    "Corp Action Price", "Corp Action Cash Rate", "Corp Action Share Ratio", "Corp Action Shares For", "Corp Action Discount Rate",
    "Corp Action Fract Shares Indicator", "Prior Dividend Transaction Eff Date", "Prior Dividend Transaction Income",
    "Corporate Action Gen Tran Flag", "Corporate Action Receiving Security", "Strike Price", "User Defined Afield 67",
    "User Defined Afield 110", "Underlying Security CUSIP", "Underlying Security Qualifier", "Capital Shares Redeemed Pay",
    "Pay Date", "Earned Income (Base)", "CUSIP (Pricing) Number", "Put/Call Flag", "State Code", "Tran Description 1",
    "Tran Description 2", "Tran Description 3", "Tran Description 4", "Trading Currency FX Rate (Position)", "Tax Status",
    "User Defined Afield 20", "Wash Sale Cross Ref Memo", "Ex-Date", "Account Underlying Security", "GST Reclaimable Trade (Base)",
    "Variation Margin Recv", "Realized F/X Gain/Loss (Settle Date)", "Variation Margin Payable", "Realized F/X Gain/Loss (Effective Date)",
    "TS-REV-FLAG", "Issue Date", "Issue Price", "Effective Maturity Price", "Bond Payment Frequency", "Bond Coupon Date (First)",
    "Accrual Method", "FX G/L On Amort", "Index Ratio", "Acct User Defined Afield 43", "Bond Amortization", "Tran User Defined Afield 8",
    "View Indicator", "Tax Flag", "Transaction Description Code", "User Defined Asset Group", "User Defined Afield 59",
    "User Defined Afield 90", "User Defined Afield 118", "Standard & Poors Rating", "Infl Comp Base", "Infl Comp at Trade FX Rate",
    "Broker Domicile Country", "Security LEI", "Transfer Cost"
]

column_mapping = {
    "Account Number": "R_IDFUND",
    "Security ISIN": "A_ISIN",
    "Security Number (CUSIP/CINS)": "A_CUSIP",
    "Security Distribution SEDOL": "A_SEDOL",
    "Country of Risk Code": "A_GEOG",
    "Coupon Rate": "A_COUPON_RATE",
    "Transaction Code": "T_TYPE",
    "Transaction Trade Broker": "A_COUNTER_PARTY",
    "Shares/Par": "A_AMOUNT",
    "Currency Code-Trade": "A_CURR",
    "Actual Settle Date": "A_SETTLE_DATE",
    "Trade Date": "A_TRADE_DATE",
    "Amortization (Local)": "A_AMORTIZATION_ACCRETION_AC",
    "Cost Amortized Base": "A_BVALUE_AMORTIZED_LTD_AC",
    "Cost-Basis-Transaction": "A_BVALUE_AC",
    "Base Income (All Asset Groups)": "A_INCOME",
    "Shares Outstanding Total Fund": "V_OUTTS",
    "Base Receivable Current Value": "A_RECEIVABLE_BASE",
    "Payable Curr Value (Base)": "A_PAYABLE_BASE"
}

key_fields = [
    "Account Number", "Security ISIN", "Security Number (CUSIP/CINS)", "Shares Outstanding Total Fund",
    "Actual Settle Date", "Trade Date"
]

date_fields = [
    "Actual Settle Date", "Trade Date", "Request To Date", "Request From Date", "Bond Maturity Date",
    "Expiration Date", "Effective Date Transaction", "Ex-Date Payment", "Corporate Action Ex-Date",
    "Corporate Action Payable Date", "Corporatate Action Effective Date", "Issue Date", "Pay Date"
]

reversal_codes = ["R", "REV", "REVERSE", "REVERSAL"]

def validate_date_format(date_str):
    if date_str is None or str(date_str).strip() == "":
        return False
    try:
        datetime.strptime(str(date_str), "%m/%d/%Y")
        return True
    except Exception:
        return False

def clean_column_names(cols):
    seen = {}
    new_cols = []
    for col in cols:
        base = col
        cnt = seen.get(base, 0)
        if cnt > 0:
            new_col = f"{base}_{cnt}"
        else:
            new_col = base
        new_cols.append(new_col)
        seen[base] = cnt + 1
    return new_cols

try:
    logger.info("Reading Excel file from ADLS path")
    data = spark.read.format("binaryFile").load(input_path).collect()[0]["content"]
    pdf = pd.read_excel(io.BytesIO(data), engine="openpyxl")
    pdf = pdf.dropna(how="all")
    pdf = pdf.loc[~pdf.apply(lambda row: row.astype(str).str.contains("Total|Subtotal|Report", case=False).any(), axis=1)]
    pdf.columns = clean_column_names(list(pdf.columns))
    missing_cols = [col for col in expected_columns if col not in pdf.columns]
    if missing_cols:
        logger.error(f"Missing columns in input file: {missing_cols}")
        raise Exception(f"Missing columns: {missing_cols}")
    for k in key_fields:
        if k in pdf.columns and pdf[k].isnull().any():
            logger.error(f"Null values found in key field: {k}")
            raise Exception(f"Null values in key field: {k}")
    for d in date_fields:
        if d in pdf.columns:
            invalid_dates = pdf[~pdf[d].apply(lambda x: validate_date_format(x))]
            if not invalid_dates.empty:
                logger.warning(f"Invalid date format found in column {d}")
    for k in key_fields:
        if k in pdf.columns:
            pdf = pdf[pdf[k].notnull()]
    pdf.columns = clean_column_names(list(pdf.columns))
    df = spark.createDataFrame(pdf)
except Exception as e:
    logger.error(f"Error reading or validating input file: {str(e)}")
    raise

for client_col, dnav_col in column_mapping.items():
    if client_col in df.columns:
        df = df.withColumnRenamed(client_col, dnav_col)

a_type_map = {}
t_type_map = {}
a_geog_map = {}

def map_code_udf(mapping_dict):
    def map_code(val):
        if val is None:
            return None
        return mapping_dict.get(val, val)
    return F.udf(map_code, StringType())

if "A_GEOG" in df.columns:
    df = df.withColumn("A_GEOG", map_code_udf(a_geog_map)(F.col("A_GEOG")))
if "T_TYPE" in df.columns:
    df = df.withColumn("T_TYPE", map_code_udf(t_type_map)(F.col("T_TYPE")))

if "A_BVALUE_AMORTIZED_LTD_AC" in df.columns and "A_BVALUE_AC" in df.columns:
    df = df.withColumn("A_AMORTIZATION_ACCRETION_AC", F.col("A_BVALUE_AMORTIZED_LTD_AC") - F.col("A_BVALUE_AC"))

if "A_BVALUE_AC" in df.columns and "A_AMOUNT" in df.columns:
    if "A_QUOTETYPE" in df.columns:
        df = df.withColumn("A_BOOKPRICE_AC",
            F.when(F.col("A_QUOTETYPE") == "NOM",
                F.abs(100 * F.col("A_BVALUE_AC") / F.col("A_AMOUNT"))
            ).otherwise(
                F.abs(F.col("A_BVALUE_AC") / F.col("A_AMOUNT"))
            )
        )
    else:
        df = df.withColumn("A_BOOKPRICE_AC", F.abs(F.col("A_BVALUE_AC") / F.col("A_AMOUNT")))
if "A_BVALUE_AMORTIZED_LTD_AC" in df.columns and "A_AMOUNT" in df.columns:
    if "A_QUOTETYPE" in df.columns:
        df = df.withColumn("A_BOOKPRICE_AMORTIZED_LTD_AC",
            F.when(F.col("A_QUOTETYPE") == "NOM",
                100 * F.abs(F.col("A_BVALUE_AMORTIZED_LTD_AC") / F.col("A_AMOUNT"))
            ).otherwise(
                F.abs(F.col("A_BVALUE_AMORTIZED_LTD_AC") / F.col("A_AMOUNT"))
            )
        )
    else:
        df = df.withColumn("A_BOOKPRICE_AMORTIZED_LTD_AC", F.abs(F.col("A_BVALUE_AMORTIZED_LTD_AC") / F.col("A_AMOUNT")))

if "V_OUTTS" in df.columns and "A_RECEIVABLE_BASE" in df.columns and "A_PAYABLE_BASE" in df.columns:
    df = df.withColumn("V_NAV", (F.col("A_RECEIVABLE_BASE") - F.col("A_PAYABLE_BASE")) / F.col("V_OUTTS"))

if "TS-REV-FLAG" in df.columns:
    df = df.filter(~F.col("TS-REV-FLAG").isin(reversal_codes))

if "T_TYPE" in df.columns:
    relevant_t_types = [code for code in t_type_map.values() if code is not None]
    if relevant_t_types:
        df = df.filter(F.col("T_TYPE").isin(relevant_t_types))

if "Account Class" in df.columns:
    df = df.filter(F.col("Account Class") == "0")

for dnav_col in ["R_IDFUND", "A_ISIN", "A_CUSIP", "V_OUTTS", "A_SETTLE_DATE", "A_TRADE_DATE"]:
    if dnav_col in df.columns:
        df = df.filter(F.col(dnav_col).isNotNull())

for dnav_col in ["A_SETTLE_DATE", "A_TRADE_DATE"]:
    if dnav_col in df.columns:
        df = df.withColumn(dnav_col, F.date_format(F.to_date(F.col(dnav_col), "MM/dd/yyyy"), "yyyy-MM-dd"))

output_columns = list(column_mapping.values())
for col in ["A_AMORTIZATION_ACCRETION_AC", "A_BOOKPRICE_AC", "A_BOOKPRICE_AMORTIZED_LTD_AC", "V_NAV"]:
    if col in df.columns and col not in output_columns:
        output_columns.append(col)
final_df = df.select([col for col in output_columns if col in df.columns])

try:
    logger.info(f"Writing output to {output_path}")
    final_df.write.mode("overwrite").parquet(output_path)
    logger.info("Transformation and write completed successfully.")
except Exception as e:
    logger.error(f"Error writing output file: {str(e)}")
    raise

issues = []
for k in key_fields:
    mapped_col = column_mapping.get(k, k)
    if mapped_col in df.columns:
        null_count = df.filter(F.col(mapped_col).isNull()).count()
        if null_count > 0:
            issues.append(f"Nulls in {mapped_col}: {null_count}")
for d in date_fields:
    mapped_col = column_mapping.get(d, d)
    if mapped_col in df.columns:
        invalid_count = df.filter(~F.col(mapped_col).rlike(r"\d{4}-\d{2}-\d{2}")).count()
        if invalid_count > 0:
            issues.append(f"Invalid date format in {mapped_col}: {invalid_count}")
if issues:
    logger.warning("Data issues found during transformation:")
    for issue in issues:
        logger.warning(issue)