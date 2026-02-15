# risk_attribute_loader_extended.py
"""
Extended Risk Attribute Loader

This module integrates with load_alm_data.py to extract and classify
risk attributes from RiskPro CONTRACT and COUNTERPARTY tables according
to the four logical categories:

1. Market Risk-Linked
2. Credit Risk-Linked
3. Behavioral Risk-Linked
4. Cross-Risk / Control

Usage:
    from risk_attribute_loader_extended import extract_risk_attributes
    
    # After loading contracts
    contracts, counterparties = load_from_riskpro(...)
    
    # Extract classified risk attributes
    risk_attr_sets = extract_risk_attributes(contracts, counterparties)
    
    # Now available for scenario generation with proper classification

Author: ALM Risk Engineering Team
"""

from typing import List, Dict, Optional, Tuple
import logging
from collections import defaultdict

from risk_attributes import (
    MarketRiskAttribute,
    MarketRiskCategory,
    CreditRiskAttribute,
    CreditRiskCategory,
    BehavioralRiskAttribute,
    BehavioralRiskCategory,
    ControlAttribute,
    ControlAttributeCategory,
    RiskAttributeSet
)

logger = logging.getLogger(__name__)


# ============================================================================
# ATTRIBUTE FIELD MAPPINGS
# ============================================================================

# Map RiskPro column names to MarketRiskAttribute fields
MARKET_RISK_FIELD_MAP = {
    # Currency & FX
    'CURRENCY_DEF': 'currency_def',
    'DOM_CURRENCY_DEF': 'dom_currency_def',
    'FOR_CURRENCY_DEF': 'for_currency_def',
    'CONTRACTED_FX_RATE': 'contracted_fx_rate',
    'FX_RATE_AT_CDD': 'fx_rate_at_cdd',
    'FX_RATE': 'contracted_fx_rate',  # Alias
    
    # Yield / Discount / IR
    'PRICING_MARKET_OBJECT': 'pricing_market_object',
    'DISC_MARKET_OBJECT': 'disc_market_object',
    'DISCOUNT_RATE': 'discount_rate',
    'CURRENT_NOMINAL_INT_RATE': 'current_nominal_int_rate',
    'NEXT_REPRICING_RATE': 'next_repricing_rate',
    'CONST_EFFECT_YIELD': 'const_effect_yield',
    
    # Spreads
    'DSCNG_SPREAD': 'dscng_spread',
    'CONTRACT_SPREAD': 'contract_spread',
    'OBSERVED_CREDIT_SPREAD': 'observed_credit_spread',
    'CREDIT_SPREAD_CURVE_DEF': 'credit_spread_curve_def',
    'SPREAD_CURVE_DEF': 'spread_curve_def',
    'CREDIT_SPREAD': 'observed_credit_spread',  # Alias
    
    # Equity / Commodity
    'STOCK_INDEX_DEF': 'stock_index_def',
    'COMMODITY_INDEX_DEF': 'commodity_index_def',
    'COMMODITY_PRICING_MARKET_OBJ': 'commodity_pricing_market_obj',
    'DIVIDEND_RATE': 'dividend_rate',
    'BETA_AT_MVD': 'beta_at_mvd',
    
    # Volatility
    'VOLATILITY_SURFACE_DEF': 'volatility_surface_def',
    'VOLATILITY_AT_MVD': 'volatility_at_mvd',
    'FUT_VOLATILITY_AT_MVD': 'fut_volatility_at_mvd',
    
    # Inflation
    'CSM_PRICE_INDEX_DEF': 'csm_price_index_def',
    'ORIGINAL_CPI': 'original_cpi',
    'INDEXATION_LAG_COUNT': 'indexation_lag_count',
    'INDEXATION_LAG_UNIT': 'indexation_lag_unit',
    
    # Valuation / MTM
    'MARKET_VALUE_OBSERVED': 'market_value_observed',
    'QUOTED_PRICE_AT_MVD': 'quoted_price_at_mvd',
    'FUT_QUOTED_PRICE_AT_MVD': 'fut_quoted_price_at_mvd',
    'PRICE_AT_TD': 'price_at_td',
    'PRICE_AT_CDD': 'price_at_cdd',
    'FUTURE_PRICE': 'future_price',
    'UNDERLYING_MVO': 'underlying_mvo',
    'MARKET_VALUE': 'market_value_observed',  # Alias
}

