"""
RiskPro ALM Data Loader - Enhanced Version

Loads comprehensive ALM data including:
- Risk factors (yield curves, spreads, FX rates)
- Counterparties with full credit attributes
- Counterparty classes for credit risk classification
- Contracts with detailed product and valuation attributes

Author: ALM Risk Engineering Team
"""


from datetime import date, datetime
from typing import List, Tuple, Optional, Dict, Any
import logging

# Database connection
try:
    import pyodbc
    HAS_PYODBC = True
except ImportError:
    HAS_PYODBC = False

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

try:
    import cx_Oracle
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


class RiskProConfig:
    """Configuration for RiskPro database connection"""
    
    # Database connection settings
    DB_TYPE = "sqlserver"
    DB_HOST = "127.0.0.1" #"localhost"
    DB_PORT = 1433
    DB_NAME = "RP_1225"
    DB_USER = "RP_1225"  # UPDATE THIS
    DB_PASSWORD = "RP_1225"  # UPDATE THIS
    
    # Schema
    SCHEMA = "dbo"
    
    # Table names
    CONTRACTS_TABLE = "CONTRACT"
    COUNTERPARTY_TABLE = "COUNTERPARTY"
    COUNTERPARTY_CLASS_TABLE = "COUNTERPARTY_CLASS"
    RATING_TABLE = "RATING_CLASS"
    YIELD_CURVE_TABLE = "OBS_YIELD_CURVE"
    SPREAD_CURVE_TABLE = "OBS_SPREAD_CURVE"
    FX_RATE_TABLE = "OBS_FX_RATE"
    
    # Valuation date
    VALUATION_DATE = datetime(2025, 12, 1).date()
    
    @classmethod
    def get_connection_string(cls) -> str:
        """Get database connection string"""
        if cls.DB_TYPE == "sqlserver":
            return (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={cls.DB_HOST},{cls.DB_PORT};"
                f"DATABASE={cls.DB_NAME};"
                f"UID={cls.DB_USER};"
                f"PWD={cls.DB_PASSWORD}"
            )
        elif cls.DB_TYPE == "oracle":
            return f"{cls.DB_USER}/{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        elif cls.DB_TYPE == "postgresql":
            return f"host={cls.DB_HOST} port={cls.DB_PORT} dbname={cls.DB_NAME} user={cls.DB_USER} password={cls.DB_PASSWORD}"
        else:
            raise ValueError(f"Unsupported DB type: {cls.DB_TYPE}")


