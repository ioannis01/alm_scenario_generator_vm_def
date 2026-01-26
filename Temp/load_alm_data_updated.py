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
    DB_NAME = "RP_1225"
    DB_USER = "RP_1225"
    DB_PASSWORD = "RP_1225"
    SCHEMA = "dbo"
    
    # RiskPro tables that exist:
    # - CONTRACT
    # - COUNTERPARTY
    # - COUNTERPARTY_CLASS
    # - RATING_CLASS
    
    # Note: No OBS_YIELD_CURVE, OBS_SPREAD_CURVE, OBS_FX_RATE tables
    # So we use sample data for risk factors
    
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
        logger.error(f"Failed to connect: {e}")
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


def load_counterparties(conn, counterparty_classes: Dict, **kwargs) -> List[Counterparty]:
    """
    Load counterparties from COUNTERPARTY table with enhanced attributes.
    Enriched with counterparty class information.
    """
    logger.info("Loading counterparties from RiskPro...")
    
    counterparties = []
    cursor = conn.cursor()
    
    # Build query with optional model_id filter
    base_query = """
    SELECT TOP {limit}
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
    """
    
    limit = kwargs.get('limit', 10000)
    model_id = kwargs.get('model_id')
    
    where_clause = f"WHERE MODEL_ID = '{model_id}'" if model_id else ""
    query = base_query.format(limit=limit, where_clause=where_clause)
    
    try:
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
        
        logger.info(f"✓ Loaded {len(counterparties)} counterparties")
    except Exception as e:
        logger.error(f"✗ Could not load counterparties: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
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


def load_contracts(conn, limit: Optional[int] = None, **kwargs) -> List[Contract]:
    """
    Load contracts from CONTRACT table with enhanced attributes.
    Includes valuation, credit risk, and product classification details.
    """
    logger.info("Loading contracts from RiskPro...")
    
    contracts = []
    cursor = conn.cursor()
    
    limit_clause = f"TOP {limit}" if limit else "TOP 1000"
    
    # Add model_id filter if provided
    model_id = kwargs.get('model_id')
    where_clause = f"WHERE MODEL_ID = '{model_id}'" if model_id else ""
    
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
    FROM dbo.CONTRACT
    {where_clause}
    ORDER BY CONTRACT_ID
    """.format(where_clause=where_clause)
    
    try:
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
        
        logger.info(f"✓ Loaded {len(contracts)} contracts")
    except Exception as e:
        logger.error(f"✗ Could not load contracts: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        cursor.close()
    
    return contracts


def load_from_riskpro(
    limit_contracts: Optional[int] = None,
    model_id: Optional[str] = None
) -> Tuple[List[RiskFactor], List[Counterparty], List[Contract]]:
    """
    Load ALM data using hybrid approach:
    - Sample risk factors (RiskPro doesn't have OBS_* tables)
    - Real counterparties from COUNTERPARTY table
    - Real contracts from CONTRACT table
    
    Args:
        limit_contracts: Optional limit on number of contracts
    
    Returns:
        Tuple of (risk_factors, counterparties, contracts)
    """
    logger.info("=" * 80)
    logger.info("LOADING HYBRID ALM DATA FROM RISKPRO")
    logger.info("=" * 80)
    logger.info(f"Database: {RiskProConfig.DB_NAME} @ {RiskProConfig.DB_HOST}")
    if model_id:
        logger.info(f"Model ID filter: {model_id}")
    if limit_contracts:
        logger.info(f"Contract limit: {limit_contracts}")
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
        
        # Step 3: Load RiskPro data
        counterparty_classes = load_counterparty_classes(conn)
        counterparties = load_counterparties(conn, counterparty_classes, model_id=model_id, limit=limit_contracts or 10000)
        contracts = load_contracts(conn, limit=limit_contracts, model_id=model_id)
        
        conn.close()
        
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
        risk_factors, counterparties, contracts = load_from_riskpro(limit_contracts=10)
        
        print("\n" + "=" * 80)
        print("SAMPLE DATA")
        print("=" * 80)
        
        if risk_factors:
            print(f"\nFirst risk factor:")
            print(f"  {risk_factors[0].to_dict()}")
        
        if counterparties:
            print(f"\nFirst counterparty:")
            cp = counterparties[0]
            print(f"  ID: {cp.counterparty_id}")
            print(f"  Name: {cp.name}")
            print(f"  Rating: {cp.rating}")
            print(f"  PD: {cp.pd:.4f}")
            if hasattr(cp, 'extended_attributes'):
                print(f"  Segment: {cp.extended_attributes.get('segment')}")
                print(f"  NPL: {cp.extended_attributes.get('is_non_performing')}")
        
        if contracts:
            print(f"\nFirst contract:")
            ct = contracts[0]
            print(f"  ID: {ct.contract_id}")
            print(f"  Type: {ct.contract_type}")
            print(f"  Notional: {ct.notional:,.2f}")
            if hasattr(ct, 'extended_attributes'):
                print(f"  Product: {ct.extended_attributes.get('product_type')}")
                print(f"  Segment: {ct.extended_attributes.get('segment')}")
                print(f"  Book Value: {ct.extended_attributes.get('book_value'):,.2f}")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
