"""
RiskPro ALM Data Loader - EXTENDED VERSION

Supports loading from multiple sources:
- Risk Factors: RiskPro DB (RES_DIM_* tables) OR sample data
- Counterparties: RiskPro DB (COUNTERPARTY table)
- Contracts: RiskPro DB (CONTRACT table)
- Counterparty Classes: RiskPro DB (COUNTERPARTY_CLASS table)

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
    
    Used as fallback when RiskPro risk factor tables are not available
    or user chooses not to load from database.
    """
    logger.info("Loading sample risk factors (create_sample_universe)...")
    
    risk_factors, _, _ = create_sample_universe()
    
    logger.info(f"✓ Loaded {len(risk_factors)} sample risk factors")
    logger.info(f"  - Yield curves, spread curves, FX rates, equity indices, macro factors")
    return risk_factors


def load_risk_factors_from_db(
    conn,
    model_id: Optional[str] = None,
    limit: Optional[int] = None
) -> List[RiskFactor]:
    """
    Load risk factors from RiskPro dimension tables.
    
    RiskPro/OneSumX stores risk factors across multiple dimension tables:
    - RES_DIM_*_RISK_FACTOR: Generic risk factors
    - RES_DIM_*_CURVE: Yield/spread curves
    - RES_DIM_*_INDEX: Equity/commodity indices
    - RES_DIM_*_SURF: Volatility surfaces
    
    They are grouped using:
    - RES_DIM_*_VAR_GROUP: Risk factor groupings
    - RES_DIM_MATRIX_CODE: Matrix codes for factor relationships
    
    Args:
        conn: Database connection
        model_id: Optional model ID filter (if risk factors are model-specific)
        limit: Optional limit on number of risk factors to load
        
    Returns:
        List of RiskFactor objects
        
    Raises:
        Exception if tables don't exist or query fails
    """
    logger.info("Loading risk factors from RiskPro dimension tables...")
    if model_id:
        logger.info(f"  Filtering by MODEL_ID = '{model_id}'")
    if limit:
        logger.info(f"  Limiting to {limit} records per table")
    
    risk_factors = []
    cursor = conn.cursor()
    
    # Build limit clause
    top_clause = f"TOP {limit}" if limit else "TOP 1000"
    
    try:
        # ================================================================
        # STRATEGY:
        # We'll query multiple RES_DIM tables and consolidate them into
        # RiskFactor objects. The exact table structure may vary by
        # RiskPro version, so we use error handling per table.
        # ================================================================
        
        # ----- 1. Load RISK_FACTOR dimension -----
        try:
            logger.info("  Querying RES_DIM_RISK_FACTOR...")
            
            # Try the most common table pattern
            query_rf = f"""
            SELECT {top_clause}
                RISK_FACTOR_ID,
                RISK_FACTOR_NAME,
                RISK_FACTOR_TYPE,
                CURRENCY,
                DESCRIPTION,
                VAR_GROUP_ID,
                MATRIX_CODE
            FROM dbo.RES_DIM_RISK_FACTOR
            ORDER BY RISK_FACTOR_ID
            """
            
            cursor.execute(query_rf)
            rf_count = 0
            
            for row in cursor.fetchall():
                rf_id = str(row[0]) if row[0] else None
                if not rf_id:
                    continue
                
                rf_name = row[1] if row[1] else rf_id
                rf_type = row[2] if row[2] else "generic"
                currency = row[3] if row[3] else "USD"
                description = row[4] if row[4] else f"Risk factor {rf_id}"
                
                # Map RiskPro type to internal factor_type
                factor_type = map_risk_factor_type(rf_type)
                
                risk_factor = RiskFactor(
                    factor_id=rf_id,
                    factor_type=factor_type,
                    currency=currency,
                    name=rf_name,
                    description=description
                )
                
                # Store extended attributes for context
                risk_factor.extended_attributes = {
                    'source': 'RES_DIM_RISK_FACTOR',
                    'riskpro_type': rf_type,
                    'var_group_id': str(row[5]) if row[5] else None,
                    'matrix_code': str(row[6]) if row[6] else None
                }
                
                risk_factors.append(risk_factor)
                rf_count += 1
            
            logger.info(f"    ✓ Loaded {rf_count} risk factors")
            
        except pyodbc.Error as e:
            logger.warning(f"    ⚠ RES_DIM_RISK_FACTOR not available or empty: {e}")
        
        # ----- 2. Load CURVE dimension -----
        try:
            logger.info("  Querying RES_DIM_CURVE...")
            
            query_curve = f"""
            SELECT {top_clause}
                CURVE_ID,
                CURVE_NAME,
                CURVE_TYPE,
                CURRENCY,
                DESCRIPTION
            FROM dbo.RES_DIM_CURVE
            ORDER BY CURVE_ID
            """
            
            cursor.execute(query_curve)
            curve_count = 0
            
            for row in cursor.fetchall():
                curve_id = str(row[0]) if row[0] else None
                if not curve_id:
                    continue
                
                curve_name = row[1] if row[1] else curve_id
                curve_type = row[2] if row[2] else "yield_curve"
                currency = row[3] if row[3] else "USD"
                description = row[4] if row[4] else f"Curve {curve_id}"
                
                # Determine if yield or spread curve
                factor_type = "spread_curve" if "spread" in curve_type.lower() else "yield_curve"
                
                risk_factor = RiskFactor(
                    factor_id=curve_id,
                    factor_type=factor_type,
                    currency=currency,
                    name=curve_name,
                    description=description
                )
                
                risk_factor.extended_attributes = {
                    'source': 'RES_DIM_CURVE',
                    'curve_type': curve_type
                }
                
                risk_factors.append(risk_factor)
                curve_count += 1
            
            logger.info(f"    ✓ Loaded {curve_count} curves")
            
        except pyodbc.Error as e:
            logger.warning(f"    ⚠ RES_DIM_CURVE not available or empty: {e}")
        
        # ----- 3. Load INDEX dimension -----
        try:
            logger.info("  Querying RES_DIM_INDEX...")
            
            query_index = f"""
            SELECT {top_clause}
                INDEX_ID,
                INDEX_NAME,
                INDEX_TYPE,
                CURRENCY,
                DESCRIPTION
            FROM dbo.RES_DIM_INDEX
            ORDER BY INDEX_ID
            """
            
            cursor.execute(query_index)
            index_count = 0
            
            for row in cursor.fetchall():
                index_id = str(row[0]) if row[0] else None
                if not index_id:
                    continue
                
                index_name = row[1] if row[1] else index_id
                index_type = row[2] if row[2] else "equity_index"
                currency = row[3] if row[3] else "USD"
                description = row[4] if row[4] else f"Index {index_id}"
                
                # Map index type
                if "fx" in index_type.lower() or "currency" in index_type.lower():
                    factor_type = "fx_rate"
                elif "equity" in index_type.lower() or "stock" in index_type.lower():
                    factor_type = "equity_index"
                else:
                    factor_type = "macro_factor"
                
                risk_factor = RiskFactor(
                    factor_id=index_id,
                    factor_type=factor_type,
                    currency=currency,
                    name=index_name,
                    description=description
                )
                
                risk_factor.extended_attributes = {
                    'source': 'RES_DIM_INDEX',
                    'index_type': index_type
                }
                
                risk_factors.append(risk_factor)
                index_count += 1
            
            logger.info(f"    ✓ Loaded {index_count} indices")
            
        except pyodbc.Error as e:
            logger.warning(f"    ⚠ RES_DIM_INDEX not available or empty: {e}")
        
        # ----- 4. Load SURF dimension (volatility surfaces) -----
        try:
            logger.info("  Querying RES_DIM_SURF...")
            
            query_surf = f"""
            SELECT {top_clause}
                SURF_ID,
                SURF_NAME,
                SURF_TYPE,
                CURRENCY,
                DESCRIPTION
            FROM dbo.RES_DIM_SURF
            ORDER BY SURF_ID
            """
            
            cursor.execute(query_surf)
            surf_count = 0
            
            for row in cursor.fetchall():
                surf_id = str(row[0]) if row[0] else None
                if not surf_id:
                    continue
                
                surf_name = row[1] if row[1] else surf_id
                surf_type = row[2] if row[2] else "volatility"
                currency = row[3] if row[3] else "USD"
                description = row[4] if row[4] else f"Surface {surf_id}"
                
                risk_factor = RiskFactor(
                    factor_id=surf_id,
                    factor_type="volatility_surface",
                    currency=currency,
                    name=surf_name,
                    description=description
                )
                
                risk_factor.extended_attributes = {
                    'source': 'RES_DIM_SURF',
                    'surf_type': surf_type
                }
                
                risk_factors.append(risk_factor)
                surf_count += 1
            
            logger.info(f"    ✓ Loaded {surf_count} surfaces")
            
        except pyodbc.Error as e:
            logger.warning(f"    ⚠ RES_DIM_SURF not available or empty: {e}")
        
        # ----- Final validation -----
        if len(risk_factors) == 0:
            raise Exception(
                "No risk factors loaded from any RES_DIM_* table. "
                "Tables may not exist, be empty, or have different schema. "
                "Consider using sample risk factors instead."
            )
        
        logger.info(f"✓ Loaded {len(risk_factors)} total risk factors from RiskPro DB")
        
        # Log breakdown by source
        sources = {}
        for rf in risk_factors:
            source = rf.extended_attributes.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        for source, count in sources.items():
            logger.info(f"    {source}: {count}")
        
        return risk_factors
        
    except Exception as e:
        logger.error(f"✗ Error loading risk factors from database: {e}")
        raise
    finally:
        cursor.close()


