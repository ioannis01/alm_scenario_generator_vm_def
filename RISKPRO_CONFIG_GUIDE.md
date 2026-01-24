# RiskPro Data Loader Configuration Guide

## 📋 Overview

The `load_alm_data.py` file is designed to load data directly from your RiskPro (OneSumX Risk Management) database based on the contract data model and reporting reference documentation you provided.

---

## 🔧 Step 1: Configure Database Connection

Open `load_alm_data.py` and find the `RiskProConfig` class (around line 50):

```python
class RiskProConfig:
    """Configuration for RiskPro database connection"""
    
    # Database connection settings
    DB_TYPE = "mssql+pyodb"  # Options: "sqlserver", "oracle", "postgresql"
    DB_HOST = "127.0.0.1"
    DB_PORT = 1433
    DB_NAME = "RP_1225"
    DB_USER = "RP_1225"
    DB_PASSWORD = "RP_1225"
    
    # Schema/owner names
    SCHEMA = "dbo"  # or "RISKPRO" for Oracle

    # Table names (OneSumX default naming)
    CONTRACTS_TABLE = "CONTRACT"
    MARKET_OBJECTS_TABLE = "MARKET_OBJECT"
    COUNTERPARTY_TABLE = "COUNTERPARTY"
    # ... etc
    
    # Calculation/reporting date
    VALUATION_DATE = datetime.now().date()  # Or set specific date
```

### Example Configurations:

#### For SQL Server:
```python
DB_TYPE = "sqlserver"
DB_HOST = "riskpro-db.yourcompany.com"
DB_PORT = 1433
DB_NAME = "RISKPRO_PROD"
DB_USER = "riskpro_reader"
DB_PASSWORD = "your_secure_password"
SCHEMA = "dbo"
```

#### For Oracle:
```python
DB_TYPE = "oracle"
DB_HOST = "riskpro-ora.yourcompany.com"
DB_PORT = 1521
DB_NAME = "RISKPRO"  # SID or Service Name
DB_USER = "RISKPRO_USER"
DB_PASSWORD = "your_secure_password"
SCHEMA = "RISKPRO"
```

#### For PostgreSQL:
```python
DB_TYPE = "postgresql"
DB_HOST = "riskpro-pg.yourcompany.com"
DB_PORT = 5432
DB_NAME = "riskpro"
DB_USER = "riskpro_app"
DB_PASSWORD = "your_secure_password"
SCHEMA = "public"
```

---

## 📦 Step 2: Install Database Driver

Based on your database type, install the appropriate Python driver:

### For SQL Server:
```bash
pip install pyodbc
```

### For Oracle:
```bash
pip install cx_Oracle
```

### For PostgreSQL:
```bash
pip install psycopg2-binary
```

---

## 🗂️ Step 3: Verify Table Names

RiskPro table names may vary by installation. Check your database and update if needed:

```python
# Common table names in OneSumX:
CONTRACTS_TABLE = "CONTRACT"              # Contract master data
MARKET_OBJECTS_TABLE = "MARKET_OBJECT"    # Market risk factors
COUNTERPARTY_TABLE = "COUNTERPARTY"       # Counterparty master
RATING_TABLE = "RATING"                   # Rating definitions
YIELD_CURVE_TABLE = "YIELD_CURVE_POINT"   # Yield curve points
SPREAD_CURVE_TABLE = "SPREAD_CURVE_POINT" # Spread curve points
FX_RATE_TABLE = "FX_RATE"                 # FX rates
```

You can query your database to find exact table names:

```sql
-- SQL Server
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME LIKE '%CONTRACT%' OR TABLE_NAME LIKE '%MARKET%';

-- Oracle
SELECT TABLE_NAME FROM ALL_TABLES 
WHERE OWNER = 'RISKPRO' AND TABLE_NAME LIKE '%CONTRACT%';

-- PostgreSQL
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' AND tablename LIKE '%contract%';
```

---

## 🧪 Step 4: Test the Connection

Run the test mode to verify configuration:

```bash
python load_alm_data.py
```

Or test programmatically:

```python
from load_alm_data import load_from_riskpro

# Load a small sample (limit to 100 contracts for testing)
risk_factors, counterparties, contracts = load_from_riskpro(limit_contracts=100)

print(f"Loaded {len(risk_factors)} risk factors")
print(f"Loaded {len(counterparties)} counterparties")
print(f"Loaded {len(contracts)} contracts")

# Inspect first items
print(f"\nFirst yield curve: {risk_factors[0].to_dict()}")
print(f"\nFirst counterparty: {counterparties[0].to_dict()}")
print(f"\nFirst contract: {contracts[0].to_dict()}")
```

---

## 🔗 Step 5: Integrate with Scenario Generator

Update `main.py` to use real RiskPro data:

```python
from alm_scenarios import ALMScenarioGenerator, LlamaClient
from load_alm_data import load_from_riskpro  # ← Add this import

def main():
    print("Loading ALM data from RiskPro...")
    
    # Load real data from RiskPro
    risk_factors, counterparties, contracts = load_from_riskpro()
    
    # Initialize LLM
    llm_client = LlamaClient(base_url="http://localhost:11434")
    generator = ALMScenarioGenerator(llm_client)
    
    # Generate scenarios
    user_instruction = """
    Generate 5 regulatory stress scenarios for Swiss banking (FINMA):
    1. Interest rate shock (+200 bps)
    2. Credit spread widening (+150 bps)
    3. CHF appreciation (-20% EURCHF)
    4. Equity decline (-30%)
    5. Combined adverse scenario
    """
    
    scenarios, df = generator.generate_scenarios(
        risk_factors=risk_factors,
        counterparties=counterparties,
        contracts=contracts,
        user_instruction=user_instruction,
        num_scenarios=5
    )
    
    # Save results
    df.to_csv("riskpro_scenarios.csv", index=False)
    print(f"✓ Generated {len(scenarios)} scenarios")
    print(f"✓ Saved to riskpro_scenarios.csv")

if __name__ == "__main__":
    main()
```

---

## 📊 Data Mapping Details

### Contract Type Mapping

The loader maps RiskPro contract type codes to standard types:

| RiskPro Code | Description | Mapped To |
|--------------|-------------|-----------|
| ANN | Annuity | LOAN |
| PAM | Principal At Maturity | LOAN |
| RGM | Regular Amortizer | LOAN |
| NGM | Negative Amortizer | LOAN |
| DSC | Discount | DEPOSIT |
| BNDIDX | Bond | BOND |
| IRSWP | Interest Rate Swap | SWAP |
| FXSWP | FX Swap | SWAP |
| FXFWD | FX Forward | FORWARD |
| FXOP | FX Option | OPTION |

### Key RiskPro Fields Used

**From CONTRACT table:**
- `CONTRACT_KEY` → contract_id
- `CONTRACT_TYPE` → contract_type
- `CURRENCY` → currency
- `NOTIONAL_PRINCIPAL` → notional
- `MATURITY_DATE` → maturity_date
- `DISCOUNTING_MARKET_OBJECT` → linked_yield_curve
- `CREDIT_SPREAD_CURVE_DEFINITION` → linked_spread_curve
- `COUNTERPARTY_KEY` → counterparty_id

**From COUNTERPARTY table:**
- `COUNTERPARTY_KEY` → counterparty_id
- `COUNTERPARTY_NAME` → name
- `RATING_CLASS` → rating
- `PROBABILITY_OF_DEFAULT` → pd
- `RECOVERY_RATE` → recovery_rate

**From MARKET_OBJECT table:**
- `MARKET_OBJECT_KEY` → factor_id
- `MARKET_OBJECT_NAME` → description
- `CURRENCY` → currency
- Various type-specific fields

---

## 🛠️ Customization

### Loading Specific Portfolios

Filter contracts by portfolio or book:

```python
def load_contracts_by_portfolio(conn, portfolio_id: str, limit: Optional[int] = None):
    # ... existing code ...
    query = f"""
    SELECT ...
    FROM {RiskProConfig.SCHEMA}.{RiskProConfig.CONTRACTS_TABLE} c
    WHERE c.AS_OF_DATE = ?
        AND c.CONTRACT_STATUS = 'ACTIVE'
        AND c.PORTFOLIO_KEY = ?  ← Add portfolio filter
        {rownum_clause}
    """
    
    cursor.execute(query, (RiskProConfig.VALUATION_DATE, portfolio_id))
    # ... rest of code ...
```