# Map RiskPro column names to CreditRiskAttribute fields
CREDIT_RISK_FIELD_MAP = {
    # Counterparty & reference entities
    'COUNTERPARTY_SSRN': 'counterparty_ssrn',
    'REFERENCE_ENTITY_SSRN': 'reference_entity_ssrn',
    'ISSUER_SSRN': 'issuer_ssrn',
    'CREDIT_LINE_SSRN': 'credit_line_ssrn',
    'COUNTERPARTY_ID': 'counterparty_ssrn',  # Alias
    
    # Ratings & PD
    'RATING_SCALE': 'rating_scale',
    'RATING_CLASS': 'rating_class',
    'DEFAULT_PROBABILITY': 'default_probability',
    'PD_AMORTIZATION_DATE': 'pd_amortization_date',
    'PD': 'default_probability',  # Alias
    'RATING': 'rating_class',  # Alias
    
    # Recovery / LGD / Collateral
    'GROSS_RECOVERY_RATE': 'gross_recovery_rate',
    'NET_RECOVERY_RATE': 'net_recovery_rate',
    'HAIRCUT': 'haircut',
    'CR_CAD_COLLATERAL_TYPE': 'cr_cad_collateral_type',
    'NOMINAL_VALUE_OF_GUARANTEE': 'nominal_value_of_guarantee',
    'RECOVERY_RATE': 'gross_recovery_rate',  # Alias
    'LGD': 'haircut',  # Can map LGD to haircut as related concept
    
    # Default & impairment
    'NON_PERFORMING_DATE': 'non_performing_date',
    'WRITE_OFF_AMOUNT': 'write_off_amount',
    'WRITE_OFF_AMOUNT_IFRS': 'write_off_amount_ifrs',
    'CREDIT_RISK_PROVISION': 'credit_risk_provision',
    'CREDIT_RISK_PROVISION_IFRS': 'credit_risk_provision_ifrs',
    
    # Netting & mitigation
    'CLOSE_OUT_NETTING': 'close_out_netting',
    'ON_BALANCE_SHEET_NETTING': 'on_balance_sheet_netting',
    'CR_CAD_CONVERSION_FACTOR': 'cr_cad_conversion_factor',
    'CCF': 'cr_cad_conversion_factor',  # Alias
}

# Map RiskPro column names to BehavioralRiskAttribute fields
BEHAVIORAL_RISK_FIELD_MAP = {
    # Optionality
    'OPTION_TYPE_ID': 'option_type_id',
    'OPTION_EXERCISE_BEGIN_DATE': 'option_exercise_begin_date',
    'OPTION_EXERCISE_END_DATE': 'option_exercise_end_date',
    'OPTION_STRIKE_CALL': 'option_strike_call',
    'OPTION_STRIKE_PUT': 'option_strike_put',
    'OPTION_TYPE': 'option_type_id',  # Alias
    
    # Prepayment / amortization / renegotiation
    'REF_AMORTIZATION_TYPE_ID': 'ref_amortization_type_id',
    'AMORTIZATION_DATE': 'amortization_date',
    'REF_GRACE_TYPE_ID': 'ref_grace_type_id',
    'RENEGOTIATION_ID': 'renegotiation_id',
    'AMORTIZATION_TYPE': 'ref_amortization_type_id',  # Alias
    
    # Behavior cycles
    'PRE_FIXING_PERIOD': 'pre_fixing_period',
    'FIXING_DAYS_COUNT': 'fixing_days_count',
}

