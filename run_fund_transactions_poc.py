"""
Fund Transactions POC - Test MAF agent with complete context.

Give the agent:
1. Fund Transactions field mapping
2. A_TYPE lookup table
3. T_TYPE lookup table
4. REVERSALS (cancel codes)
5. Source data sample

See if it can generate PySpark that matches the reference patterns.
"""

import asyncio
import json
import os
import sys
from typing import Annotated

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from agent_framework import Agent, tool
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential
import pandas as pd


# =============================================================================
# Tools - Read from DNAV Data Dictionary
# =============================================================================

@tool
def read_fund_transactions_mapping() -> str:
    """Read the Fund Transactions field mapping from DNAV Data Dictionary.
    Returns mapping of DNAV fields to client fields with transformation notes."""
    df = pd.read_excel('input_data/JG Copy of DNAV Data Dictionary.xlsx',
                       sheet_name='Fund Transactions', header=6)

    mappings = []
    for _, row in df.iterrows():
        dnav_field = row.get('DNAV Field', '')
        if pd.isna(dnav_field) or not dnav_field:
            continue

        mapping = {
            'dnav_field': str(dnav_field).strip(),
            'description': str(row.get('DNAV Field Description', '')).strip(),
            'data_type': str(row.get('Data Type', '')).strip(),
            'client_field': str(row.get('Client Field', '')).strip(),
            'source_file': str(row.get('Field Source File ', '')).strip(),
            'formula_notes': str(row.get('Field Notes', '')).strip(),
            'required': str(row.get('Requirement Level', '')).strip()
        }
        mappings.append(mapping)

    return json.dumps(mappings, indent=2, default=str)


@tool
def read_a_type_lookup() -> str:
    """Read A_TYPE lookup table - maps client asset types to DNAV asset types.
    Example: 'COMMON STOCK' -> 'EQT', 'CORPORATE BONDS' -> 'BON'"""
    df = pd.read_excel('input_data/JG Copy of DNAV Data Dictionary.xlsx',
                       sheet_name='A_TYPE')

    # Find the actual data rows (skip header rows)
    # Looking for columns: Client A_TYPE, DNAV A_TYPE
    lookups = []
    for _, row in df.iterrows():
        client_type = row.get('Unnamed: 4', '')  # Client A_TYPE column
        dnav_type = row.get('Unnamed: 5', '')    # DNAV A_TYPE column

        if pd.notna(client_type) and pd.notna(dnav_type) and client_type and dnav_type:
            if client_type not in ['Client A_TYPE', 'Client Field A_TYPE Mapping']:
                lookups.append({
                    'client_a_type': str(client_type).strip(),
                    'dnav_a_type': str(dnav_type).strip()
                })

    return json.dumps(lookups, indent=2)


@tool
def read_t_type_lookup() -> str:
    """Read T_TYPE lookup table - maps client transaction codes to DNAV transaction types.
    Example: 'BUY' -> 'DT_BUY', 'SELL' -> 'DT_SELL'"""
    df = pd.read_excel('input_data/JG Copy of DNAV Data Dictionary.xlsx',
                       sheet_name='T_TYPE')

    lookups = []
    for _, row in df.iterrows():
        client_type = row.get('Unnamed: 4', '')  # T_TYPE_CLIENT
        dnav_type = row.get('Unnamed: 6', '')    # DNAV T_TYPE

        if pd.notna(client_type) and pd.notna(dnav_type) and client_type and dnav_type:
            if client_type not in ['T_TYPE_CLIENT', 'Client T_TYPE Mapping']:
                lookups.append({
                    'client_t_type': str(client_type).strip(),
                    'dnav_t_type': str(dnav_type).strip()
                })

    return json.dumps(lookups, indent=2)


@tool
def read_reversal_codes() -> str:
    """Read REVERSALS - transaction codes that indicate cancelled/reversed transactions.
    If T_TYPE_CLIENT starts with any of these codes, DT_FL_CANCELLED = 1."""
    df = pd.read_excel('input_data/JG Copy of DNAV Data Dictionary.xlsx',
                       sheet_name='REVERSALS')

    codes = df['Name'].dropna().tolist()
    return json.dumps({'reversal_codes': codes, 'count': len(codes)})


@tool
def read_source_data_sample(n_rows: Annotated[int, "Number of rows to sample"] = 5) -> str:
    """Read sample rows from Effective_Transactions source file."""
    df = pd.read_csv('input_data/Effective_Transactions_sample.csv', nrows=n_rows)

    result = {
        'columns': list(df.columns),
        'column_count': len(df.columns),
        'sample_rows': df.head(n_rows).to_dict(orient='records')
    }
    return json.dumps(result, indent=2, default=str)


@tool
def list_source_columns() -> str:
    """List all column names in the source file."""
    df = pd.read_csv('input_data/Effective_Transactions_sample.csv', nrows=1)
    return json.dumps({'columns': list(df.columns), 'count': len(df.columns)})


@tool
def save_generated_code(
    code: Annotated[str, "Complete PySpark transformation code"],
    description: Annotated[str, "Brief description"]
) -> str:
    """Save generated PySpark code to file."""
    output_path = 'input_data/generated_fund_transactions.py'
    with open(output_path, 'w') as f:
        f.write(f'# {description}\n')
        f.write('# Generated by MAF Agent - Fund Transactions POC\n\n')
        f.write(code)

    return json.dumps({'status': 'saved', 'path': output_path})


