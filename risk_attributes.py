# risk_attributes.py
"""
Enhanced Risk Attribute Models for ALM Scenario Generation

This module defines the four logical categories of risk-related attributes
from RiskPro/OneSumX that drive stress testing:

1. Market Risk-Linked Attributes
2. Credit Risk-Linked Attributes  
3. Behavioral Risk-Linked Attributes
4. Cross-Risk / Stress-Testing Control Attributes

These extend beyond traditional "risk factors" to capture the full spectrum
of stress testing inputs available in RiskPro.

Author: ALM Risk Engineering Team
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


# ============================================================================
# CATEGORY 1: MARKET RISK-LINKED ATTRIBUTES
# ============================================================================

class MarketRiskCategory(Enum):
    """Sub-categories of market risk attributes"""
    CURRENCY_FX = "currency_fx"
    YIELD_DISCOUNT_IR = "yield_discount_ir"
    SPREADS = "spreads"
    EQUITY_COMMODITY = "equity_commodity"
    VOLATILITY = "volatility"
    INFLATION = "inflation"
    VALUATION_MTM = "valuation_mtm"


@dataclass
class MarketRiskAttribute:
    """
    Market risk-linked attributes that serve as direct stress levers.
    
    Purpose:
    - Direct market risk drivers
    - Map to market risk factors, curves, surfaces
    - First-class stress levers for IR, FX, spreads, equity, volatility
    
    Stress Usage Examples:
    - IR shocks (+200 bps)
    - Spread widening (+50 bps)
    - FX devaluation (-20%)
    - Equity crash (-30%)
    - Volatility spike (+50%)
    - Inflation shock (+3%)
    """
    
    # Identity
    attribute_name: str
    category: MarketRiskCategory
    contract_id: str
    
    # Currency & FX
    currency_def: Optional[str] = None
    dom_currency_def: Optional[str] = None
    for_currency_def: Optional[str] = None
    contracted_fx_rate: Optional[float] = None
    fx_rate_at_cdd: Optional[float] = None
    
    # Yield / Discount / IR
    pricing_market_object: Optional[str] = None
    disc_market_object: Optional[str] = None
    discount_rate: Optional[float] = None
    current_nominal_int_rate: Optional[float] = None
    next_repricing_rate: Optional[float] = None
    const_effect_yield: Optional[float] = None
    
    # Spreads
    dscng_spread: Optional[float] = None
    contract_spread: Optional[float] = None
    observed_credit_spread: Optional[float] = None
    credit_spread_curve_def: Optional[str] = None
    spread_curve_def: Optional[str] = None
    
    # Equity / Commodity
    stock_index_def: Optional[str] = None
    commodity_index_def: Optional[str] = None
    commodity_pricing_market_obj: Optional[str] = None
    dividend_rate: Optional[float] = None
    beta_at_mvd: Optional[float] = None
    
    # Volatility
    volatility_surface_def: Optional[str] = None
    volatility_at_mvd: Optional[float] = None
    fut_volatility_at_mvd: Optional[float] = None
    
    # Inflation
    csm_price_index_def: Optional[str] = None
    original_cpi: Optional[float] = None
    indexation_lag_count: Optional[int] = None
    indexation_lag_unit: Optional[str] = None
    
    # Valuation / MTM
    market_value_observed: Optional[float] = None
    quoted_price_at_mvd: Optional[float] = None
    fut_quoted_price_at_mvd: Optional[float] = None
    price_at_td: Optional[float] = None
    price_at_cdd: Optional[float] = None
    future_price: Optional[float] = None
    underlying_mvo: Optional[float] = None
    
    # Extended attributes for additional fields
    extended: Dict[str, Any] = field(default_factory=dict)
    
    def get_stress_levers(self) -> Dict[str, Any]:
        """
        Extract the primary stress levers from this attribute set.
        
        Returns:
            Dictionary of stress lever names to current values
        """
        levers = {}
        
        # IR levers
        if self.current_nominal_int_rate is not None:
            levers['interest_rate'] = self.current_nominal_int_rate
        if self.discount_rate is not None:
            levers['discount_rate'] = self.discount_rate
            
        # Spread levers
        if self.contract_spread is not None:
            levers['contract_spread'] = self.contract_spread
        if self.observed_credit_spread is not None:
            levers['credit_spread'] = self.observed_credit_spread
            
        # FX levers
        if self.contracted_fx_rate is not None:
            levers['fx_rate'] = self.contracted_fx_rate
            
        # Equity levers
        if self.market_value_observed is not None:
            levers['market_value'] = self.market_value_observed
            
        # Volatility levers
        if self.volatility_at_mvd is not None:
            levers['volatility'] = self.volatility_at_mvd
            
        return levers


# ============================================================================
# CATEGORY 2: CREDIT RISK-LINKED ATTRIBUTES
# ============================================================================

class CreditRiskCategory(Enum):
    """Sub-categories of credit risk attributes"""
    COUNTERPARTY_REF = "counterparty_ref"
    RATINGS_PD = "ratings_pd"
    RECOVERY_LGD = "recovery_lgd"
    DEFAULT_IMPAIRMENT = "default_impairment"
    NETTING_MITIGATION = "netting_mitigation"


@dataclass
class CreditRiskAttribute:
    """
    Credit risk-linked attributes for default, recovery, IFRS 9, Basel stress.
    
    Purpose:
    - Default, recovery, counterparty credit risk
    - IFRS 9 ECL calculations
    - Basel stress testing
    
    Stress Usage Examples:
    - PD up (+50 bps, +100 bps, +200 bps)
    - Rating migration (downgrade by 1, 2, 3 notches)
    - LGD stress (+10%, +20%)
    - Collateral haircut increase
    - Guarantor failure scenarios
    """
    
    # Identity
    attribute_name: str
    category: CreditRiskCategory
    contract_id: str
    
    # Counterparty & reference entities
    counterparty_ssrn: Optional[str] = None
    reference_entity_ssrn: Optional[str] = None
    issuer_ssrn: Optional[str] = None
    credit_line_ssrn: Optional[str] = None
    
    # Ratings & PD
    rating_scale: Optional[str] = None
    rating_class: Optional[str] = None
    default_probability: Optional[float] = None
    pd_amortization_date: Optional[datetime] = None
    
    # Recovery / LGD / Collateral
    gross_recovery_rate: Optional[float] = None
    net_recovery_rate: Optional[float] = None
    haircut: Optional[float] = None
    cr_cad_collateral_type: Optional[str] = None
    nominal_value_of_guarantee: Optional[float] = None
    
    # Default & impairment
    non_performing_date: Optional[datetime] = None
    write_off_amount: Optional[float] = None
    write_off_amount_ifrs: Optional[float] = None
    credit_risk_provision: Optional[float] = None
    credit_risk_provision_ifrs: Optional[float] = None
    
    # Netting & mitigation
    close_out_netting: Optional[bool] = None
    on_balance_sheet_netting: Optional[bool] = None
    cr_cad_conversion_factor: Optional[float] = None
    
    # Extended attributes
    extended: Dict[str, Any] = field(default_factory=dict)
    
    def get_stress_levers(self) -> Dict[str, Any]:
        """
        Extract the primary stress levers from this attribute set.
        
        Returns:
            Dictionary of stress lever names to current values
        """
        levers = {}
        
        # PD levers
        if self.default_probability is not None:
            levers['default_probability'] = self.default_probability
            
        # LGD levers (derived from recovery)
        if self.gross_recovery_rate is not None:
            levers['lgd'] = 1.0 - self.gross_recovery_rate
        if self.net_recovery_rate is not None:
            levers['lgd_net'] = 1.0 - self.net_recovery_rate
            
        # Collateral levers
        if self.haircut is not None:
            levers['collateral_haircut'] = self.haircut
            
        # Rating levers
        if self.rating_class is not None:
            levers['rating'] = self.rating_class
            
        return levers


# ============================================================================
# CATEGORY 3: BEHAVIORAL RISK-LINKED ATTRIBUTES
# ============================================================================

class BehavioralRiskCategory(Enum):
    """Sub-categories of behavioral risk attributes"""
    OPTIONALITY = "optionality"
    PREPAYMENT_AMORTIZATION = "prepayment_amortization"
    BEHAVIOR_CYCLES = "behavior_cycles"


@dataclass
class BehavioralRiskAttribute:
    """
    Behavioral risk-linked attributes that drive cash-flow uncertainty.
    
    Purpose:
    - Cash-flow uncertainty
    - Client behavioral assumptions
    - NOT direct market shocks
    
    Stress Usage Examples:
    - Higher prepayments (+50%, +100%)
    - Lower repricing pass-through (-20%, -50%)
    - Payment delays (30, 60, 90 days)
    - Option exercise waves (mass redemption, mass draw-down)
    """
    
    # Identity
    attribute_name: str
    category: BehavioralRiskCategory
    contract_id: str
    
    # Optionality
    option_type_id: Optional[str] = None
    option_exercise_begin_date: Optional[datetime] = None
    option_exercise_end_date: Optional[datetime] = None
    option_strike_call: Optional[float] = None
    option_strike_put: Optional[float] = None
    
    # Prepayment / amortization / renegotiation
    ref_amortization_type_id: Optional[str] = None
    amortization_date: Optional[datetime] = None
    ref_grace_type_id: Optional[str] = None
    renegotiation_id: Optional[str] = None
    
    # Behavior cycles (pattern fields)
    ip_fields: Dict[str, Any] = field(default_factory=dict)  # Interest payment cycles
    fix_fields: Dict[str, Any] = field(default_factory=dict)  # Fixing cycles
    var_fields: Dict[str, Any] = field(default_factory=dict)  # Variable rate cycles
    inc_fields: Dict[str, Any] = field(default_factory=dict)  # Increase cycles
    dec_fields: Dict[str, Any] = field(default_factory=dict)  # Decrease cycles
    rp_fields: Dict[str, Any] = field(default_factory=dict)   # Repricing cycles
    pre_fixing_period: Optional[int] = None
    fixing_days_count: Optional[int] = None
    
    # Extended attributes
    extended: Dict[str, Any] = field(default_factory=dict)
    
    def get_stress_levers(self) -> Dict[str, Any]:
        """
        Extract the primary stress levers from this attribute set.
        
        Returns:
            Dictionary of stress lever names to current values
        """
        levers = {}
        
        # Prepayment levers
        if self.ref_amortization_type_id is not None:
            levers['amortization_type'] = self.ref_amortization_type_id
            
        # Option levers
        if self.option_type_id is not None:
            levers['option_type'] = self.option_type_id
        if self.option_strike_call is not None:
            levers['call_strike'] = self.option_strike_call
        if self.option_strike_put is not None:
            levers['put_strike'] = self.option_strike_put
            
        # Repricing levers
        if self.rp_fields:
            levers['repricing_pattern'] = self.rp_fields
            
        return levers


# ============================================================================
# CATEGORY 4: CROSS-RISK / STRESS-TESTING CONTROL ATTRIBUTES
# ============================================================================

class ControlAttributeCategory(Enum):
    """Sub-categories of control attributes"""
    SCENARIO_CONTROL = "scenario_control"
    LIQUIDITY_FUNDING = "liquidity_funding"
    SEGMENTATION = "segmentation"
    INSURANCE_STRESS = "insurance_stress"


@dataclass
class ControlAttribute:
    """
    Cross-risk and stress-testing control attributes.
    
    Purpose:
    - Scenario logic and routing
    - Model switches and configuration
    - Segmentation for targeted stress
    - Amplification factors
    
    Usage Examples:
    - Route contracts to specific scenarios by MODEL_ID
    - Apply liquidity stress by segment
    - Target industry-specific shocks
    - Insurance catastrophe modeling
    """
    
    # Identity
    attribute_name: str
    category: ControlAttributeCategory
    contract_id: str
    
    # Scenario control
    model_id: Optional[str] = None
    ref_simulation_type_id: Optional[str] = None
    ref_reference_risk_factor_id: Optional[str] = None
    
    # Liquidity & funding
    ref_liquidity_level_type_id: Optional[str] = None
    ftp_liquidity_spread: Optional[float] = None
    ftp_credit_risk_spread: Optional[float] = None
    limit_amount: Optional[float] = None
    margin_required: Optional[float] = None
    
    # Segmentation
    product_type: Optional[str] = None
    segment: Optional[str] = None
    main_industry: Optional[str] = None
    national_market: Optional[str] = None
    legal_entity: Optional[str] = None
    
    # Insurance stress
    attritional_ins_rf_def: Optional[str] = None
    catastrophic_ins_rf_def: Optional[str] = None
    large_ins_rf_def: Optional[str] = None
    prior_claims: Optional[float] = None
    
    # Extended attributes
    extended: Dict[str, Any] = field(default_factory=dict)
    
    def get_segmentation_keys(self) -> Dict[str, str]:
        """
        Extract segmentation keys for targeted stress scenarios.
        
        Returns:
            Dictionary of segmentation dimensions
        """
        keys = {}
        
        if self.product_type:
            keys['product_type'] = self.product_type
        if self.segment:
            keys['segment'] = self.segment
        if self.main_industry:
            keys['industry'] = self.main_industry
        if self.national_market:
            keys['market'] = self.national_market
        if self.legal_entity:
            keys['legal_entity'] = self.legal_entity
            
        return keys


# ============================================================================
# UNIFIED RISK ATTRIBUTE CONTAINER
# ============================================================================

@dataclass
class RiskAttributeSet:
    """
    Unified container for all risk attributes associated with a contract.
    
    This structure provides clear separation of concerns and enables
    scenario generation logic to selectively apply stresses based on
    risk category.
    """
    
    contract_id: str
    
    # Four logical categories
    market_risk: Optional[MarketRiskAttribute] = None
    credit_risk: Optional[CreditRiskAttribute] = None
    behavioral_risk: Optional[BehavioralRiskAttribute] = None
    control: Optional[ControlAttribute] = None
    
    def has_market_risk_attributes(self) -> bool:
        """Check if market risk attributes are available"""
        return self.market_risk is not None
    
    def has_credit_risk_attributes(self) -> bool:
        """Check if credit risk attributes are available"""
        return self.credit_risk is not None
    
    def has_behavioral_risk_attributes(self) -> bool:
        """Check if behavioral risk attributes are available"""
        return self.behavioral_risk is not None
    
    def has_control_attributes(self) -> bool:
        """Check if control attributes are available"""
        return self.control is not None
    
    def get_all_stress_levers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all stress levers organized by category.
        
        Returns:
            Dictionary with keys: 'market', 'credit', 'behavioral'
            Each containing the stress levers for that category
        """
        levers = {}
        
        if self.market_risk:
            levers['market'] = self.market_risk.get_stress_levers()
        
        if self.credit_risk:
            levers['credit'] = self.credit_risk.get_stress_levers()
        
        if self.behavioral_risk:
            levers['behavioral'] = self.behavioral_risk.get_stress_levers()
        
        return levers
    
    def get_segmentation(self) -> Dict[str, str]:
        """Get segmentation keys for targeted stress scenarios"""
        if self.control:
            return self.control.get_segmentation_keys()
        return {}