### Adding Custom Risk Factors

If you have custom market objects or scenarios:

```python
def load_custom_risk_factors(conn) -> List[RiskFactor]:
    """Load custom risk factors specific to your implementation"""
    custom_factors = []
    
    # Query your custom tables
    cursor = conn.cursor()
    query = "SELECT ... FROM YOUR_CUSTOM_TABLE"
    cursor.execute(query)
    
    for row in cursor.fetchall():
        factor = MacroFactor(
            factor_id=row[0],
            macro_type=row[1],
            current_value=float(row[2])
        )
        custom_factors.append(factor)
    
    return custom_factors
```

---

## 🆘 Troubleshooting

### Connection Issues

**Error: "Can't connect to database"**
```python
# Test connection manually
import pyodbc  # or cx_Oracle or psycopg2

conn_str = RiskProConfig.get_connection_string()
try:
    conn = pyodbc.connect(conn_str)
    print("✓ Connection successful!")
    conn.close()
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

**Error: "Table not found"**
- Check schema name (dbo vs RISKPRO vs public)
- Verify table names in your database
- Check user permissions

### Query Issues

**Error: "Invalid column name"**
- Field names may differ in your RiskPro version
- Check actual column names:
```sql
SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'CONTRACT';
```

**Error: "No data returned"**
- Check `VALUATION_DATE` is correct
- Verify `AS_OF_DATE` field exists and has data
- Check `CONTRACT_STATUS = 'ACTIVE'` filter

### Performance Issues

**Loading is too slow**
- Use `limit_contracts` parameter for testing
- Add database indexes on key fields
- Consider loading in batches
- Filter by specific portfolios

---

## 📝 Example: Complete Workflow

```python
#!/usr/bin/env python
"""
Complete workflow: Load RiskPro data and generate scenarios
"""

from load_alm_data import load_from_riskpro, RiskProConfig
from alm_scenarios import ALMScenarioGenerator, LlamaClient
from datetime import date

# 1. Configure (already done in RiskProConfig class)
print("Configuration:")
print(f"  Database: {RiskProConfig.DB_TYPE}")
print(f"  Host: {RiskProConfig.DB_HOST}")
print(f"  Valuation Date: {RiskProConfig.VALUATION_DATE}")
print()

# 2. Load data from RiskPro
print("Loading data from RiskPro...")
risk_factors, counterparties, contracts = load_from_riskpro()
print(f"✓ Loaded {len(risk_factors)} risk factors")
print(f"✓ Loaded {len(counterparties)} counterparties")
print(f"✓ Loaded {len(contracts)} contracts")
print()

# 3. Initialize LLM
print("Initializing LLM...")
llm_client = LlamaClient(
    base_url="http://localhost:11434",
    model_name="llama3"
)
generator = ALMScenarioGenerator(llm_client)
print("✓ LLM initialized")
print()

# 4. Generate scenarios
print("Generating scenarios...")
scenarios, df = generator.generate_scenarios(
    risk_factors=risk_factors,
    counterparties=counterparties,
    contracts=contracts,
    user_instruction="""
    Generate 3 stress scenarios:
    1. Severe interest rate rise (+250 bps)
    2. Credit crisis (spreads +200 bps, PD +50%)
    3. CHF appreciation (EUR/CHF -15%, USD/CHF -20%)
    """,
    num_scenarios=3
)
print(f"✓ Generated {len(scenarios)} scenarios")
print()

# 5. Review and save
print("Scenarios generated:")
for i, scenario in enumerate(scenarios, 1):
    print(f"  {i}. {scenario.name}")
    print(f"     Shocks: {len(scenario.shocks)}")

df.to_csv("riskpro_scenarios.csv", index=False)
print(f"\n✓ Saved to riskpro_scenarios.csv")
```

---

## 📚 Additional Resources

- **RiskPro Documentation**: See uploaded PDFs for complete data model
- **Database Schema**: Check `INFORMATION_SCHEMA` in your database
- **OneSumX Support**: Contact Wolters Kluwer for version-specific details

---

**Ready to load your RiskPro data!** 🚀

Configure the settings, test the connection, and start generating AI-powered scenarios from your real ALM system.