def get_database_connection():
    """Establish connection to RiskPro database"""
    db_type = RiskProConfig.DB_TYPE
    conn_str = RiskProConfig.get_connection_string()
    
    try:
        if db_type == "sqlserver":
            if not HAS_PYODBC:
                raise ImportError("pyodbc not installed")
            return pyodbc.connect(conn_str)
        elif db_type == "oracle":
            if not HAS_ORACLE:
                raise ImportError("cx_Oracle not installed")
            return cx_Oracle.connect(conn_str)
        elif db_type == "postgresql":
            if not HAS_PSYCOPG2:
                raise ImportError("psycopg2 not installed")
            return psycopg2.connect(conn_str)
        else:
            raise ValueError(f"Unsupported DB type: {db_type}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


def load_yield_curves(conn) -> List[YieldCurve]:
    """Load yield curves directly from OBS_YIELD_CURVE table"""
    logger.info("Loading yield curves...")
    
    curves = []
    cursor = conn.cursor()
    
    query = f"""
    SELECT 
        CURVE_ID,
        CURRENCY,
        TENOR,
        RATE,
        AS_OF_DATE
    FROM {RiskProConfig.SCHEMA}.{RiskProConfig.YIELD_CURVE_TABLE}
    WHERE AS_OF_DATE = ?
    ORDER BY CURVE_ID, TENOR
    """
    
    try:
        cursor.execute(query, (RiskProConfig.VALUATION_DATE,))
        
        curves_dict = {}
        for row in cursor.fetchall():
            curve_id = row[0]
            if curve_id not in curves_dict:
                curves_dict[curve_id] = {
                    'curve_id': str(curve_id),
                    'currency': row[1] or 'USD',
                    'tenors': [],
                    'rates': []
                }
            curves_dict[curve_id]['tenors'].append(str(row[2]))
            curves_dict[curve_id]['rates'].append(float(row[3]) if row[3] else 0.0)
        
        for curve_data in curves_dict.values():
            curve = YieldCurve(
                factor_id=curve_data['curve_id'],
                currency=curve_data['currency'],
                description=f"Yield Curve {curve_data['curve_id']}",
                tenors=curve_data['tenors'],
                rates=curve_data['rates']
            )
            curves.append(curve)
        
        logger.info(f"Loaded {len(curves)} yield curves")
    except Exception as e:
        logger.warning(f"Could not load yield curves: {e}")
    finally:
        cursor.close()
    
    return curves


def load_spread_curves(conn) -> List[SpreadCurve]:
    """Load spread curves directly from OBS_SPREAD_CURVE table"""
    logger.info("Loading spread curves...")
    
    curves = []
    cursor = conn.cursor()
    
    query = f"""
    SELECT 
        CURVE_ID,
        CURRENCY,
        RATING,
        TENOR,
        SPREAD,
        AS_OF_DATE
    FROM {RiskProConfig.SCHEMA}.{RiskProConfig.SPREAD_CURVE_TABLE}
    WHERE AS_OF_DATE = ?
    ORDER BY CURVE_ID, TENOR
    """
    
    try:
        cursor.execute(query, (RiskProConfig.VALUATION_DATE,))
        
        curves_dict = {}
        for row in cursor.fetchall():
            curve_id = row[0]
            if curve_id not in curves_dict:
                curves_dict[curve_id] = {
                    'curve_id': str(curve_id),
                    'currency': row[1] or 'USD',
                    'rating': row[2] or 'BBB',
                    'tenors': [],
                    'spreads': []
                }
            curves_dict[curve_id]['tenors'].append(str(row[3]))
            curves_dict[curve_id]['spreads'].append(float(row[4]) if row[4] else 0.0)
        
        for curve_data in curves_dict.values():
            curve = SpreadCurve(
                factor_id=curve_data['curve_id'],
                currency=curve_data['currency'],
                rating=curve_data['rating'],
                spread_type="credit",
                description=f"Spread Curve {curve_data['curve_id']}",
                tenors=curve_data['tenors'],
                spreads=curve_data['spreads']
            )
            curves.append(curve)
        
        logger.info(f"Loaded {len(curves)} spread curves")
    except Exception as e:
        logger.warning(f"Could not load spread curves: {e}")
    finally:
        cursor.close()
    
    return curves


def load_fx_rates(conn) -> List[FXRate]:
    """Load FX rates directly from OBS_FX_RATE table"""
    logger.info("Loading FX rates...")
    
    fx_rates = []
    cursor = conn.cursor()
    
    query = f"""
    SELECT 
        CURRENCY_PAIR,
        BASE_CURRENCY,
        QUOTE_CURRENCY,
        SPOT_RATE,
        AS_OF_DATE
    FROM {RiskProConfig.SCHEMA}.{RiskProConfig.FX_RATE_TABLE}
    WHERE AS_OF_DATE = ?
    """
    
    try:
        cursor.execute(query, (RiskProConfig.VALUATION_DATE,))
        
        for row in cursor.fetchall():
            fx_rate = FXRate(
                factor_id=row[0] or f"{row[1]}{row[2]}",
                currency_pair=row[0] or f"{row[1]}/{row[2]}",
                base_currency=row[1] or 'USD',
                quote_currency=row[2] or 'CHF',
                spot_rate=float(row[3]) if row[3] else 1.0
            )
            fx_rates.append(fx_rate)
        
        logger.info(f"Loaded {len(fx_rates)} FX rates")
    except Exception as e:
        logger.warning(f"Could not load FX rates: {e}")
    finally:
        cursor.close()
    
    return fx_rates


def load_equity_indices(conn) -> List[EquityIndex]:
    """Placeholder for equity indices"""
    logger.info("Loading equity indices...")
    return []


def load_macro_factors(conn) -> List[MacroFactor]:
    """Placeholder for macro factors"""
    logger.info("Loading macro factors...")
    return []


def load_all_risk_factors(conn) -> List[RiskFactor]:
    """Load all risk factors"""
    logger.info("Loading all risk factors...")
    
    risk_factors = []
    risk_factors.extend(load_yield_curves(conn))
    risk_factors.extend(load_spread_curves(conn))
    risk_factors.extend(load_fx_rates(conn))
    risk_factors.extend(load_equity_indices(conn))
    risk_factors.extend(load_macro_factors(conn))
    
    logger.info(f"Total risk factors loaded: {len(risk_factors)}")
    return risk_factors


def load_counterparty_classes(conn) -> Dict[str, Dict[str, Any]]:
    """
    Load counterparty class definitions from COUNTERPARTY_CLASS table.
    Returns a dictionary mapping COUNTERPARTY_CLASS_ID to class details.
    """
    logger.info("Loading counterparty classes...")
    
    classes = {}
    cursor = conn.cursor()
    
    query = f"""
    SELECT 
        COUNTERPARTY_CLASS_ID,
        ATTRIBUTE_RANGE_ID,
        NAME,
        RANK,
        CODE,
        DESCRIPTION
    FROM {RiskProConfig.SCHEMA}.{RiskProConfig.COUNTERPARTY_CLASS_TABLE}
    """
    
    try:
        cursor.execute(query)
        
        for row in cursor.fetchall():
            class_id = str(row[0]) if row[0] else None
            if class_id:
                classes[class_id] = {
                    'counterparty_class_id': class_id,
                    'attribute_range_id': str(row[1]) if row[1] else None,
                    'name': row[2] if row[2] else None,
                    'rank': int(row[3]) if row[3] is not None else None,
                    'code': row[4] if row[4] else None,
                    'description': row[5] if row[5] else None
                }
        
        logger.info(f"Loaded {len(classes)} counterparty classes")
    except Exception as e:
        logger.warning(f"Could not load counterparty classes: {e}")
    finally:
        cursor.close()
    
    return classes


def load_counterparties(conn, counterparty_classes: Dict[str, Dict[str, Any]]) -> List[Counterparty]:
    """
    Load counterparties with enhanced attributes from COUNTERPARTY table.
    Enriched with counterparty class information.
    """
    logger.info("Loading counterparties...")
    
    counterparties = []
    cursor = conn.cursor()
    
    query = f"""
    SELECT TOP 10000
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
    FROM {RiskProConfig.SCHEMA}.{RiskProConfig.COUNTERPARTY_TABLE}
    """
    
    try:
        cursor.execute(query)
        
        for row in cursor.fetchall():
            counterparty_id = str(row[0]) if row[0] else None
            if not counterparty_id:
                continue
            
            # Get counterparty class details
            cp_class_id = str(row[4]) if row[4] else None
            cp_class_info = counterparty_classes.get(cp_class_id, {})
            
            # Extract values
            pd_value = float(row[5]) if row[5] is not None else 0.01
            lgd_market = float(row[8]) if row[8] is not None else 0.60
            recovery_rate = 1.0 - lgd_market  # Convert LGD to recovery rate
            is_npl = bool(row[10]) if row[10] is not None else False
            
            # Create enhanced counterparty with additional attributes
            counterparty = Counterparty(
                counterparty_id=counterparty_id,
                name=row[6] or "Unknown",
                rating=cp_class_info.get('name', 'NR'),  # Use class name as rating
                pd=pd_value,
                recovery_rate=recovery_rate,
                sector=row[11],  # INDUSTRY
                country=row[2]   # LEGAL_COUNTRY
            )
            
            # Add extended attributes for LLM context
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
        
        logger.info(f"Loaded {len(counterparties)} counterparties")
    except Exception as e:
        logger.warning(f"Could not load counterparties: {e}")
        import traceback
        logger.warning(traceback.format_exc())
    finally:
        cursor.close()
    
    return counterparties


def map_contract_type(product_type: str) -> ContractType:
    """Map RiskPro product type to ContractType enum"""
    if not product_type:
        return ContractType.LOAN
    
    product_type = product_type.upper()
    
    type_mapping = {
        'LOAN': ContractType.LOAN,
        'MORTGAGE': ContractType.LOAN,
        'ANN': ContractType.LOAN,
        'PAM': ContractType.LOAN,
        'RGM': ContractType.LOAN,
        'NGM': ContractType.LOAN,
        'DEPOSIT': ContractType.DEPOSIT,
        'DSC': ContractType.DEPOSIT,
        'BOND': ContractType.BOND,
        'BNDIDX': ContractType.BOND,
        'PBN': ContractType.BOND,
        'ZCB': ContractType.BOND,
        'SWAP': ContractType.SWAP,
        'IRSWP': ContractType.SWAP,
        'FXSWP': ContractType.SWAP,
        'FORWARD': ContractType.FORWARD,
        'FXFWD': ContractType.FORWARD,
        'OPTION': ContractType.OPTION,
        'FXOP': ContractType.OPTION,
        'FACILITY': ContractType.FACILITY,
        'FACIL': ContractType.FACILITY,
    }
    
    for key, value in type_mapping.items():
        if key in product_type:
            return value
    
    return ContractType.LOAN


def load_contracts(conn, limit: Optional[int] = None) -> List[Contract]:
    """
    Load contracts with enhanced attributes from CONTRACT table.
    Includes valuation, credit risk, and product classification details.
    """
    logger.info("Loading contracts...")
    
    contracts = []
    cursor = conn.cursor()
    
    limit_clause = f"TOP {limit}" if limit else "TOP 1000"
    
    query = f"""
    SELECT {limit_clause}
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
    FROM {RiskProConfig.SCHEMA}.{RiskProConfig.CONTRACTS_TABLE}
    ORDER BY CONTRACT_ID
    """
    
    try:
        cursor.execute(query)
        
        for row in cursor.fetchall():
            contract_id = str(row[0]) if row[0] else None
            if not contract_id:
                continue
            
            # Extract core attributes
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
            
            # Get currency from notional or default
            notional_value = float(row[17]) if row[17] is not None else 0.0
            original_principal = float(row[11]) if row[11] is not None else notional_value
            
            # Create contract
            contract = Contract(
                contract_id=contract_id,
                contract_type=map_contract_type(row[14]),  # PRODUCT_TYPE
                currency='CHF',  # Default, adjust if you have currency field
                notional=notional_value,
                maturity_date=maturity_date,
                linked_yield_curve=None,  # Not in this query
                linked_spread_curve=None,  # Not in this query
                counterparty_id=None,  # Not in this query
                is_asset=is_asset,
                rate=None  # Not in this query
            )
            
            # Add extended attributes for LLM context
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
        
        logger.info(f"Loaded {len(contracts)} contracts")
    except Exception as e:
        logger.error(f"Could not load contracts: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        cursor.close()
    
    return contracts


def load_from_riskpro(
    limit_contracts: Optional[int] = None
) -> Tuple[List[RiskFactor], List[Counterparty], List[Contract]]:
    """
    Main function to load all ALM data from RiskPro database.
    
    Args:
        limit_contracts: Optional limit on number of contracts
    
    Returns:
        Tuple of (risk_factors, counterparties, contracts)
    """
    logger.info("=" * 80)
    logger.info("LOADING ENHANCED ALM DATA FROM RISKPRO")
    logger.info("=" * 80)
    logger.info(f"Database: {RiskProConfig.DB_TYPE}")
    logger.info(f"Host: {RiskProConfig.DB_HOST}")
    logger.info(f"Database: {RiskProConfig.DB_NAME}")
    logger.info(f"Valuation Date: {RiskProConfig.VALUATION_DATE}")
    logger.info("")
    
    try:
        logger.info("Connecting to database...")
        conn = get_database_connection()
        logger.info("✓ Connected successfully")
        logger.info("")
        
        # Load counterparty classes first
        counterparty_classes = load_counterparty_classes(conn)
        
        # Load data
        risk_factors = load_all_risk_factors(conn)
        counterparties = load_counterparties(conn, counterparty_classes)
        contracts = load_contracts(conn, limit=limit_contracts)
        
        conn.close()
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("LOADING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"✓ Risk factors: {len(risk_factors)}")
        logger.info(f"✓ Counterparty classes: {len(counterparty_classes)}")
        logger.info(f"✓ Counterparties: {len(counterparties)}")
        logger.info(f"✓ Contracts: {len(contracts)}")
        logger.info("")
        
        return risk_factors, counterparties, contracts
    
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        logger.error("Check:")
        logger.error("1. Database connection settings")
        logger.error("2. Database credentials")
        logger.error("3. Table and column names match your schema")
        raise