# Map RiskPro column names to ControlAttribute fields
CONTROL_ATTRIBUTE_FIELD_MAP = {
    # Scenario control
    'MODEL_ID': 'model_id',
    'REF_SIMULATION_TYPE_ID': 'ref_simulation_type_id',
    'REF_REFERENCE_RISK_FACTOR_ID': 'ref_reference_risk_factor_id',
    
    # Liquidity & funding
    'REF_LIQUIDITY_LEVEL_TYPE_ID': 'ref_liquidity_level_type_id',
    'FTP_LIQUIDITY_SPREAD': 'ftp_liquidity_spread',
    'FTP_CREDIT_RISK_SPREAD': 'ftp_credit_risk_spread',
    'LIMIT_AMOUNT': 'limit_amount',
    'MARGIN_REQUIRED': 'margin_required',
    
    # Segmentation
    'PRODUCT_TYPE': 'product_type',
    'SEGMENT': 'segment',
    'MAIN_INDUSTRY': 'main_industry',
    'NATIONAL_MARKET': 'national_market',
    'LEGAL_ENTITY': 'legal_entity',
    
    # Insurance stress
    'ATTRITIONAL_INS_RF_DEF': 'attritional_ins_rf_def',
    'CATASTROPHIC_INS_RF_DEF': 'catastrophic_ins_rf_def',
    'LARGE_INS_RF_DEF': 'large_ins_rf_def',
    'PRIOR_CLAIMS': 'prior_claims',
}


# ============================================================================
# EXTRACTION LOGIC
# ============================================================================

def determine_market_risk_category(field_data: Dict[str, Any]) -> MarketRiskCategory:
    """
    Determine which market risk subcategory this contract belongs to.
    
    Args:
        field_data: Dictionary of populated market risk fields
        
    Returns:
        Appropriate MarketRiskCategory
    """
    # Check for FX-related fields
    if any(k in field_data for k in ['contracted_fx_rate', 'fx_rate_at_cdd', 'currency_def']):
        return MarketRiskCategory.CURRENCY_FX
    
    # Check for volatility fields
    if any(k in field_data for k in ['volatility_surface_def', 'volatility_at_mvd']):
        return MarketRiskCategory.VOLATILITY
    
    # Check for equity/commodity fields
    if any(k in field_data for k in ['stock_index_def', 'commodity_index_def', 'beta_at_mvd']):
        return MarketRiskCategory.EQUITY_COMMODITY
    
    # Check for spread fields
    if any(k in field_data for k in ['contract_spread', 'observed_credit_spread', 'dscng_spread']):
        return MarketRiskCategory.SPREADS
    
    # Check for inflation fields
    if any(k in field_data for k in ['csm_price_index_def', 'original_cpi']):
        return MarketRiskCategory.INFLATION
    
    # Check for valuation/MTM fields
    if any(k in field_data for k in ['market_value_observed', 'quoted_price_at_mvd']):
        return MarketRiskCategory.VALUATION_MTM
    
    # Default to yield/IR
    return MarketRiskCategory.YIELD_DISCOUNT_IR


def determine_credit_risk_category(field_data: Dict[str, Any]) -> CreditRiskCategory:
    """Determine which credit risk subcategory"""
    if any(k in field_data for k in ['default_probability', 'rating_class']):
        return CreditRiskCategory.RATINGS_PD
    if any(k in field_data for k in ['gross_recovery_rate', 'haircut']):
        return CreditRiskCategory.RECOVERY_LGD
    if any(k in field_data for k in ['non_performing_date', 'write_off_amount']):
        return CreditRiskCategory.DEFAULT_IMPAIRMENT
    if any(k in field_data for k in ['close_out_netting', 'cr_cad_conversion_factor']):
        return CreditRiskCategory.NETTING_MITIGATION
    return CreditRiskCategory.COUNTERPARTY_REF


def determine_behavioral_risk_category(field_data: Dict[str, Any]) -> BehavioralRiskCategory:
    """Determine which behavioral risk subcategory"""
    if any(k in field_data for k in ['option_type_id', 'option_strike_call']):
        return BehavioralRiskCategory.OPTIONALITY
    if any(k in field_data for k in ['ref_amortization_type_id', 'amortization_date']):
        return BehavioralRiskCategory.PREPAYMENT_AMORTIZATION
    return BehavioralRiskCategory.BEHAVIOR_CYCLES


def determine_control_category(field_data: Dict[str, Any]) -> ControlAttributeCategory:
    """Determine which control attribute subcategory"""
    if any(k in field_data for k in ['model_id', 'ref_simulation_type_id']):
        return ControlAttributeCategory.SCENARIO_CONTROL
    if any(k in field_data for k in ['ftp_liquidity_spread', 'limit_amount']):
        return ControlAttributeCategory.LIQUIDITY_FUNDING
    if any(k in field_data for k in ['attritional_ins_rf_def', 'prior_claims']):
        return ControlAttributeCategory.INSURANCE_STRESS
    return ControlAttributeCategory.SEGMENTATION


