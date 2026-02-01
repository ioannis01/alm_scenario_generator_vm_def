"""
RiskPro ALM Data Loader - HYBRID VERSION

Uses:
- Sample risk factors from create_sample_universe() (RiskPro doesn't have these tables)
- Real counterparties from COUNTERPARTY table
- Real contracts from CONTRACT table
- Counterparty classes from COUNTERPARTY_CLASS table

Author: ALM Risk Engineering Team
"""

from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
import logging

import pyodbc
from alm_scenarios.models import (
    RiskFactor, Counterparty, Contract, ContractType
)
from alm_scenarios.utils.sample_data import create_sample_universe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskProConfig:
    """Configuration for RiskPro database connection"""
    DB_TYPE = "sqlserver"
    DB_HOST = "127.0.0.1"  # localhost works from WSL2
    DB_PORT = 1433
    DB_NAME = "RP_141301"       # "RP_1225"
    DB_USER = "sa"              # "RP_1225"
    DB_PASSWORD = "2F@st4u2c"   # "RP_1225"
    SCHEMA = "dbo"
    
    @classmethod
    def get_connection_string(cls) -> str:
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={cls.DB_HOST},{cls.DB_PORT};"
            f"DATABASE={cls.DB_NAME};"
            f"UID={cls.DB_USER};"
            f"PWD={cls.DB_PASSWORD}"
        )


def get_database_connection():
    """Establish connection to RiskPro database"""
    try:
        conn = pyodbc.connect(RiskProConfig.get_connection_string())
        logger.info("✓ Connected to RiskPro database")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to RiskPro: {e}")
        raise Exception(f"Database connection failed: {str(e)}")


def get_available_model_ids() -> List[Dict[str, Any]]:
    """
    Get distinct model_ids from RiskPro database with counts.
    
    Returns:
        List of dicts with model_id, contract_count, counterparty_count
    
    Raises:
        Exception if database query fails
    """
    logger.info("Fetching available model IDs from RiskPro...")
    
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Query to get distinct MODEL_ID values with counts
        query = """
        SELECT 
            c.MODEL_ID,
            COUNT(DISTINCT c.CONTRACT_ID) as contract_count,
            COUNT(DISTINCT cp.COUNTERPARTY_ID) as counterparty_count
        FROM dbo.CONTRACT c
        LEFT JOIN dbo.COUNTERPARTY cp ON c.MODEL_ID = cp.MODEL_ID
        WHERE c.MODEL_ID IS NOT NULL
        GROUP BY c.MODEL_ID
        ORDER BY c.MODEL_ID
        """
        
        logger.info(f"Executing query to fetch model IDs...")
        cursor.execute(query)
        
        models = []
        for row in cursor.fetchall():
            model_id = str(row[0]) if row[0] else None
            if model_id:
                models.append({
                    'model_id': model_id,
                    'contract_count': int(row[1]) if row[1] else 0,
                    'counterparty_count': int(row[2]) if row[2] else 0
                })
        
        cursor.close()
        conn.close()
        
        if len(models) == 0:
            logger.warning("⚠ No model IDs found in CONTRACT table")
            raise Exception("No model IDs found in database. Check if CONTRACT table has MODEL_ID values.")
        
        logger.info(f"✓ Found {len(models)} model IDs")
        for m in models[:5]:  # Log first 5
            logger.info(f"  - {m['model_id']}: {m['contract_count']} contracts, {m['counterparty_count']} counterparties")
        
        return models
        
    except pyodbc.Error as e:
        logger.error(f"Database error fetching model IDs: {e}")
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching model IDs: {e}")
        raise


def load_sample_risk_factors() -> List[RiskFactor]:
    """
    Load sample risk factors using create_sample_universe().
    
    RiskPro database doesn't have dedicated risk factor tables,
    so we use realistic sample data for scenario generation.
    """
    logger.info("Loading sample risk factors (create_sample_universe)...")
    
    risk_factors, _, _ = create_sample_universe()
    
    logger.info(f"✓ Loaded {len(risk_factors)} sample risk factors")
    logger.info(f"  - Yield curves, spread curves, FX rates, equity indices, macro factors")
    return risk_factors