# ============================================================================
# HELPER FUNCTIONS FOR SCENARIO GENERATION
# ============================================================================

def extract_market_stress_targets(
    risk_attribute_sets: List[RiskAttributeSet],
    stress_category: MarketRiskCategory
) -> List[Dict[str, Any]]:
    """
    Extract contracts with specific market risk category for targeted stress.
    
    Args:
        risk_attribute_sets: List of risk attribute sets
        stress_category: Which market risk category to target
        
    Returns:
        List of dictionaries with contract_id and stress levers
    """
    targets = []
    
    for attr_set in risk_attribute_sets:
        if attr_set.has_market_risk_attributes():
            if attr_set.market_risk.category == stress_category:
                targets.append({
                    'contract_id': attr_set.contract_id,
                    'levers': attr_set.market_risk.get_stress_levers(),
                    'segmentation': attr_set.get_segmentation()
                })
    
    return targets


def extract_credit_stress_targets(
    risk_attribute_sets: List[RiskAttributeSet],
    min_pd: Optional[float] = None,
    rating_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract contracts with credit risk attributes for targeted stress.
    
    Args:
        risk_attribute_sets: List of risk attribute sets
        min_pd: Optional minimum PD threshold
        rating_filter: Optional rating class filter
        
    Returns:
        List of dictionaries with contract_id and stress levers
    """
    targets = []
    
    for attr_set in risk_attribute_sets:
        if attr_set.has_credit_risk_attributes():
            cr = attr_set.credit_risk
            
            # Apply filters
            if min_pd and (cr.default_probability or 0) < min_pd:
                continue
            if rating_filter and cr.rating_class != rating_filter:
                continue
            
            targets.append({
                'contract_id': attr_set.contract_id,
                'levers': cr.get_stress_levers(),
                'counterparty': cr.counterparty_ssrn,
                'segmentation': attr_set.get_segmentation()
            })
    
    return targets


def extract_behavioral_stress_targets(
    risk_attribute_sets: List[RiskAttributeSet],
    has_optionality: bool = False
) -> List[Dict[str, Any]]:
    """
    Extract contracts with behavioral risk attributes for targeted stress.
    
    Args:
        risk_attribute_sets: List of risk attribute sets
        has_optionality: Filter for contracts with options
        
    Returns:
        List of dictionaries with contract_id and stress levers
    """
    targets = []
    
    for attr_set in risk_attribute_sets:
        if attr_set.has_behavioral_risk_attributes():
            br = attr_set.behavioral_risk
            
            # Apply filters
            if has_optionality and not br.option_type_id:
                continue
            
            targets.append({
                'contract_id': attr_set.contract_id,
                'levers': br.get_stress_levers(),
                'segmentation': attr_set.get_segmentation()
            })
    
    return targets


def group_by_segment(
    risk_attribute_sets: List[RiskAttributeSet],
    segment_key: str = 'product_type'
) -> Dict[str, List[RiskAttributeSet]]:
    """
    Group contracts by segmentation dimension for targeted stress.
    
    Args:
        risk_attribute_sets: List of risk attribute sets
        segment_key: Which segmentation dimension to use
        
    Returns:
        Dictionary mapping segment values to lists of attribute sets
    """
    groups = {}
    
    for attr_set in risk_attribute_sets:
        seg = attr_set.get_segmentation()
        key_value = seg.get(segment_key, 'unknown')
        
        if key_value not in groups:
            groups[key_value] = []
        
        groups[key_value].append(attr_set)
    
    return groups
