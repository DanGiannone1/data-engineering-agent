"""Claude Code v2 - Actually be an agent, adapt to what we see."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dotenv import load_dotenv
load_dotenv()

import clients.adls as adls_module
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

def get_adls_client_cli():
    account_name = os.environ['ADLS_ACCOUNT_NAME']
    return DataLakeServiceClient(
        account_url=f'https://{account_name}.dfs.core.windows.net',
        credential=AzureCliCredential(process_timeout=60),
    )
adls_module.get_adls_client = get_adls_client_cli

from tools.adls import read_mapping_spreadsheet, read_spark_output
from tools.databricks import submit_spark_job, wait_for_spark_job

print("=" * 60)
print("Claude Code v2 - Adaptive Agent")
print("=" * 60)

# Step 1: Read mapping and LOOK at what we get
print("\n[1] Reading mapping...")
mapping = read_mapping_spreadsheet('TEST_CLIENT/mapping.xlsx')
sheet_name = list(mapping.keys())[0]
rows = mapping[sheet_name]['sample_rows']
columns = mapping[sheet_name]['columns']
print(f"    Sheet: {sheet_name}, Columns: {columns}")

# Step 2: Adapt to actual column names
src_col = [c for c in columns if 'source' in c.lower()][0]
tgt_col = [c for c in columns if 'target' in c.lower()][0]
rule_col = [c for c in columns if 'transform' in c.lower()][0]
print(f"    Detected: source='{src_col}', target='{tgt_col}', rule='{rule_col}'")

# Step 3: Generate PySpark
storage = os.environ['ADLS_ACCOUNT_NAME']
input_path = f"abfss://data@{storage}.dfs.core.windows.net/TEST_CLIENT/transactions.csv"
output_path = f"abfss://output@{storage}.dfs.core.windows.net/TEST_CLIENT/output_claude"

code = f'''
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType

df = spark.read.option("header", True).option("inferSchema", True).csv("{input_path}")
'''

for row in rows:
    src = row[src_col]
    tgt = row[tgt_col]
    rule = row[rule_col].lower()

    if 'uppercase' in rule:
        code += f'df = df.withColumn("{tgt}", F.upper(F.col("{src}")))\n'
    elif 'date' in rule or 'yyyy' in rule:
        code += f'df = df.withColumn("{tgt}", F.date_format(F.to_date(F.col("{src}")), "yyyy-MM-dd"))\n'
    elif 'round' in rule or 'decimal' in rule:
        code += f'df = df.withColumn("{tgt}", F.round(F.col("{src}"), 2).cast(DecimalType(18,2)))\n'
    elif 'map:' in rule or 'map ' in rule:
        code += f'df = df.withColumn("{tgt}", F.when(F.lower(F.col("{src}"))=="completed", 1).when(F.lower(F.col("{src}"))=="pending", 2).when(F.lower(F.col("{src}"))=="failed", 3).otherwise(None))\n'
    else:
        code += f'df = df.withColumn("{tgt}", F.col("{src}"))\n'

target_cols = [row[tgt_col] for row in rows]
code += f'''
output_df = df.select({target_cols})
output_df.write.mode("overwrite").parquet("{output_path}")
print(f"Wrote {{output_df.count()}} rows")
'''

print("\n[2] Generated PySpark:")
for line in code.strip().split('\n')[:10]:
    print(f"    {line}")
print("    ...")

# Step 4: Submit and wait
print("\n[3] Submitting Spark job...")
run_id = submit_spark_job(code, "TEST_CLIENT")
print(f"    Run ID: {run_id}")

print("\n[4] Waiting for completion...")
result = wait_for_spark_job(run_id, poll_interval=15, timeout=600)
print(f"    Result: {result['result_state']}")

# Step 5: Verify
if result['success']:
    print("\n[5] Verifying output...")
    output = read_spark_output('TEST_CLIENT/output_claude', 5)
    print(f"    Rows: {output['row_count']}")
    print(f"    Columns: {output['columns']}")
    print(f"    Sample: {output['sample_rows'][0]}")
    print("\n✓ SUCCESS")
else:
    print(f"\n✗ FAILED: {result['error_log'][:300]}")

print("=" * 60)
