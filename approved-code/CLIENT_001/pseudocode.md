### Pseudocode Transformation Plan for CLIENT_001

#### 1. Data Reading and Initial Validation

1. Read the transactions file provided by the client.
2. Check that the file contains all required columns as per the mapping spreadsheet.
3. Confirm that the column headers are present in the first row and match the expected names.
4. Validate that key fields (such as Account Number, Security Identifiers, Fund Number, and Dates) are not missing or null.
5. Ensure all date fields are in the mm/dd/yyyy format.
6. Check for duplicate column names and rename if necessary.
7. Remove any report titles, blank rows, or subtotals from the data.

#### 2. Column Mapping and Renaming

8. Map each client column to the DNAV target field as specified in the mapping spreadsheet:
    - Map 'Account Number' to 'R_IDFUND' (Internal Fund ID).
    - Map 'Security ISIN' to 'A_ISIN' (International Security Identifier).
    - Map 'Security Number (CUSIP/CINS)' to 'A_CUSIP' (CUSIP).
    - Map 'Security Distribution SEDOL' to 'A_SEDOL' (SEDOL).
    - Map 'Country of Risk Code' to 'A_GEOG' (Country).
    - Map 'Coupon Rate' to 'A_COUPON_RATE'.
    - Map 'Transaction Code' to 'T_TYPE' (Transaction Type).
    - Map 'Transaction Trade Broker' to 'A_COUNTER_PARTY' (Broker Name).
    - Map 'Shares/Par' to 'A_AMOUNT' (Quantity).
    - Map 'Currency Code-Trade' to 'A_CURR' (Currency).
    - Map 'Actual Settle Date' to 'A_SETTLE_DATE'.
    - Map 'Trade Date' to 'A_TRADE_DATE'.
    - Map 'Amortization (Local)' to 'A_AMORTIZATION_ACCRETION_AC'.
    - Map 'Cost Amortized Base' to 'A_BVALUE_AMORTIZED_LTD_AC'.
    - Map 'Cost-Basis-Transaction' to 'A_BVALUE_AC'.
    - Map 'Base Income (All Asset Groups)' to 'A_INCOME'.
    - Map 'Shares Outstanding Total Fund' to 'V_OUTTS' (Shares Outstanding).
    - Map 'Base Receivable Current Value' and 'Payable Curr Value (Base)' as required for receivables/payables.
    - Map other fields as needed per the mapping spreadsheet.

9. Use the mapping tabs for A_TYPE, T_TYPE, and A_GEOG to convert client-specific codes to DNAV standard codes.

#### 3. Calculations and Derived Columns

10. For fields that require calculation:
    - Calculate 'A_AMORTIZATION_ACCRETION_AC' as: Amortized Costs ('Cost Amortized Base') minus Current Costs ('Cost-Basis-Transaction').
    - Calculate 'A_BOOKPRICE_AC' as:
        - If 'A_QUOTETYPE' is "NOM", then ABS(100 * 'Cost-Basis-Transaction' / 'Shares/Par').
        - Otherwise, ABS('Cost-Basis-Transaction' / 'Shares/Par').
    - Calculate 'A_BOOKPRICE_AMORTIZED_LTD_AC' as:
        - If 'A_QUOTETYPE' is "NOM", then 100 * ABS('Cost Amortized Base' / 'Shares/Par').
        - Otherwise, ABS('Cost Amortized Base' / 'Shares/Par').
    - Calculate Net Asset Value (NAV) if required as: (Total Assets - Total Liabilities) / Shares Outstanding.

#### 4. Filtering and Business Rules

11. Filter out any rows where:
    - The 'TS-REV-FLAG' indicates a reversal (e.g., "R") or matches any reversal codes listed in the REVERSALS tab.
    - The 'Transaction Code' or 'Transaction Class Code' is not relevant for DNAV (as per T_TYPE mapping).
    - The 'Account Class' is not "0" (if only master fund data is required).
    - Any critical fields are missing or null (as per Data Integrity Checklist).
12. For multi-share class funds, aggregate or define composite totals for V_NAV, V_OUTTS, V_VPS as needed.

#### 5. Output Format and Destination

13. Prepare the final output file with DNAV field names as column headers.
14. Ensure all mapped and calculated fields are included and formatted correctly.
15. Output the transformed data to the required destination (e.g., DNAV template, CSV, or Excel file).
16. Provide a summary of any data issues or exceptions encountered during transformation.

---

**Notes for Auditor Review:**
- All steps above are based on the mapping spreadsheet and data integrity checklist.
- Calculations and mappings use the definitions provided in the mapping tabs.
- Filtering rules ensure only valid, non-reversed, and complete transactions are included.
- Output is structured for DNAV ingestion and audit review.