def load_counterparty_classes(conn) -> Dict[str, Dict[str, Any]]:
    """Load counterparty class definitions from COUNTERPARTY_CLASS table"""
    logger.info("Loading counterparty classes...")
    
    classes = {}
    cursor = conn.cursor()
    
    query = """
    SELECT 
        COUNTERPARTY_CLASS_ID,
        ATTRIBUTE_RANGE_ID,
        NAME,
        RANK,
        CODE,
        DESCRIPTION
    FROM dbo.COUNTERPARTY_CLASS
    """
    
    try:
        cursor.execute(query)
        for row in cursor.fetchall():
            class_id = str(row[0]) if row[0] else None
            if class_id:
                classes[class_id] = {
                    'name': row[2],
                    'rank': int(row[3]) if row[3] is not None else None,
                    'code': row[4],
                    'description': row[5]
                }
        logger.info(f"✓ Loaded {len(classes)} counterparty classes")
    except Exception as e:
        logger.warning(f"⚠ Could not load counterparty classes: {e}")
    finally:
        cursor.close()
    
    return classes


def load_counterparties(
    conn, 
    counterparty_classes: Dict,
    model_id: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Counterparty]:
    """
    Load counterparties from COUNTERPARTY table with optional filtering.
    
    Args:
        conn: Database connection
        counterparty_classes: Dict of counterparty class definitions
        model_id: Optional model ID to filter by
        limit: Optional maximum number of records to load
    
    Returns:
        List of Counterparty objects
    """
    logger.info("Loading counterparties from RiskPro...")
    if model_id:
        logger.info(f"  Filtering by MODEL_ID = '{model_id}'")
    if limit:
        logger.info(f"  Limiting to {limit} records")
    
    counterparties = []
    cursor = conn.cursor()
    
    # Build query with optional filters
    top_clause = f"TOP {limit}" if limit else "TOP 10000"
    where_clause = f"WHERE MODEL_ID = ?" if model_id else ""
    
    query = f"""
    SELECT {top_clause}
        COUNTERPARTY_ID,
        SEGMENT,
        LEGAL_COUNTRY,
        MODEL_ID,
        COUNTERPARTY_CLASS,
        DEFAULT_PROBABILITY,
        CP_NAME,
        SPREAD_CURVE_DEF,
        LGD_MARKET,
        CURRENCY_DEF,
        IS_NON_PERFORMING,
        INDUSTRY,
        REGION
    FROM dbo.COUNTERPARTY
    {where_clause}
    ORDER BY COUNTERPARTY_ID
    """
    
    try:
        if model_id:
            cursor.execute(query, (model_id,))
        else:
            cursor.execute(query)
        
        for row in cursor.fetchall():
            counterparty_id = str(row[0]) if row[0] else None
            if not counterparty_id:
                continue
            
            # Get counterparty class details
            cp_class_id = str(row[4]) if row[4] else None
            cp_class_info = counterparty_classes.get(cp_class_id, {})
            
            # Extract risk metrics
            pd_value = float(row[5]) if row[5] is not None else 0.01
            lgd_market = float(row[8]) if row[8] is not None else 0.60
            recovery_rate = 1.0 - lgd_market
            is_npl = bool(row[10]) if row[10] is not None else False
            
            # Create counterparty
            counterparty = Counterparty(
                counterparty_id=counterparty_id,
                name=row[6] or "Unknown",
                rating=cp_class_info.get('name', 'NR'),
                pd=pd_value,
                recovery_rate=recovery_rate,
                sector=row[11],  # INDUSTRY
                country=row[2]   # LEGAL_COUNTRY
            )
            
            # Add extended attributes for rich LLM context
            counterparty.extended_attributes = {
                'segment': row[1],
                'model_id': row[3],
                'counterparty_class': cp_class_id,
                'counterparty_class_name': cp_class_info.get('name'),
                'counterparty_class_rank': cp_class_info.get('rank'),
                'counterparty_class_code': cp_class_info.get('code'),
                'counterparty_class_description': cp_class_info.get('description'),
                'spread_curve_def': row[7],
                'lgd_market': lgd_market,
                'currency': row[9],
                'is_non_performing': is_npl,
                'region': row[12]
            }
            
            counterparties.append(counterparty)
        
        if len(counterparties) == 0:
            warning_msg = f"No counterparties found"
            if model_id:
                warning_msg += f" for MODEL_ID = '{model_id}'"
            logger.warning(f"⚠ {warning_msg}")
        else:
            logger.info(f"✓ Loaded {len(counterparties)} counterparties")
            
    except Exception as e:
        logger.error(f"✗ Could not load counterparties: {e}")
        raise Exception(f"Error loading counterparties: {str(e)}")
    finally:
        cursor.close()
    
    return counterparties