def extract_market_risk_attrs(contract) -> Optional[MarketRiskAttribute]:
    """
    Extract market risk attributes from a contract's extended_attributes.
    
    Args:
        contract: Contract object with extended_attributes dict
        
    Returns:
        MarketRiskAttribute if any relevant fields found, else None
    """
    if not hasattr(contract, 'extended_attributes') or not contract.extended_attributes:
        return None
    
    ext_attrs = contract.extended_attributes
    field_data = {}
    extended = {}
    
    # Extract mapped fields
    for riskpro_col, attr_field in MARKET_RISK_FIELD_MAP.items():
        if riskpro_col in ext_attrs and ext_attrs[riskpro_col] is not None:
            field_data[attr_field] = ext_attrs[riskpro_col]
    
    # Collect unmapped market-related fields into extended
    market_keywords = ['RATE', 'PRICE', 'VALUE', 'SPREAD', 'CURRENCY', 'FX', 'VOLATILITY', 'INDEX']
    for col, val in ext_attrs.items():
        if col not in MARKET_RISK_FIELD_MAP and any(kw in col for kw in market_keywords):
            extended[col] = val
    
    if not field_data and not extended:
        return None
    
    # Determine category
    category = determine_market_risk_category(field_data)
    
    # Create attribute object
    return MarketRiskAttribute(
        attribute_name=f"market_{contract.contract_id}",
        category=category,
        contract_id=contract.contract_id,
        extended=extended,
        **field_data
    )


def extract_credit_risk_attrs(contract, counterparties: Dict[str, Any]) -> Optional[CreditRiskAttribute]:
    """
    Extract credit risk attributes from contract and linked counterparty.
    
    Args:
        contract: Contract object
        counterparties: Dict mapping counterparty_id -> Counterparty object
        
    Returns:
        CreditRiskAttribute if any relevant fields found, else None
    """
    field_data = {}
    extended = {}
    
    # Extract from contract extended_attributes
    if hasattr(contract, 'extended_attributes') and contract.extended_attributes:
        ext_attrs = contract.extended_attributes
        
        for riskpro_col, attr_field in CREDIT_RISK_FIELD_MAP.items():
            if riskpro_col in ext_attrs and ext_attrs[riskpro_col] is not None:
                field_data[attr_field] = ext_attrs[riskpro_col]
    
    # Extract from linked counterparty
    if hasattr(contract, 'counterparty_id') and contract.counterparty_id:
        cp = counterparties.get(contract.counterparty_id)
        if cp:
            if hasattr(cp, 'pd') and cp.pd is not None:
                field_data['default_probability'] = cp.pd
            if hasattr(cp, 'recovery_rate') and cp.recovery_rate is not None:
                field_data['gross_recovery_rate'] = cp.recovery_rate
            if hasattr(cp, 'rating') and cp.rating:
                field_data['rating_class'] = cp.rating
            if hasattr(cp, 'counterparty_id'):
                field_data['counterparty_ssrn'] = cp.counterparty_id
    
    if not field_data:
        return None
    
    # Determine category
    category = determine_credit_risk_category(field_data)
    
    return CreditRiskAttribute(
        attribute_name=f"credit_{contract.contract_id}",
        category=category,
        contract_id=contract.contract_id,
        extended=extended,
        **field_data
    )


