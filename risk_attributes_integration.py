"""
Risk Attributes Integration for ALM Data Loader

This module enhances the Contract model with classified risk attributes
following RiskPro/OneSumX semantics for the four logical categories:
1. Market Risk
2. Credit Risk
3. Behavioral Risk
4. Control

Integration approach:
- Extends existing load_alm_data.py functionality
- Extracts risk attributes from extended_attributes
- Populates RiskAttributes object on each contract
- Makes attributes available for scenario generation

Author: ALM Risk Engineering Team
"""

from typing import List, Optional
import logging

try:
    from risk_attributes_models import (
        RiskAttributes,
        MarketRiskAttributes,
        CreditRiskAttributes,
        BehavioralRiskAttributes,
        ControlAttributes,
        extract_risk_attributes_from_row,
        summarize_risk_attributes
    )
    RISK_ATTRS_AVAILABLE = True
except ImportError:
    logging.warning("risk_attributes_models not found - risk attribute classification unavailable")
    RISK_ATTRS_AVAILABLE = False


logger = logging.getLogger(__name__)


def enrich_contracts_with_risk_attributes(
    contracts: List,
    counterparties: List = None
) -> List:
    """
    Enhance contracts with classified risk attributes
    
    This function:
    1. Extracts attributes from contract.extended_attributes
    2. Classifies into Market/Credit/Behavioral/Control categories
    3. Attaches RiskAttributes object to each contract
    4. Enriches credit attributes from linked counterparty data
    
    Args:
        contracts: List of Contract objects (from load_alm_data.py)
        counterparties: Optional list of Counterparty objects for credit enrichment
        
    Returns:
        Same contracts list, now with risk_attributes property
        
    Example:
        contracts, counterparties = load_from_riskpro(...)
        contracts = enrich_contracts_with_risk_attributes(contracts, counterparties)
        
        # Now each contract has:
        contract.risk_attributes.market.current_nominal_int_rate
        contract.risk_attributes.credit.default_probability
        contract.risk_attributes.behavioral.option_type_id
        contract.risk_attributes.control.product_type
    """
    if not RISK_ATTRS_AVAILABLE:
        logger.warning("Risk attribute models not available - skipping enrichment")
        return contracts
    
    logger.info("=" * 60)
    logger.info("Enriching contracts with risk attribute classification...")
    logger.info("=" * 60)
    
    # Build counterparty lookup for credit enrichment
    cp_lookup = {}
    if counterparties:
        for cp in counterparties:
            if hasattr(cp, 'counterparty_id'):
                cp_lookup[cp.counterparty_id] = cp
        logger.info(f"Loaded {len(cp_lookup)} counterparties for credit enrichment")
    
    # Enrich each contract
    enriched_count = 0
    
    for contract in contracts:
        # Extract attributes from extended_attributes if available
        if hasattr(contract, 'extended_attributes') and contract.extended_attributes:
            row_data = contract.extended_attributes.copy()
        else:
            row_data = {}
        
        # Add core contract fields to row data for extraction
        if hasattr(contract, 'contract_type'):
            row_data['PRODUCT_TYPE'] = str(contract.contract_type)
        if hasattr(contract, 'currency'):
            row_data['CURRENCY_DEF'] = contract.currency
        
        # Extract and classify risk attributes
        risk_attrs = extract_risk_attributes_from_row(row_data)
        
        # Enrich credit attributes from counterparty if available
        if hasattr(contract, 'counterparty_id') and contract.counterparty_id in cp_lookup:
            cp = cp_lookup[contract.counterparty_id]
            
            # Add counterparty credit attributes
            if hasattr(cp, 'counterparty_id'):
                risk_attrs.credit.counterparty_ssrn = cp.counterparty_id
            if hasattr(cp, 'pd') and cp.pd is not None:
                risk_attrs.credit.default_probability = cp.pd
            if hasattr(cp, 'recovery_rate') and cp.recovery_rate is not None:
                risk_attrs.credit.gross_recovery_rate = cp.recovery_rate
            if hasattr(cp, 'rating'):
                risk_attrs.credit.rating_class = cp.rating
        
        # Attach risk attributes to contract
        contract.risk_attributes = risk_attrs
        enriched_count += 1
    
    logger.info(f"✓ Enriched {enriched_count} contracts with risk attributes")
    
    # Generate summary
    summary = summarize_risk_attributes(contracts)
    
    logger.info("\n" + "=" * 60)
    logger.info("RISK ATTRIBUTE CLASSIFICATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"📊 Market Risk Attributes:")
    logger.info(f"   Contracts with market risk: {summary['market']['count']}")
    logger.info(f"   Active market levers: {', '.join(summary['market']['active_levers'][:10])}")
    
    logger.info(f"\n💳 Credit Risk Attributes:")
    logger.info(f"   Contracts with credit risk: {summary['credit']['count']}")
    logger.info(f"   Active credit levers: {', '.join(summary['credit']['active_levers'][:10])}")
    
    logger.info(f"\n🔄 Behavioral Risk Attributes:")
    logger.info(f"   Contracts with behavioral risk: {summary['behavioral']['count']}")
    logger.info(f"   Active behavioral levers: {', '.join(summary['behavioral']['active_levers'][:10])}")
    
    logger.info(f"\n⚙️  Control Attributes:")
    logger.info(f"   Segmentation dimensions: {', '.join(summary['control']['segments'].keys())}")
    for dim, values in list(summary['control']['segments'].items())[:3]:
        logger.info(f"   {dim}: {len(values)} unique values")
    
    logger.info("=" * 60 + "\n")
    
    return contracts


def get_contracts_by_segment(
    contracts: List,
    segment_key: str,
    segment_value: str
) -> List:
    """
    Filter contracts by segmentation dimension
    
    Args:
        contracts: List of enriched contracts
        segment_key: Segmentation dimension ('product_type', 'segment', etc.)
        segment_value: Value to filter by
        
    Returns:
        Filtered list of contracts
        
    Example:
        loan_contracts = get_contracts_by_segment(contracts, 'product_type', 'LOAN')
        retail_contracts = get_contracts_by_segment(contracts, 'segment', 'RETAIL')
    """
    filtered = []
    
    for contract in contracts:
        if not hasattr(contract, 'risk_attributes'):
            continue
        
        seg = contract.risk_attributes.control.get_segmentation()
        if seg.get(segment_key) == segment_value:
            filtered.append(contract)
    
    return filtered


def get_contracts_with_stress_lever(
    contracts: List,
    category: str,
    lever_name: str
) -> List:
    """
    Find contracts with a specific stress lever
    
    Args:
        contracts: List of enriched contracts
        category: 'market', 'credit', or 'behavioral'
        lever_name: Name of the stress lever to check for
        
    Returns:
        List of contracts with that lever
        
    Example:
        ir_contracts = get_contracts_with_stress_lever(contracts, 'market', 'ir_rate')
        pd_contracts = get_contracts_with_stress_lever(contracts, 'credit', 'pd')
    """
    filtered = []
    
    for contract in contracts:
        if not hasattr(contract, 'risk_attributes'):
            continue
        
        if category == 'market':
            levers = contract.risk_attributes.market.get_stress_levers()
        elif category == 'credit':
            levers = contract.risk_attributes.credit.get_stress_levers()
        elif category == 'behavioral':
            levers = contract.risk_attributes.behavioral.get_stress_levers()
        else:
            continue
        
        if lever_name in levers:
            filtered.append(contract)
    
    return filtered


def extract_stress_context_for_llm(
    contracts: List,
    include_segmentation: bool = True
) -> str:
    """
    Extract risk attribute context for LLM scenario generation
    
    This creates a structured summary of available stress levers
    to inject into LLM prompts for more sophisticated scenario generation.
    
    Args:
        contracts: List of enriched contracts
        include_segmentation: Include segmentation breakdown
        
    Returns:
        Formatted text suitable for LLM context
        
    Example:
        context = extract_stress_context_for_llm(contracts)
        prompt = f"Given this portfolio:\\n{context}\\n\\nGenerate 3 stress scenarios..."
    """
    summary = summarize_risk_attributes(contracts)
    
    lines = []
    lines.append("PORTFOLIO RISK ATTRIBUTE LANDSCAPE:")
    lines.append("")
    
    # Market Risk
    lines.append(f"📊 MARKET RISK DRIVERS ({summary['market']['count']} contracts):")
    if summary['market']['active_levers']:
        lines.append(f"   Available stress levers: {', '.join(summary['market']['active_levers'])}")
    lines.append("")
    
    # Credit Risk
    lines.append(f"💳 CREDIT RISK DRIVERS ({summary['credit']['count']} contracts):")
    if summary['credit']['active_levers']:
        lines.append(f"   Available stress levers: {', '.join(summary['credit']['active_levers'])}")
    lines.append("")
    
    # Behavioral Risk
    lines.append(f"🔄 BEHAVIORAL RISK DRIVERS ({summary['behavioral']['count']} contracts):")
    if summary['behavioral']['active_levers']:
        lines.append(f"   Available stress levers: {', '.join(summary['behavioral']['active_levers'])}")
    lines.append("")
    
    # Segmentation
    if include_segmentation and summary['control']['segments']:
        lines.append("⚙️  SEGMENTATION DIMENSIONS:")
        for dim, values in summary['control']['segments'].items():
            lines.append(f"   {dim}: {', '.join(list(values.keys())[:5])}")
        lines.append("")
    
    return "\n".join(lines)


# =============================================================================
# INTEGRATION WITH load_from_riskpro
# =============================================================================

def load_from_riskpro_with_risk_attrs(
    model_id: Optional[str] = None,
    limit_contracts: Optional[int] = None,
    load_risk_factors_from_db_flag: bool = False,
    load_counterparties_flag: bool = True,
    load_contracts_flag: bool = True
):
    """
    Extended version of load_from_riskpro that includes risk attribute classification
    
    This is a wrapper around the existing load_from_riskpro that adds
    risk attribute enrichment as a post-processing step.
    
    Args:
        Same as load_from_riskpro
        
    Returns:
        (risk_factors, counterparties, contracts)
        where contracts are enriched with risk_attributes
        
    Usage:
        # Drop-in replacement for load_from_riskpro
        rf, cp, contracts = load_from_riskpro_with_risk_attrs(model_id="2", limit_contracts=1000)
        
        # Now contracts have risk_attributes
        for contract in contracts:
            market_levers = contract.risk_attributes.market.get_stress_levers()
            credit_levers = contract.risk_attributes.credit.get_stress_levers()
    """
    try:
        from load_alm_data import load_from_riskpro
    except ImportError:
        raise ImportError("load_alm_data module not found")
    
    # Load data using existing function
    risk_factors, counterparties, contracts = load_from_riskpro(
        model_id=model_id,
        limit_contracts=limit_contracts,
        load_risk_factors_from_db_flag=load_risk_factors_from_db_flag,
        load_counterparties_flag=load_counterparties_flag,
        load_contracts_flag=load_contracts_flag
    )
    
    # Enrich with risk attributes
    if contracts:
        contracts = enrich_contracts_with_risk_attributes(contracts, counterparties)
    
    return risk_factors, counterparties, contracts


# =============================================================================
# CONVENIENCE FUNCTIONS FOR SCENARIO GENERATION
# =============================================================================

def prepare_scenario_context(contracts: List) -> dict:
    """
    Prepare all risk attribute context needed for scenario generation
    
    Returns comprehensive dictionary with:
    - Contracts grouped by risk category
    - Available stress levers by category
    - Segmentation breakdown
    - LLM-ready context string
    
    Args:
        contracts: List of enriched contracts
        
    Returns:
        Dictionary with scenario generation context
    """
    if not contracts or not hasattr(contracts[0], 'risk_attributes'):
        return {
            'contracts_total': len(contracts),
            'enriched': False,
            'message': 'Contracts not enriched with risk attributes'
        }
    
    summary = summarize_risk_attributes(contracts)
    
    context = {
        'contracts_total': len(contracts),
        'enriched': True,
        
        # Market risk
        'market': {
            'count': summary['market']['count'],
            'stress_levers': summary['market']['active_levers'],
            'contracts': get_contracts_with_stress_lever(contracts, 'market', summary['market']['active_levers'][0] if summary['market']['active_levers'] else 'ir_rate')
        },
        
        # Credit risk
        'credit': {
            'count': summary['credit']['count'],
            'stress_levers': summary['credit']['active_levers'],
            'contracts': get_contracts_with_stress_lever(contracts, 'credit', summary['credit']['active_levers'][0] if summary['credit']['active_levers'] else 'pd')
        },
        
        # Behavioral risk
        'behavioral': {
            'count': summary['behavioral']['count'],
            'stress_levers': summary['behavioral']['active_levers'],
        },
        
        # Segmentation
        'segmentation': summary['control']['segments'],
        
        # LLM context
        'llm_context': extract_stress_context_for_llm(contracts)
    }
    
    return context