def map_contract_type(product_type: str) -> ContractType:
    """Map RiskPro product type to ContractType enum"""
    if not product_type:
        return ContractType.LOAN
    
    product_type = product_type.upper()
    
    mapping = {
        'LOAN': ContractType.LOAN,
        'MORTGAGE': ContractType.LOAN,
        'ANNUITY': ContractType.LOAN,
        'DEPOSIT': ContractType.DEPOSIT,
        'BOND': ContractType.BOND,
        'SWAP': ContractType.SWAP,
        'IRS': ContractType.SWAP,
        'FORWARD': ContractType.FORWARD,
        'OPTION': ContractType.OPTION,
        'FACILITY': ContractType.FACILITY,
        'CREDIT_LINE': ContractType.FACILITY,
    }
    
    for key, value in mapping.items():
        if key in product_type:
            return value
    
    return ContractType.LOAN


def load_contracts(
    conn,
    model_id: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Contract]:
    """
    Load contracts from CONTRACT table with optional filtering.
    
    Args:
        conn: Database connection
        model_id: Optional model ID to filter by
        limit: Optional maximum number of records to load
    
    Returns:
        List of Contract objects
    """
    logger.info("Loading contracts from RiskPro...")
    if model_id:
        logger.info(f"  Filtering by MODEL_ID = '{model_id}'")
    if limit:
        logger.info(f"  Limiting to {limit} records")
    
    contracts = []
    cursor = conn.cursor()
    
    # Build query with optional filters
    top_clause = f"TOP {limit}" if limit else "TOP 1000"
    where_clause = f"WHERE MODEL_ID = ?" if model_id else ""
    
    query = f"""
    SELECT {top_clause}
        CONTRACT_ID,
        MODEL_ID,
        IP_TYPE_ID,
        BOOK_VALUE_DATE,
        VALUE_DATE,
        BOOK_VALUE,
        FTP_CREDIT_RISK_SPREAD,
        FTP_LIQUIDITY_SPREAD,
        MARKET_VALUE_DATE,
        MARKET_VALUE_OBSERVED,
        MATURITY_DATE,
        ORIGINAL_TOTAL_PRINCIPAL,
        PREMIUM_DISCOUNT,
        FEE_AMOUNT,
        PRODUCT_TYPE,
        SEGMENT,
        LEGAL_ENTITY,
        NOTIONAL_VALUE
    FROM dbo.CONTRACT
    {where_clause}
    ORDER BY CONTRACT_ID
    """
    
    try:
        if model_id:
            cursor.execute(query, (model_id,))
        else:
            cursor.execute(query)
        
        for row in cursor.fetchall():
            contract_id = str(row[0]) if row[0] else None
            if not contract_id:
                continue
            
            # Determine asset/liability from book value
            book_value = float(row[5]) if row[5] is not None else 0.0
            is_asset = book_value >= 0
            
            # Handle maturity date
            maturity_date = row[10]
            if isinstance(maturity_date, str):
                try:
                    maturity_date = datetime.strptime(maturity_date, "%Y-%m-%d").date()
                except:
                    maturity_date = datetime(2030, 12, 31).date()
            elif isinstance(maturity_date, datetime):
                maturity_date = maturity_date.date()
            elif maturity_date is None:
                maturity_date = datetime(2030, 12, 31).date()
            
            # Get notional and principal
            notional_value = float(row[17]) if row[17] is not None else 0.0
            original_principal = float(row[11]) if row[11] is not None else notional_value
            
            # Create contract
            contract = Contract(
                contract_id=contract_id,
                contract_type=map_contract_type(row[14]),
                currency='CHF',  # Default currency
                notional=notional_value,
                maturity_date=maturity_date,
                linked_yield_curve=None,
                linked_spread_curve=None,
                counterparty_id=None,
                is_asset=is_asset,
                rate=None
            )
            
            # Add extended attributes for rich LLM context
            contract.extended_attributes = {
                'model_id': row[1],
                'ip_type_id': row[2],
                'book_value_date': str(row[3]) if row[3] else None,
                'value_date': str(row[4]) if row[4] else None,
                'book_value': book_value,
                'ftp_credit_risk_spread': float(row[6]) if row[6] is not None else None,
                'ftp_liquidity_spread': float(row[7]) if row[7] is not None else None,
                'market_value_date': str(row[8]) if row[8] else None,
                'market_value_observed': float(row[9]) if row[9] is not None else None,
                'original_total_principal': original_principal,
                'premium_discount': float(row[12]) if row[12] is not None else None,
                'fee_amount': float(row[13]) if row[13] is not None else None,
                'product_type': row[14],
                'segment': row[15],
                'legal_entity': row[16]
            }
            
            contracts.append(contract)
        
        if len(contracts) == 0:
            warning_msg = f"No contracts found"
            if model_id:
                warning_msg += f" for MODEL_ID = '{model_id}'"
            logger.warning(f"⚠ {warning_msg}")
        else:
            logger.info(f"✓ Loaded {len(contracts)} contracts")
            
    except Exception as e:
        logger.error(f"✗ Could not load contracts: {e}")
        raise Exception(f"Error loading contracts: {str(e)}")
    finally:
        cursor.close()
    
    return contracts