def extract_behavioral_risk_attrs(contract) -> Optional[BehavioralRiskAttribute]:
    """Extract behavioral risk attributes from contract"""
    if not hasattr(contract, 'extended_attributes') or not contract.extended_attributes:
        return None
    
    ext_attrs = contract.extended_attributes
    field_data = {}
    extended = {}
    
    # Extract mapped fields
    for riskpro_col, attr_field in BEHAVIORAL_RISK_FIELD_MAP.items():
        if riskpro_col in ext_attrs and ext_attrs[riskpro_col] is not None:
            field_data[attr_field] = ext_attrs[riskpro_col]
    
    # Extract behavior cycle fields (IP_*, FIX_*, VAR_*, etc.)
    cycle_prefixes = ['IP_', 'FIX_', 'VAR_', 'INC_', 'DEC_', 'RP_']
    cycle_data = {
        'ip_fields': {},
        'fix_fields': {},
        'var_fields': {},
        'inc_fields': {},
        'dec_fields': {},
        'rp_fields': {}
    }
    
    for col, val in ext_attrs.items():
        for prefix in cycle_prefixes:
            if col.startswith(prefix):
                field_key = prefix.lower().rstrip('_') + '_fields'
                cycle_data[field_key][col] = val
    
    # Add non-empty cycle data to field_data
    for key, data in cycle_data.items():
        if data:
            field_data[key] = data
    
    if not field_data:
        return None
    
    # Determine category
    category = determine_behavioral_risk_category(field_data)
    
    return BehavioralRiskAttribute(
        attribute_name=f"behavioral_{contract.contract_id}",
        category=category,
        contract_id=contract.contract_id,
        extended=extended,
        **field_data
    )


def extract_control_attrs(contract) -> Optional[ControlAttribute]:
    """Extract control/segmentation attributes from contract"""
    if not hasattr(contract, 'extended_attributes'):
        # Still create basic control attributes from core contract fields
        field_data = {}
    else:
        ext_attrs = contract.extended_attributes or {}
        field_data = {}
        
        for riskpro_col, attr_field in CONTROL_ATTRIBUTE_FIELD_MAP.items():
            if riskpro_col in ext_attrs and ext_attrs[riskpro_col] is not None:
                field_data[attr_field] = ext_attrs[riskpro_col]
    
    # Also extract from core contract fields
    if hasattr(contract, 'contract_type') and contract.contract_type:
        field_data['product_type'] = str(contract.contract_type)
    
    if not field_data:
        return None
    
    # Determine category
    category = determine_control_category(field_data)
    
    return ControlAttribute(
        attribute_name=f"control_{contract.contract_id}",
        category=category,
        contract_id=contract.contract_id,
        **field_data
    )


def extract_risk_attributes(
    contracts: List,
    counterparties: List = None
) -> List[RiskAttributeSet]:
    """
    Main entry point: Extract all risk attributes from contracts.
    
    Args:
        contracts: List of Contract objects
        counterparties: Optional list of Counterparty objects
        
    Returns:
        List of RiskAttributeSet objects, one per contract
    """
    logger.info(f"Extracting risk attributes from {len(contracts)} contracts...")
    
    # Build counterparty lookup
    cp_lookup = {}
    if counterparties:
        for cp in counterparties:
            if hasattr(cp, 'counterparty_id'):
                cp_lookup[cp.counterparty_id] = cp
    
    # Extract attributes for each contract
    risk_attr_sets = []
    stats = defaultdict(int)
    
    for contract in contracts:
        contract_id = contract.contract_id if hasattr(contract, 'contract_id') else 'unknown'
        
        # Extract all four categories
        market = extract_market_risk_attrs(contract)
        credit = extract_credit_risk_attrs(contract, cp_lookup)
        behavioral = extract_behavioral_risk_attrs(contract)
        control = extract_control_attrs(contract)
        
        # Track statistics
        if market:
            stats['market'] += 1
        if credit:
            stats['credit'] += 1
        if behavioral:
            stats['behavioral'] += 1
        if control:
            stats['control'] += 1
        
        # Create unified attribute set
        attr_set = RiskAttributeSet(
            contract_id=contract_id,
            market_risk=market,
            credit_risk=credit,
            behavioral_risk=behavioral,
            control=control
        )
        
        risk_attr_sets.append(attr_set)
    
    # Log summary
    logger.info("=" * 60)
    logger.info("RISK ATTRIBUTE EXTRACTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total contracts processed: {len(contracts)}")
    logger.info(f"Contracts with Market Risk attrs: {stats['market']}")
    logger.info(f"Contracts with Credit Risk attrs: {stats['credit']}")
    logger.info(f"Contracts with Behavioral Risk attrs: {stats['behavioral']}")
    logger.info(f"Contracts with Control attrs: {stats['control']}")
    logger.info("=" * 60)
    
    return risk_attr_sets
