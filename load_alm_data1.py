"""
RiskPro ALM Data Loader

This module loads risk factors, counterparties, and contracts from the RiskPro (OneSumX) database
for use with the ALM Scenario Generator.

Database Structure:
- Contracts are stored with various types (ANN, PAM, RGM, IRSWP, etc.)
- Market objects define yield curves, spreads, and other market risk factors
- Counterparties/Obligors linked via counterpartyKey and issuerKey
- Credit ratings and PD stored at contract and counterparty level

Author: ALM Risk Engineering Team
"""

from datetime import date, datetime
from typing import List, Tuple, Optional, Dict, Any
import logging

# Database connection - adjust based on your setup
try:
    import pyodbc  # For SQL Server / ODBC
    HAS_PYODBC = True
except ImportError:
    HAS_PYODBC = False

try:
    import psycopg2  # For PostgreSQL
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

try:
    import cx_Oracle  # For Oracle
    HAS_ORACLE = True
except ImportError:
    HAS_ORACLE = False

from alm_scenarios.models import (
    RiskFactor, YieldCurve, SpreadCurve, FXRate, EquityIndex, MacroFactor,
    Counterparty, Contract, ContractType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class RiskProConfig:
    """Configuration for RiskPro database connection"""
    
    # Database connection settings
    DB_TYPE = "sqlserver"  # Options: "sqlserver", "oracle", "postgresql"
    DB_HOST = "192.168.50.195"
    DB_PORT = 1433
    DB_NAME = "RP_1225"
    DB_USER = "RP_1225"
    DB_PASSWORD = "RP_1225"
    
    # Schema/owner names (adjust based on your installation)
    SCHEMA = "dbo"  # or "RISKPRO" for Oracle
    
    # Table names (OneSumX default naming)
    CONTRACTS_TABLE = "CONTRACT"
    MARKET_OBJECTS_TABLE = "MARKET_OBJECT"
    COUNTERPARTY_TABLE = "COUNTERPARTY"
    RATING_TABLE = "RATING_CLASS"
    YIELD_CURVE_TABLE = "OBS_YIELD_CURVE"
    SPREAD_CURVE_TABLE = "OBS_SPREAD_CURVE"
    FX_RATE_TABLE = "OBS_FX_RATE"
    
    # Calculation/reporting date
    VALUATION_DATE = datetime.now().date()
    
    
    @classmethod
    def get_connection_string(cls) -> str:
        """Get database connection string based on DB type"""
        if cls.DB_TYPE == "sqlserver":
            return (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={cls.DB_HOST},{cls.DB_PORT};"
                f"DATABASE={cls.DB_NAME};"
                f"UID={cls.DB_USER};"
                #f"PWD={cls.DB_PASSWORD}"
                f"Trusted_Connection=yes;"

            )
        elif cls.DB_TYPE == "oracle":
            return f"{cls.DB_USER}/{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        elif cls.DB_TYPE == "postgresql":
            return (
                f"host={cls.DB_HOST} "
                f"port={cls.DB_PORT} "
                f"dbname={cls.DB_NAME} "
                f"user={cls.DB_USER} "
                f"password={cls.DB_PASSWORD}"
            )
        else:
            raise ValueError(f"Unsupported DB type: {cls.DB_TYPE}")


# =============================================================================
# Database Connection
# =============================================================================

def get_database_connection():
    """
    Establish connection to RiskPro database.
    
    Returns:
        Database connection object
    
    Raises:
        ImportError: If required database driver not installed
        Exception: If connection fails
    """
    db_type = RiskProConfig.DB_TYPE
    conn_str = RiskProConfig.get_connection_string()
    
    try:
        if db_type == "sqlserver":
            if not HAS_PYODBC:
                raise ImportError(
                    "pyodbc not installed. Install with: pip install pyodbc"
                )
            return pyodbc.connect(conn_str)
        
        elif db_type == "oracle":
            if not HAS_ORACLE:
                raise ImportError(
                    "cx_Oracle not installed. Install with: pip install cx_Oracle"
                )
            return cx_Oracle.connect(conn_str)
        
        elif db_type == "postgresql":
            if not HAS_PSYCOPG2:
                raise ImportError(
                    "psycopg2 not installed. Install with: pip install psycopg2-binary"
                )
            return psycopg2.connect(conn_str)
        
        else:
            raise ValueError(f"Unsupported DB type: {db_type}")
    
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


# =============================================================================
# Risk Factors Loader
# =============================================================================

def load_yield_curves(conn) -> List[YieldCurve]:
    """
    Load yield curves from RiskPro.
    
    RiskPro stores yield curves in MARKET_OBJECT and YIELD_CURVE_POINT tables.
    
    Args:
        conn: Database connection
    
    Returns:
        List of YieldCurve objects
    """
    logger.info("Loading yield curves from RiskPro...")
    
    curves = []
    cursor = conn.cursor()
    
    # Query to get yield curve definitions and points
    # Adjust schema and table names based on your installation
    query = f"""
    SELECT 
        mo.MARKET_OBJECT_KEY as curve_id,
        mo.MARKET_OBJECT_NAME as curve_name,
        mo.CURRENCY as currency,
        ycp.MATURITY as tenor,
        ycp.RATE as rate
    FROM {RiskProConfig.SCHEMA}.{RiskProConfig.MARKET_OBJECTS_TABLE} mo
    INNER JOIN {RiskProConfig.SCHEMA}.{RiskProConfig.YIELD_CURVE_TABLE} ycp
        ON mo.MARKET_OBJECT_KEY = ycp.MARKET_OBJECT_KEY
    WHERE mo.MARKET_OBJECT_TYPE = 'YIELD_CURVE'
        AND mo.AS_OF_DATE = ?
    ORDER BY mo.MARKET_OBJECT_KEY, ycp.MATURITY
    """
    
    cursor.execute(query, (RiskProConfig.VALUATION_DATE,))
    
    # Group by curve
    curves_dict = {}
    for row in cursor.fetchall():
        curve_id = row[0]
        if curve_id not in curves_dict:
            curves_dict[curve_id] = {
                'curve_id': curve_id,
                'curve_name': row[1],
                'currency': row[2],
                'tenors': [],
                'rates': []
            }
        curves_dict[curve_id]['tenors'].append(str(row[3]))
        curves_dict[curve_id]['rates'].append(float(row[4]))
    
    # Create YieldCurve objects
    for curve_data in curves_dict.values():
        curve = YieldCurve(
            factor_id=curve_data['curve_id'],
            currency=curve_data['currency'],
            description=curve_data['curve_name'],
            tenors=curve_data['tenors'],
            rates=curve_data['rates']
        )
        curves.append(curve)
    
    cursor.close()
    logger.info(f"Loaded {len(curves)} yield curves")
    return curves


def load_spread_curves(conn) -> List[SpreadCurve]:
    """
    Load credit/liquidity spread curves from RiskPro.
    
    Args:
        conn: Database connection
    
    Returns:
        List of SpreadCurve objects
    """
    logger.info("Loading spread curves from RiskPro...")
    
    curves = []
    cursor = conn.cursor()
    
    query = f"""
    SELECT 
        mo.MARKET_OBJECT_KEY as curve_id,
        mo.MARKET_OBJECT_NAME as curve_name,
        mo.CURRENCY as currency,
        mo.RATING_CLASS as rating,
        scp.MATURITY as tenor,
        scp.SPREAD as spread_bps
    FROM {RiskProConfig.SCHEMA}.{RiskProConfig.MARKET_OBJECTS_TABLE} mo
    INNER JOIN {RiskProConfig.SCHEMA}.{RiskProConfig.SPREAD_CURVE_TABLE} scp
        ON mo.MARKET_OBJECT_KEY = scp.MARKET_OBJECT_KEY
    WHERE mo.MARKET_OBJECT_TYPE IN ('CREDIT_SPREAD_CURVE', 'LIQUIDITY_SPREAD_CURVE')
        AND mo.AS_OF_DATE = ?
    ORDER BY mo.MARKET_OBJECT_KEY, scp.MATURITY
    """
    
    cursor.execute(query, (RiskProConfig.VALUATION_DATE,))
    
    # Group by curve
    curves_dict = {}
    for row in cursor.fetchall():
        curve_id = row[0]
        if curve_id not in curves_dict:
            curves_dict[curve_id] = {
                'curve_id': curve_id,
                'curve_name': row[1],
                'currency': row[2],
                'rating': row[3],
                'tenors': [],
                'spreads': []
            }
        curves_dict[curve_id]['tenors'].append(str(row[4]))
        curves_dict[curve_id]['spreads'].append(float(row[5]))
    
    # Create SpreadCurve objects
    for curve_data in curves_dict.values():
        curve = SpreadCurve(
            factor_id=curve_data['curve_id'],
            currency=curve_data['currency'],
            rating=curve_data['rating'],
            spread_type="credit",  # Adjust if you have liquidity spreads
            description=curve_data['curve_name'],
            tenors=curve_data['tenors'],
            spreads=curve_data['spreads']
        )
        curves.append(curve)
    
    cursor.close()
    logger.info(f"Loaded {len(curves)} spread curves")
    return curves


def load_fx_rates(conn) -> List[FXRate]:
    """
    Load FX rates from RiskPro.
    
    Args:
        conn: Database connection
    
    Returns:
        List of FXRate objects
    """
    logger.info("Loading FX rates from RiskPro...")
    
    fx_rates = []
    cursor = conn.cursor()
    
    query = f"""
    SELECT 
        FX_PAIR as currency_pair,
        BASE_CURRENCY as base_currency,
        QUOTE_CURRENCY as quote_currency,
        SPOT_RATE as spot_rate
    FROM {RiskProConfig.SCHEMA}.{RiskProConfig.FX_RATE_TABLE}
    WHERE AS_OF_DATE = ?
    """
    
    cursor.execute(query, (RiskProConfig.VALUATION_DATE,))
    
    for row in cursor.fetchall():
        fx_rate = FXRate(
            factor_id=row[0],
            currency_pair=row[0],
            base_currency=row[1],
            quote_currency=row[2],
            spot_rate=float(row[3])
        )
        fx_rates.append(fx_rate)
    
    cursor.close()
    logger.info(f"Loaded {len(fx_rates)} FX rates")
    return fx_rates


def load_equity_indices(conn) -> List[EquityIndex]:
    """
    Load equity index levels from RiskPro.
    
    Args:
        conn: Database connection
    
    Returns:
        List of EquityIndex objects
    """
    logger.info("Loading equity indices from RiskPro...")
    
    indices = []
    cursor = conn.cursor()
    
    query = f"""
    SELECT 
        MARKET_OBJECT_KEY as index_id,
        MARKET_OBJECT_NAME as index_name,
        INDEX_LEVEL as current_level
    FROM {RiskProConfig.SCHEMA}.{RiskProConfig.MARKET_OBJECTS_TABLE}
    WHERE MARKET_OBJECT_TYPE = 'EQUITY_INDEX'
        AND AS_OF_DATE = ?
    """
    
    cursor.execute(query, (RiskProConfig.VALUATION_DATE,))
    
    for row in cursor.fetchall():
        index = EquityIndex(
            factor_id=row[0],
            index_name=row[1],
            current_level=float(row[2])
        )
        indices.append(index)
    
    cursor.close()
    logger.info(f"Loaded {len(indices)} equity indices")
    return indices


def load_macro_factors(conn) -> List[MacroFactor]:
    """
    Load macroeconomic factors from RiskPro.
    
    Note: RiskPro may not have dedicated macro factor tables.
    This is a placeholder - adjust based on your implementation.
    
    Args:
        conn: Database connection
    
    Returns:
        List of MacroFactor objects
    """
    logger.info("Loading macro factors from RiskPro...")
    
    # Placeholder implementation
    # Adjust based on where you store GDP, inflation, unemployment, etc.
    macro_factors = []
    
    # Example: You might have a custom table or use market objects
    # cursor = conn.cursor()
    # query = "SELECT ..."
    # cursor.execute(query)
    # ...
    
    logger.info(f"Loaded {len(macro_factors)} macro factors")
    return macro_factors


def load_all_risk_factors(conn) -> List[RiskFactor]:
    """
    Load all risk factors from RiskPro.
    
    Args:
        conn: Database connection
    
    Returns:
        List of all RiskFactor objects
    """
    logger.info("Loading all risk factors from RiskPro...")
    
    risk_factors = []
    risk_factors.extend(load_yield_curves(conn))
    risk_factors.extend(load_spread_curves(conn))
    risk_factors.extend(load_fx_rates(conn))
    risk_factors.extend(load_equity_indices(conn))
    risk_factors.extend(load_macro_factors(conn))
    
    logger.info(f"Total risk factors loaded: {len(risk_factors)}")
    return risk_factors


# =============================================================================
# Counterparties Loader
# =============================================================================

def load_counterparties(conn) -> List[Counterparty]:
    """
    Load counterparties/obligors from RiskPro.
    
    RiskPro stores counterparty information including:
    - counterpartyKey / issuerKey
    - Rating class
    - Probability of default (PD)
    - Recovery rate / Loss Given Default (LGD)
    
    Args:
        conn: Database connection
    
    Returns:
        List of Counterparty objects
    """
    logger.info("Loading counterparties from RiskPro...")
    
    counterparties = []
    cursor = conn.cursor()
    
    # Query counterparty master data
    # Adjust field names based on your RiskPro schema version
    query = f"""
    SELECT 
        cp.COUNTERPARTY_KEY as counterparty_id,
        cp.COUNTERPARTY_NAME as name,
        cp.RATING_CLASS as rating,
        cp.PROBABILITY_OF_DEFAULT as pd,
        cp.RECOVERY_RATE as recovery_rate,
        cp.SECTOR as sector,
        cp.COUNTRY as country
    FROM {RiskProConfig.SCHEMA}.{RiskProConfig.COUNTERPARTY_TABLE} cp
    WHERE cp.AS_OF_DATE = ?
        AND cp.COUNTERPARTY_KEY IS NOT NULL
    """
    
    cursor.execute(query, (RiskProConfig.VALUATION_DATE,))
    
    for row in cursor.fetchall():
        # Handle NULL values
        pd_value = float(row[3]) if row[3] is not None else 0.01  # Default 1%
        recovery = float(row[4]) if row[4] is not None else 0.40  # Default 40%
        
        counterparty = Counterparty(
            counterparty_id=row[0],
            name=row[1],
            rating=row[2] or "NR",  # Not Rated if NULL
            pd=pd_value,
            recovery_rate=recovery,
            sector=row[5],
            country=row[6]
        )
        counterparties.append(counterparty)
    
    cursor.close()
    logger.info(f"Loaded {len(counterparties)} counterparties")
    return counterparties


# =============================================================================
# Contracts Loader
# =============================================================================

def map_contract_type(riskpro_type: str) -> ContractType:
    """
    Map RiskPro contract type codes to ContractType enum.
    
    RiskPro uses codes like:
    - ANN, PAM, RGM, NGM for loans/mortgages
    - IRSWP for interest rate swaps
    - FXSWP for FX swaps
    - etc.
    
    Args:
        riskpro_type: RiskPro contract type code
    
    Returns:
        ContractType enum value
    """
    # Mapping of RiskPro codes to our contract types
    type_mapping = {
        # Loans and mortgages
        'ANN': ContractType.LOAN,
        'PAM': ContractType.LOAN,
        'RGM': ContractType.LOAN,
        'NGM': ContractType.LOAN,
        'ANNOP': ContractType.OPTION,
        
        # Deposits
        'DSC': ContractType.DEPOSIT,
        'CPDSDC': ContractType.DEPOSIT,
        
        # Bonds
        'BNDIDX': ContractType.BOND,
        'PBN': ContractType.BOND,
        'ZCB': ContractType.BOND,
        
        # Swaps
        'IRSWP': ContractType.SWAP,
        'FXSWP': ContractType.SWAP,
        'IIS': ContractType.SWAP,
        
        # Forwards
        'FXFWD': ContractType.FORWARD,
        
        # Options
        'FXOP': ContractType.OPTION,
        'IDXOP': ContractType.OPTION,
        
        # Facilities
        'FACIL': ContractType.FACILITY,
    }
    
    return type_mapping.get(riskpro_type, ContractType.LOAN)  # Default to LOAN


def load_contracts(conn, limit: Optional[int] = None) -> List[Contract]:
    """
    Load contracts/positions from RiskPro.
    
    RiskPro CONTRACT table contains:
    - Contract identification
    - Contract type (ANN, PAM, IRSWP, etc.)
    - Notional, currency, maturity
    - Links to market objects (discountingMarketObject, etc.)
    - Links to counterparties (counterpartyKey, issuerKey)
    
    Args:
        conn: Database connection
        limit: Optional limit on number of contracts to load (for testing)
    
    Returns:
        List of Contract objects
    """
    logger.info("Loading contracts from RiskPro...")
    
    contracts = []
    cursor = conn.cursor()
    
    # Build query with optional limit
    limit_clause = f"TOP {limit}" if limit and RiskProConfig.DB_TYPE == "sqlserver" else ""
    rownum_clause = f"AND ROWNUM <= {limit}" if limit and RiskProConfig.DB_TYPE == "oracle" else ""
    
    query = f"""
    SELECT {limit_clause}
        c.CONTRACT_KEY as contract_id,
        c.CONTRACT_TYPE as contract_type,
        c.CURRENCY as currency,
        c.NOTIONAL_PRINCIPAL as notional,
        c.MATURITY_DATE as maturity_date,
        c.DISCOUNTING_MARKET_OBJECT as linked_yield_curve,
        c.CREDIT_SPREAD_CURVE_DEFINITION as linked_spread_curve,
        c.COUNTERPARTY_KEY as counterparty_id,
        c.BOOK_VALUE as book_value,
        c.INTEREST_RATE as rate
    FROM {RiskProConfig.SCHEMA}.{RiskProConfig.CONTRACTS_TABLE} c
    WHERE c.AS_OF_DATE = ?
        AND c.CONTRACT_STATUS = 'ACTIVE'
        {rownum_clause}
    """
    
    if limit and RiskProConfig.DB_TYPE == "postgresql":
        query += f" LIMIT {limit}"
    
    cursor.execute(query, (RiskProConfig.VALUATION_DATE,))
    
    for row in cursor.fetchall():
        # Determine if asset or liability based on book value sign
        book_value = float(row[8]) if row[8] is not None else 0.0
        is_asset = book_value >= 0
        
        # Handle date conversion
        maturity_date = row[4]
        if isinstance(maturity_date, str):
            maturity_date = datetime.strptime(maturity_date, "%Y-%m-%d").date()
        elif isinstance(maturity_date, datetime):
            maturity_date = maturity_date.date()
        
        contract = Contract(
            contract_id=row[0],
            contract_type=map_contract_type(row[1]),
            currency=row[2],
            notional=float(row[3]) if row[3] is not None else 0.0,
            maturity_date=maturity_date,
            linked_yield_curve=row[5],
            linked_spread_curve=row[6],
            counterparty_id=row[7],
            is_asset=is_asset,
            rate=float(row[9]) if row[9] is not None else None
        )
        contracts.append(contract)
    
    cursor.close()
    logger.info(f"Loaded {len(contracts)} contracts")
    return contracts


# =============================================================================
# Main Loader Function
# =============================================================================

def load_from_riskpro(
    limit_contracts: Optional[int] = None
) -> Tuple[List[RiskFactor], List[Counterparty], List[Contract]]:
    """
    Main function to load all ALM data from RiskPro database.
    
    Args:
        limit_contracts: Optional limit on number of contracts (for testing)
    
    Returns:
        Tuple of (risk_factors, counterparties, contracts)
    
    Example:
        >>> from load_alm_data import load_from_riskpro
        >>> risk_factors, counterparties, contracts = load_from_riskpro()
        >>> print(f"Loaded {len(risk_factors)} risk factors")
        >>> print(f"Loaded {len(counterparties)} counterparties")
        >>> print(f"Loaded {len(contracts)} contracts")
    """
    logger.info("=" * 80)
    logger.info("LOADING ALM DATA FROM RISKPRO")
    logger.info("=" * 80)
    logger.info(f"Database: {RiskProConfig.DB_TYPE}")
    logger.info(f"Valuation Date: {RiskProConfig.VALUATION_DATE}")
    logger.info("")
    
    try:
        # Connect to database
        logger.info("Connecting to RiskPro database...")
        conn = get_database_connection()
        logger.info("✓ Connected successfully")
        logger.info("")
        
        # Load risk factors
        risk_factors = load_all_risk_factors(conn)
        
        # Load counterparties
        counterparties = load_counterparties(conn)
        
        # Load contracts
        contracts = load_contracts(conn, limit=limit_contracts)
        
        # Close connection
        conn.close()
        logger.info("")
        logger.info("=" * 80)
        logger.info("LOADING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"✓ Total risk factors: {len(risk_factors)}")
        logger.info(f"✓ Total counterparties: {len(counterparties)}")
        logger.info(f"✓ Total contracts: {len(contracts)}")
        logger.info("")
        
        return risk_factors, counterparties, contracts
    
    except Exception as e:
        logger.error(f"Error loading data from RiskPro: {e}")
        logger.error("Please check:")
        logger.error("1. Database connection settings in RiskProConfig")
        logger.error("2. Database driver is installed (pyodbc/cx_Oracle/psycopg2)")
        logger.error("3. Database is accessible and credentials are correct")
        logger.error("4. Schema and table names match your RiskPro installation")
        raise


# =============================================================================
# Testing / Example Usage
# =============================================================================

if __name__ == "__main__":
    """
    Test the data loader.
    
    Before running:
    1. Update RiskProConfig with your database settings
    2. Install required database driver
    3. Ensure database is accessible
    """
    
    print("=" * 80)
    print("RISKPRO DATA LOADER - TEST MODE")
    print("=" * 80)
    print()
    print("Configuration:")
    print(f"  Database Type: {RiskProConfig.DB_TYPE}")
    print(f"  Database Host: {RiskProConfig.DB_HOST}")
    print(f"  Database Name: {RiskProConfig.DB_NAME}")
    print(f"  Valuation Date: {RiskProConfig.VALUATION_DATE}")
    print()
    print("NOTE: Update RiskProConfig class with your actual settings before running!")
    print()
    
    try:
        # Load small sample for testing (limit to 100 contracts)
        risk_factors, counterparties, contracts = load_from_riskpro(limit_contracts=100)
        
        print("\nSample Data:")
        if risk_factors:
            print(f"\nFirst yield curve: {risk_factors[0].to_dict()}")
        if counterparties:
            print(f"\nFirst counterparty: {counterparties[0].to_dict()}")
        if contracts:
            print(f"\nFirst contract: {contracts[0].to_dict()}")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nPlease check:")
        print("1. Database credentials in RiskProConfig")
        print("2. pyodbc is installed: pip install pyodbc")
        print("3. SQL Server is accessible from this machine")
        print("4. Database name and schema are correct")