def map_risk_factor_type(riskpro_type: str) -> str:
    """
    Map RiskPro risk factor type to internal factor_type.
    
    Args:
        riskpro_type: Type string from RiskPro
        
    Returns:
        Standardized factor_type
    """
    if not riskpro_type:
        return "generic"
    
    rp = riskpro_type.lower()
    
    # Mapping logic
    if "yield" in rp or "interest" in rp:
        return "yield_curve"
    elif "spread" in rp or "credit" in rp:
        return "spread_curve"
    elif "fx" in rp or "currency" in rp or "exchange" in rp:
        return "fx_rate"
    elif "equity" in rp or "stock" in rp:
        return "equity_index"
    elif "vol" in rp or "volatility" in rp:
        return "volatility_surface"
    elif "macro" in rp or "economic" in rp:
        return "macro_factor"
    else:
        return "generic"


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
            cp_class = counterparty_classes.get(cp_class_id, {})
            
            counterparty = Counterparty(
                counterparty_id=counterparty_id,
                name=row[6] if row[6] else f"CP_{counterparty_id}",
                country=row[2],
                rating=cp_class.get('name', 'Unknown'),
                sector=row[11] if row[11] else 'Unknown',
                default_probability=float(row[5]) if row[5] is not None else 0.0
            )
            
            # Add extended attributes for rich LLM context
            counterparty.extended_attributes = {
                'model_id': row[3],
                'segment': row[1],
                'counterparty_class_id': cp_class_id,
                'counterparty_class_code': cp_class.get('code'),
                'counterparty_class_rank': cp_class.get('rank'),
                'spread_curve_def': row[7],
                'lgd_market': float(row[8]) if row[8] is not None else None,
                'currency_def': row[9],
                'is_non_performing': bool(row[10]) if row[10] is not None else False,
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


def map_contract_type(product_type: Optional[str]) -> ContractType:
    """Map RiskPro product type to ContractType enum"""
    if not product_type:
        return ContractType.GENERIC
    
    pt = product_type.upper()
    
    # Loan types
    if 'LOAN' in pt or 'MORTGAGE' in pt or 'CREDIT' in pt:
        return ContractType.LOAN
    # Deposit types
    elif 'DEPOSIT' in pt or 'SAVINGS' in pt or 'ACCOUNT' in pt:
        return ContractType.DEPOSIT
    # Bond types
    elif 'BOND' in pt or 'NOTE' in pt or 'DEBT' in pt:
        return ContractType.BOND
    # Derivative types
    elif 'SWAP' in pt or 'OPTION' in pt or 'FORWARD' in pt or 'FUTURE' in pt or 'DERIVATIVE' in pt:
        return ContractType.DERIVATIVE
    else:
        return ContractType.GENERIC


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
    top_clause = f"TOP {limit}" if limit else "TOP 10000"
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
    limit_contracts: Optional[int] = None,
    load_risk_factors_from_db_flag: bool = False,
    load_counterparties_flag: bool = True,
    load_contracts_flag: bool = True
) -> Tuple[List[RiskFactor], List[Counterparty], List[Contract]]:
    """
    Load ALM data with user-selectable datasets.
    
    Args:
        model_id: Optional model ID to filter contracts and counterparties
        limit_contracts: Optional limit on number of contracts/counterparties
        load_risk_factors_from_db_flag: If True, load from RiskPro DB; else use sample data
        load_counterparties_flag: If True, load counterparties
        load_contracts_flag: If True, load contracts
    
    Returns:
        Tuple of (risk_factors, counterparties, contracts)
    
    Raises:
        Exception if loading fails
    """
    logger.info("=" * 80)
    logger.info("LOADING ALM DATA FROM RISKPRO")
    logger.info("=" * 80)
    logger.info(f"Database: {RiskProConfig.DB_NAME} @ {RiskProConfig.DB_HOST}")
    if model_id:
        logger.info(f"Model ID filter: {model_id}")
    if limit_contracts:
        logger.info(f"Record limit: {limit_contracts}")
    logger.info("")
    logger.info("Data Sources:")
    logger.info(f"  • Risk Factors: {'RiskPro DB (RES_DIM_* tables)' if load_risk_factors_from_db_flag else 'Sample data'}")
    logger.info(f"  • Counterparties: {'RiskPro DB' if load_counterparties_flag else 'Skipped'}")
    logger.info(f"  • Contracts: {'RiskPro DB' if load_contracts_flag else 'Skipped'}")
    logger.info("")
    
    try:
        # Connect to RiskPro
        logger.info("Connecting to RiskPro database...")
        conn = get_database_connection()
        
        # Step 1: Load risk factors
        if load_risk_factors_from_db_flag:
            try:
                risk_factors = load_risk_factors_from_db(
                    conn,
                    model_id=model_id,
                    limit=limit_contracts
                )
            except Exception as e:
                logger.warning(f"⚠ Failed to load risk factors from DB: {e}")
                logger.info("  Falling back to sample risk factors...")
                risk_factors = load_sample_risk_factors()
        else:
            risk_factors = load_sample_risk_factors()
        
        # Step 2: Load counterparty classes (needed for counterparties)
        counterparty_classes = {}
        if load_counterparties_flag:
            counterparty_classes = load_counterparty_classes(conn)
        
        # Step 3: Load counterparties
        counterparties = []
        if load_counterparties_flag:
            counterparties = load_counterparties(
                conn, 
                counterparty_classes,
                model_id=model_id,
                limit=limit_contracts
            )
        
        # Step 4: Load contracts
        contracts = []
        if load_contracts_flag:
            contracts = load_contracts(
                conn,
                model_id=model_id,
                limit=limit_contracts
            )
        
        conn.close()
        
        # Validate that we loaded something
        if not risk_factors and not counterparties and not contracts:
            raise Exception("No data loaded. Please select at least one dataset to load.")
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("LOADING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"✓ Risk factors: {len(risk_factors)} ({'DB' if load_risk_factors_from_db_flag else 'sample'})")
        if load_counterparties_flag:
            logger.info(f"✓ Counterparty classes: {len(counterparty_classes)}")
            logger.info(f"✓ Counterparties: {len(counterparties)}")
        if load_contracts_flag:
            logger.info(f"✓ Contracts: {len(contracts)}")
        logger.info("")
        
        return risk_factors, counterparties, contracts
    
    except Exception as e:
        logger.error(f"✗ Error loading data: {e}")
        raise


if __name__ == "__main__":
    print("=" * 80)
    print("RISKPRO DATA LOADER - TEST MODE")
    print("=" * 80)
    print()
    
    try:
        # Test 1: Get available models
        print("\n--- Test 1: Get Available Model IDs ---")
        models = get_available_model_ids()
        print(f"Found {len(models)} models:")
        for m in models[:5]:
            print(f"  {m['model_id']}: {m['contract_count']} contracts, {m['counterparty_count']} counterparties")
        
        # Test 2: Load with sample risk factors
        if models:
            test_model_id = models[0]['model_id']
            print(f"\n--- Test 2: Load with Sample Risk Factors ---")
            risk_factors, counterparties, contracts = load_from_riskpro(
                model_id=test_model_id,
                limit_contracts=10,
                load_risk_factors_from_db_flag=False
            )
            print(f"  Risk Factors: {len(risk_factors)} (sample)")
            print(f"  Counterparties: {len(counterparties)}")
            print(f"  Contracts: {len(contracts)}")
            
            # Test 3: Try to load risk factors from DB
            print(f"\n--- Test 3: Try Loading Risk Factors from DB ---")
            try:
                risk_factors_db, _, _ = load_from_riskpro(
                    model_id=test_model_id,
                    limit_contracts=10,
                    load_risk_factors_from_db_flag=True,
                    load_counterparties_flag=False,
                    load_contracts_flag=False
                )
                print(f"  Risk Factors from DB: {len(risk_factors_db)}")
            except Exception as e:
                print(f"  Could not load from DB (expected if tables don't exist): {e}")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