def load_from_riskpro(
    model_id: Optional[str] = None,
    limit_contracts: Optional[int] = None
) -> Tuple[List[RiskFactor], List[Counterparty], List[Contract]]:
    """
    Load ALM data using hybrid approach with filtering.
    
    Args:
        model_id: Optional model ID to filter contracts and counterparties
        limit_contracts: Optional limit on number of contracts/counterparties
    
    Returns:
        Tuple of (risk_factors, counterparties, contracts)
    
    Raises:
        Exception if loading fails
    """
    logger.info("=" * 80)
    logger.info("LOADING HYBRID ALM DATA FROM RISKPRO")
    logger.info("=" * 80)
    logger.info(f"Database: {RiskProConfig.DB_NAME} @ {RiskProConfig.DB_HOST}")
    if model_id:
        logger.info(f"Model ID filter: {model_id}")
    if limit_contracts:
        logger.info(f"Record limit: {limit_contracts}")
    logger.info("")
    logger.info("Data Sources:")
    logger.info("  • Risk Factors: Sample data (create_sample_universe)")
    logger.info("  • Counterparties: RiskPro COUNTERPARTY table")
    logger.info("  • Counterparty Classes: RiskPro COUNTERPARTY_CLASS table")
    logger.info("  • Contracts: RiskPro CONTRACT table")
    logger.info("")
    
    try:
        # Step 1: Load sample risk factors
        risk_factors = load_sample_risk_factors()
        
        # Step 2: Connect to RiskPro
        logger.info("Connecting to RiskPro database...")
        conn = get_database_connection()
        
        # Step 3: Load RiskPro data with filters
        counterparty_classes = load_counterparty_classes(conn)
        counterparties = load_counterparties(
            conn, 
            counterparty_classes,
            model_id=model_id,
            limit=limit_contracts
        )
        contracts = load_contracts(
            conn,
            model_id=model_id,
            limit=limit_contracts
        )
        
        conn.close()
        
        # Validate that we actually loaded data
        if len(contracts) == 0 and len(counterparties) == 0:
            error_msg = "No data loaded"
            if model_id:
                error_msg += f" for model_id '{model_id}'. Check if this model exists in the database."
            else:
                error_msg += ". Check database connectivity and table contents."
            logger.error(f"✗ {error_msg}")
            raise Exception(error_msg)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("LOADING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"✓ Risk factors: {len(risk_factors)} (sample)")
        logger.info(f"✓ Counterparty classes: {len(counterparty_classes)}")
        logger.info(f"✓ Counterparties: {len(counterparties)}")
        logger.info(f"✓ Contracts: {len(contracts)}")
        logger.info("")
        
        return risk_factors, counterparties, contracts
    
    except Exception as e:
        logger.error(f"✗ Error loading data: {e}")
        raise


if __name__ == "__main__":
    print("=" * 80)
    print("RISKPRO HYBRID DATA LOADER - TEST MODE")
    print("=" * 80)
    print()
    
    try:
        # Test 1: Get available models
        print("\n--- Test 1: Get Available Model IDs ---")
        models = get_available_model_ids()
        print(f"Found {len(models)} models:")
        for m in models[:5]:
            print(f"  {m['model_id']}: {m['contract_count']} contracts, {m['counterparty_count']} counterparties")
        
        # Test 2: Load with first model
        if models:
            test_model_id = models[0]['model_id']
            print(f"\n--- Test 2: Load Data for Model '{test_model_id}' ---")
            risk_factors, counterparties, contracts = load_from_riskpro(
                model_id=test_model_id,
                limit_contracts=10
            )
            
            print(f"\nLoaded:")
            print(f"  Risk Factors: {len(risk_factors)}")
            print(f"  Counterparties: {len(counterparties)}")
            print(f"  Contracts: {len(contracts)}")
            
            if counterparties:
                print(f"\nFirst counterparty:")
                cp = counterparties[0]
                print(f"  ID: {cp.counterparty_id}")
                print(f"  Name: {cp.name}")
                print(f"  Model ID: {cp.extended_attributes.get('model_id')}")
            
            if contracts:
                print(f"\nFirst contract:")
                ct = contracts[0]
                print(f"  ID: {ct.contract_id}")
                print(f"  Type: {ct.contract_type}")
                print(f"  Model ID: {ct.extended_attributes.get('model_id')}")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