# =============================================================================
# Agent Setup
# =============================================================================

AGENT_INSTRUCTIONS = """You are a data engineering agent that transforms client Fund Transactions data into DNAV format.

## Your Task
Generate production-ready PySpark code that transforms Effective_Transactions data into DNAV Fund Transactions format.

## Available Tools
1. read_fund_transactions_mapping() - Get DNAV field mappings
2. read_a_type_lookup() - Get asset type mapping (Client -> DNAV like EQT, BON)
3. read_t_type_lookup() - Get transaction type mapping (Client -> DNAV like DT_BUY, DT_SELL)
4. read_reversal_codes() - Get list of reversal/cancel transaction codes
5. read_source_data_sample() - Sample the source data
6. list_source_columns() - List all source columns
7. save_generated_code() - Save the final PySpark code

## Required Transformation Patterns

### 1. Field Mapping
- Map source columns to DNAV fields using the mapping table
- Handle fuzzy column name matching (source names may vary slightly)

### 2. Asset Type Join (A_TYPE)
- Join with A_TYPE lookup to get DNAV_A_TYPE
- Filter out: CSH, N/A, OTH, SWP asset types

### 3. Transaction Type Join (T_TYPE)
- Join with T_TYPE lookup to get DNAV_T_TYPE (DT_BUY, DT_SELL, DT_CA_IN, DT_CA_OUT)
- Filter out: N/A transaction types

### 4. Cancel Detection (DT_FL_CANCELLED)
- Set DT_FL_CANCELLED = 1 if transaction code matches any reversal code
- Also check for codes starting with 'R' that indicate reversals

### 5. Amount Sign Logic (T_AMOUNT)
- DT_SELL, DT_CA_OUT: T_AMOUNT should be negative (use -abs())
- DT_BUY, DT_CA_IN: T_AMOUNT should be positive (use abs())
- If A_LONGSHORT = 1 (short position), reverse the sign

### 6. FX Rate Handling
- If T_FXRATE = 0, set to 1 (avoid division by zero)

### 7. Identifier Validation
- A_CUSIP: valid if length = 9
- A_ISIN: valid if length = 12
- A_SEDOL: valid if length = 7
- A_KEYTYPE: derive from A_IDINT length (9=CUSIP, 12=ISIN, 7=SEDOL, else=INT)

## Code Structure
Generate a function like:
```python
def transform_fund_transactions(spark, input_path, a_type_lookup_path, t_type_lookup_path, reversal_codes):
    # 1. Read source data
    # 2. Map fields to DNAV schema
    # 3. Join with A_TYPE lookup
    # 4. Join with T_TYPE lookup
    # 5. Apply cancel detection
    # 6. Apply amount sign logic
    # 7. Validate identifiers
    # 8. Select final DNAV columns
    return dnav_df
```

Think step by step:
1. First read all the mapping/lookup tables
2. Then sample the source data to understand column names
3. Generate complete PySpark code following the patterns above
"""


def get_chat_client() -> AzureOpenAIChatClient:
    return AzureOpenAIChatClient(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        credential=AzureCliCredential(process_timeout=60),
        api_version="2025-01-01-preview",
    )


def create_agent() -> Agent:
    client = get_chat_client()

    return Agent(
        client=client,
        name="FundTransactionsTransformer",
        instructions=AGENT_INSTRUCTIONS,
        tools=[
            read_fund_transactions_mapping,
            read_a_type_lookup,
            read_t_type_lookup,
            read_reversal_codes,
            read_source_data_sample,
            list_source_columns,
            save_generated_code,
        ],
    )


# =============================================================================
# Main
# =============================================================================

async def main():
    print("=" * 70)
    print("Fund Transactions POC - MAF Agent Test")
    print("=" * 70)

    agent = create_agent()
    thread = agent.get_new_thread()

    user_request = """Transform Fund Transactions data from Effective_Transactions source file.

Please:
1. Read all the lookup tables (A_TYPE, T_TYPE, REVERSALS)
2. Read the Fund Transactions field mapping
3. Sample the source data to see actual column names
4. Generate PySpark code that:
   - Maps source fields to DNAV schema
   - Joins with A_TYPE and T_TYPE lookups
   - Detects cancelled transactions
   - Applies correct sign logic for T_AMOUNT
   - Validates identifier lengths
   - Handles edge cases (FX rate = 0, nulls, etc.)

Focus on fields from 'Effective_Transactions' source only (not 'Recalculate' fields).
Generate production-ready code following the patterns in my instructions.
"""

    print(f"\nRequest: Generate Fund Transactions transformation")
    print("=" * 70)

    response = await agent.run(user_request, thread=thread)

    print("\n" + "=" * 70)
    print("AGENT RESPONSE")
    print("=" * 70)

    if hasattr(response, 'text') and response.text:
        print(response.text)

    # Show tool calls
    if hasattr(response, 'messages') and response.messages:
        print("\n--- TOOL CALLS ---")
        for msg in response.messages:
            if hasattr(msg, 'contents') and msg.contents:
                for content in msg.contents:
                    if hasattr(content, 'name') and content.name:
                        print(f"  [{content.name}]")


if __name__ == "__main__":
    asyncio.run(main())
