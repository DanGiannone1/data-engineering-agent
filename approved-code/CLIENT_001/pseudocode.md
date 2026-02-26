### Pseudocode Transformation Plan for Fund Transaction Data

#### 1. Data Reading and Initial Validation

1.1. **Read the transactions file** provided by the client, ensuring all rows and columns are imported.

1.2. **Check for consistent report format**:
  - Confirm that the file structure (columns and headers) matches the expected template for both current and prior year data.
  - Ensure headers are in the first row, with no blank rows, report titles, or subtotals present.

1.3. **Validate key fields**:
  - Ensure there are **no null values** in the following columns:
    - Fund Number (`Account Number` or `R_IDFUND`)
    - Security Identifiers (`Security ISIN`, `Security Number (CUSIP/CINS)`, etc.)
    - Report End Date (`Request To Date` or `AS_OF_DATE`)
  - Confirm that currency fields (e.g., `Currency Code-Trade`, `Currency Code-Settle`) are present, not null, and use 3-letter codes.
  - Check that date fields are in `mm/dd/yyyy` format.

1.4. **Remove duplicate column names** if any are found.

#### 2. Column Mapping and Renaming

2.1. **Map and rename columns** from the client file to the required DNAV fields, as per the mapping spreadsheet. For example:
  - Map `Account Number` to `R_IDFUND`
  - Map `Security ISIN` to `A_ISIN`
  - Map `Security Number (CUSIP/CINS)` to `A_CUSIP`
  - Map `Trade Date` to `T_TRADE_DATE`
  - Map `Transaction Code` to `T_TYPE` (using the provided T_TYPE mapping tab)
  - Map `Currency Code-Trade` to `A_CURR`
  - Map `Base Income (All Asset Groups)` to `A_AMOUNT`
  - Map `Coupon Rate` to `A_COUPON_RATE`
  - Map `Country of Risk Code` to `A_GEOG`
  - Map `Transaction Class Code` to `T_CLASS`
  - Map `Actual Settle Date` to `T_SETTLE_DATE`
  - Map `Shares/Par` to `A_SHARES_PAR`
  - Map `Cost-Basis-Transaction` to `A_COST_BASIS`
  - Map `Realized Gain and Loss Transaction` to `A_REALIZED_GL`
  - Map `Amortization (Local)` to `A_AMORTIZATION`
  - Map `Transaction Trade Broker` to `A_BROKER`
  - Map `Memo Number` to `A_MEMO_NUMBER`
  - Map `Generated Transaction` to `A_GEN_TRAN_FLAG`
  - Map `TS-REV-FLAG` to `A_REVERSAL_FLAG`

2.2. **Standardize values** in mapped columns using reference tabs:
  - Use the `A_TYPE`, `T_TYPE`, and `A_GEOG` mapping tabs to convert client-specific codes to DNAV standard codes.
  - For transaction types, if not a corporate action, map to either `DT_BUY` or `DT_SELL` as per instructions.

#### 3. Calculations and Derived Columns

3.1. **Calculate Net Asset Value (if required)**:
  - If needed, calculate Net Asset Value as:  
    `(Total Assets - Total Liabilities) / Shares Outstanding`
  - Use relevant columns such as `Base Receivable Current Value`, `Payable Curr Value (Base)`, and `Shares Outstanding Total Fund`.

3.2. **Calculate Realized Gain/Loss**:
  - Use `Realized Gain and Loss Transaction` and related columns for reporting realized gains or losses.

3.3. **Calculate Amortization/Accretion**:
  - Use `Amortization (Local)` and `Amortization Transaction (Basis Currency)` as required.

#### 4. Filtering and Business Rules

4.1. **Filter out reversal transactions**:
  - Use the `TS-REV-FLAG` column and the `REVERSALS` tab to identify and exclude reversal transactions from the main dataset, unless specifically required for audit.

4.2. **Filter by Account Class (if applicable)**:
  - If processing Fund Volumes, filter rows where `Account Class` equals 0 to get master fund data.

4.3. **Remove rows with missing required fields**:
  - Exclude any rows missing key identifiers or required data as per the Data Integrity Checklist.

4.4. **Ensure only recognized security identifiers**:
  - Check that all security identifiers are valid (Bloomberg ID, CUSIP, ISIN, SEDOL, LoanX, or LPC LIN) as per the Security Identifiers tab.

#### 5. Output Format and Destination

5.1. **Prepare output files** for each required DNAV tab:
  - Account Balances
  - Fund Volumes
  - Fund Holdings
  - Fund Holdings Lot
  - Fund Transactions
  - Fund Income
  - Fund Custody
  - Futures (if applicable)
  - Forwards (if applicable)
  - Loans (if applicable)
  - Fund Properties
  - Fund Properties Details

5.2. **Ensure output matches required column order and naming** as per the mapping spreadsheet.

5.3. **Save the transformed data** in the agreed format (e.g., Excel, CSV), with each DNAV tab as a separate worksheet or file as required.

5.4. **Document any data issues or exceptions** (e.g., missing identifiers, unrecognized codes) for auditor review.

---

**Note:**  
- All steps should be performed in accordance with the Data Integrity Checklist provided in the mapping spreadsheet.
- Any deviations or data quality issues should be clearly noted and communicated to the audit team.