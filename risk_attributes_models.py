"""
RiskPro Risk Attribute Models - Extended Classification
Supports Market, Credit, Behavioral, and Control Risk Attributes

Author: ALM Risk Engineering Team
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


# ============================================================================
# RISK ATTRIBUTE CATEGORIES (RiskPro/OneSumX Aligned)
# ============================================================================

class RiskAttributeCategory(Enum):
    """
    Four logical categories of risk attributes per RiskPro/OneSumX semantics
    """
    MARKET_RISK = "market_risk"           # Market risk drivers (IR, FX, spreads, equity, vol)
    CREDIT_RISK = "credit_risk"           # Default, recovery, PD, LGD, collateral
    BEHAVIORAL_RISK = "behavioral_risk"   # Prepayment, optionality, repricing behavior
    CONTROL = "control"                   # Scenario control, segmentation, model switches


# ============================================================================
# 1. MARKET RISK-LINKED ATTRIBUTES
# ============================================================================

@dataclass
class MarketRiskAttributes:
    """
    Market risk drivers - direct stress levers for market shocks
    
    Purpose:
    - IR shocks, spread widening, FX devaluation
    - Equity crash, volatility spike, inflation shock
    """
    
    # Currency & FX
    currency_def: Optional[str] = None
    dom_currency_def: Optional[str] = None
    for_currency_def: Optional[str] = None
    contracted_fx_rate: Optional[float] = None
    fx_rate_at_cdd: Optional[float] = None
    
    # Yield / Discount / Interest Rates
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
    
    # Valuation / Mark-to-Market
    market_value_observed: Optional[float] = None
    quoted_price_at_mvd: Optional[float] = None
    fut_quoted_price_at_mvd: Optional[float] = None
    price_at_td: Optional[float] = None
    price_at_cdd: Optional[float] = None
    future_price: Optional[float] = None
    underlying_mvo: Optional[float] = None
    
    # Extended attributes (catch-all for additional market risk fields)
    extended: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def category(self) -> RiskAttributeCategory:
        return RiskAttributeCategory.MARKET_RISK
    
    def get_stress_levers(self) -> Dict[str, Any]:
        """Extract active market risk stress levers"""
        levers = {}
        
        # Interest rate levers
        if self.current_nominal_int_rate is not None:
            levers['ir_rate'] = self.current_nominal_int_rate
        if self.pricing_market_object:
            levers['pricing_curve'] = self.pricing_market_object
            
        # Spread levers
        if self.observed_credit_spread is not None:
            levers['credit_spread'] = self.observed_credit_spread
        if self.dscng_spread is not None:
            levers['discount_spread'] = self.dscng_spread
            
        # FX levers
        if self.contracted_fx_rate is not None:
            levers['fx_rate'] = self.contracted_fx_rate
            
        # Equity levers
        if self.stock_index_def:
            levers['equity_index'] = self.stock_index_def
            
        # Volatility levers
        if self.volatility_at_mvd is not None:
            levers['volatility'] = self.volatility_at_mvd
            
        return levers


# ============================================================================
# 2. CREDIT RISK-LINKED ATTRIBUTES
# ============================================================================

@dataclass
class CreditRiskAttributes:
    """
    Credit risk drivers - default, recovery, counterparty, IFRS 9, Basel stress
    
    Purpose:
    - PD up, rating migration, LGD stress
    - Collateral haircut, guarantor failure
    """
    
    # Counterparty & Reference Entities
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
    
    # Default & Impairment
    non_performing_date: Optional[datetime] = None
    write_off_amount: Optional[float] = None
    write_off_amount_ifrs: Optional[float] = None
    credit_risk_provision: Optional[float] = None
    credit_risk_provision_ifrs: Optional[float] = None
    
    # Netting & Mitigation
    close_out_netting: Optional[bool] = None
    on_balance_sheet_netting: Optional[bool] = None
    cr_cad_conversion_factor: Optional[float] = None
    
    # Extended attributes
    extended: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def category(self) -> RiskAttributeCategory:
        return RiskAttributeCategory.CREDIT_RISK
    
    def get_stress_levers(self) -> Dict[str, Any]:
        """Extract active credit risk stress levers"""
        levers = {}
        
        # PD lever
        if self.default_probability is not None:
            levers['pd'] = self.default_probability
            
        # Recovery/LGD levers
        if self.gross_recovery_rate is not None:
            levers['recovery_rate'] = self.gross_recovery_rate
        if self.net_recovery_rate is not None:
            levers['net_recovery'] = self.net_recovery_rate
            
        # Collateral levers
        if self.haircut is not None:
            levers['collateral_haircut'] = self.haircut
            
        # Rating lever
        if self.rating_class:
            levers['rating'] = self.rating_class
            
        return levers


# ============================================================================
# 3. BEHAVIORAL RISK-LINKED ATTRIBUTES
# ============================================================================

@dataclass
class BehavioralRiskAttributes:
    """
    Behavioral risk drivers - cash flow uncertainty, not direct market shocks
    
    Purpose:
    - Higher prepayments, lower repricing pass-through
    - Payment delays, option exercise waves
    """
    
    # Optionality
    option_type_id: Optional[str] = None
    option_exercise_begin_date: Optional[datetime] = None
    option_exercise_end_date: Optional[datetime] = None
    option_strike_call: Optional[float] = None
    option_strike_put: Optional[float] = None
    
    # Prepayment / Amortization / Renegotiation
    ref_amortization_type_id: Optional[str] = None
    amortization_date: Optional[datetime] = None
    ref_grace_type_id: Optional[str] = None
    renegotiation_id: Optional[str] = None
    
    # Behavior Cycles (IP, FIX, VAR, INC, DEC, RP patterns)
    ip_cycles: Dict[str, Any] = field(default_factory=dict)      # Interest payment cycles
    fix_cycles: Dict[str, Any] = field(default_factory=dict)     # Fixed rate cycles
    var_cycles: Dict[str, Any] = field(default_factory=dict)     # Variable rate cycles
    inc_cycles: Dict[str, Any] = field(default_factory=dict)     # Increase cycles
    dec_cycles: Dict[str, Any] = field(default_factory=dict)     # Decrease cycles
    rp_cycles: Dict[str, Any] = field(default_factory=dict)      # Repricing cycles
    
    pre_fixing_period: Optional[int] = None
    fixing_days_count: Optional[int] = None
    
    # Extended attributes
    extended: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def category(self) -> RiskAttributeCategory:
        return RiskAttributeCategory.BEHAVIORAL_RISK
    
    def get_stress_levers(self) -> Dict[str, Any]:
        """Extract active behavioral risk stress levers"""
        levers = {}
        
        # Optionality levers
        if self.option_type_id:
            levers['option_type'] = self.option_type_id
        if self.option_strike_call is not None:
            levers['call_strike'] = self.option_strike_call
            
        # Amortization levers
        if self.ref_amortization_type_id:
            levers['amortization_type'] = self.ref_amortization_type_id
            
        # Behavioral cycle levers
        if self.rp_cycles:
            levers['repricing_cycles'] = self.rp_cycles
            
        return levers


# ============================================================================
# 4. CROSS-RISK / STRESS-TESTING CONTROL ATTRIBUTES
# ============================================================================

@dataclass
class ControlAttributes:
    """
    Scenario control, model switches, segmentation, amplification factors
    
    Purpose:
    - Scenario logic, model switches, segmentation
    - Amplification factors
    """
    
    # Scenario Control
    model_id: Optional[str] = None
    ref_simulation_type_id: Optional[str] = None
    ref_reference_risk_factor_id: Optional[str] = None
    
    # Liquidity & Funding
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
    
    # Insurance Stress (if applicable)
    attritional_ins_rf_def: Optional[str] = None
    catastrophic_ins_rf_def: Optional[str] = None
    large_ins_rf_def: Optional[str] = None
    prior_claims: Optional[float] = None
    
    # Extended attributes
    extended: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def category(self) -> RiskAttributeCategory:
        return RiskAttributeCategory.CONTROL
    
    def get_segmentation(self) -> Dict[str, str]:
        """Extract segmentation dimensions"""
        seg = {}
        if self.product_type:
            seg['product_type'] = self.product_type
        if self.segment:
            seg['segment'] = self.segment
        if self.main_industry:
            seg['industry'] = self.main_industry
        if self.national_market:
            seg['market'] = self.national_market
        if self.legal_entity:
            seg['entity'] = self.legal_entity
        return seg


# ============================================================================
# UNIFIED RISK ATTRIBUTES CONTAINER
# ============================================================================

@dataclass
class RiskAttributes:
    """
    Unified container for all risk attribute categories
    
    This allows scenario generation logic to access:
    - market: Market risk drivers
    - credit: Credit risk drivers
    - behavioral: Behavioral risk drivers
    - control: Control and segmentation attributes
    """
    
    market: MarketRiskAttributes = field(default_factory=MarketRiskAttributes)
    credit: CreditRiskAttributes = field(default_factory=CreditRiskAttributes)
    behavioral: BehavioralRiskAttributes = field(default_factory=BehavioralRiskAttributes)
    control: ControlAttributes = field(default_factory=ControlAttributes)
    
    def get_all_stress_levers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all stress levers organized by category
        
        Returns:
            {
                'market': {...market levers...},
                'credit': {...credit levers...},
                'behavioral': {...behavioral levers...}
            }
        """
        return {
            'market': self.market.get_stress_levers(),
            'credit': self.credit.get_stress_levers(),
            'behavioral': self.behavioral.get_stress_levers()
        }
    
    def get_active_categories(self) -> List[RiskAttributeCategory]:
        """Return list of categories that have active attributes"""
        active = []
        
        if self.market.get_stress_levers():
            active.append(RiskAttributeCategory.MARKET_RISK)
        if self.credit.get_stress_levers():
            active.append(RiskAttributeCategory.CREDIT_RISK)
        if self.behavioral.get_stress_levers():
            active.append(RiskAttributeCategory.BEHAVIORAL_RISK)
        if self.control.get_segmentation():
            active.append(RiskAttributeCategory.CONTROL)
            
        return active
    
    def to_dict(self) -> Dict[str, Any]:
        """Export all attributes as nested dictionary"""
        return {
            'market': self.market.__dict__,
            'credit': self.credit.__dict__,
            'behavioral': self.behavioral.__dict__,
            'control': self.control.__dict__
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_risk_attributes_from_row(row: Dict[str, Any], column_map: Dict[str, str] = None) -> RiskAttributes:
    """
    Extract RiskAttributes from a database row
    
    Args:
        row: Dictionary mapping column names to values (from database query)
        column_map: Optional mapping of database column names to RiskPro field names
        
    Returns:
        RiskAttributes object with populated categories
        
    Example:
        row = {
            'CURRENCY_DEF': 'USD',
            'CURRENT_NOMINAL_INT_RATE': 0.045,
            'DEFAULT_PROBABILITY': 0.015,
            'PRODUCT_TYPE': 'LOAN'
        }
        attrs = extract_risk_attributes_from_row(row)
        # attrs.market.currency_def = 'USD'
        # attrs.market.current_nominal_int_rate = 0.045
        # attrs.credit.default_probability = 0.015
        # attrs.control.product_type = 'LOAN'
    """
    # Apply column mapping if provided
    if column_map:
        row = {column_map.get(k, k): v for k, v in row.items()}
    
    # Convert keys to lowercase for matching
    row_lower = {k.lower(): v for k, v in row.items()}
    
    # Initialize containers
    market = MarketRiskAttributes()
    credit = CreditRiskAttributes()
    behavioral = BehavioralRiskAttributes()
    control = ControlAttributes()
    
    # Map to Market Risk
    for field_name in market.__dataclass_fields__:
        if field_name in row_lower and field_name != 'extended':
            setattr(market, field_name, row_lower[field_name])
    
    # Map to Credit Risk
    for field_name in credit.__dataclass_fields__:
        if field_name in row_lower and field_name != 'extended':
            setattr(credit, field_name, row_lower[field_name])
    
    # Map to Behavioral Risk
    for field_name in behavioral.__dataclass_fields__:
        if field_name in row_lower and field_name not in ['extended', 'ip_cycles', 'fix_cycles', 'var_cycles', 'inc_cycles', 'dec_cycles', 'rp_cycles']:
            setattr(behavioral, field_name, row_lower[field_name])
    
    # Map behavioral cycles (special handling for IP_*, FIX_*, VAR_*, etc.)
    for key, value in row_lower.items():
        if key.startswith('ip_'):
            behavioral.ip_cycles[key] = value
        elif key.startswith('fix_'):
            behavioral.fix_cycles[key] = value
        elif key.startswith('var_'):
            behavioral.var_cycles[key] = value
        elif key.startswith('inc_'):
            behavioral.inc_cycles[key] = value
        elif key.startswith('dec_'):
            behavioral.dec_cycles[key] = value
        elif key.startswith('rp_'):
            behavioral.rp_cycles[key] = value
    
    # Map to Control
    for field_name in control.__dataclass_fields__:
        if field_name in row_lower and field_name != 'extended':
            setattr(control, field_name, row_lower[field_name])
    
    # Store unmapped fields in extended attributes
    mapped_fields = set()
    for obj in [market, credit, behavioral, control]:
        mapped_fields.update(obj.__dataclass_fields__.keys())
    
    for key, value in row_lower.items():
        if key not in mapped_fields and not key.startswith(('ip_', 'fix_', 'var_', 'inc_', 'dec_', 'rp_')):
            # Try to categorize unmapped field
            key_upper = key.upper()
            if any(x in key_upper for x in ['RATE', 'PRICE', 'SPREAD', 'CURRENCY', 'INDEX', 'VOLATILITY']):
                market.extended[key] = value
            elif any(x in key_upper for x in ['PD', 'LGD', 'DEFAULT', 'RECOVERY', 'CREDIT', 'RATING']):
                credit.extended[key] = value
            elif any(x in key_upper for x in ['OPTION', 'AMORTIZATION', 'PREPAY', 'FIXING']):
                behavioral.extended[key] = value
            else:
                control.extended[key] = value
    
    return RiskAttributes(
        market=market,
        credit=credit,
        behavioral=behavioral,
        control=control
    )


def summarize_risk_attributes(contracts: List[Any]) -> Dict[str, Any]:
    """
    Summarize risk attributes across a portfolio of contracts
    
    Args:
        contracts: List of Contract objects (each with risk_attributes: RiskAttributes)
        
    Returns:
        Summary statistics by category
    """
    summary = {
        'market': {'count': 0, 'active_levers': set()},
        'credit': {'count': 0, 'active_levers': set()},
        'behavioral': {'count': 0, 'active_levers': set()},
        'control': {'count': 0, 'segments': {}}
    }
    
    for contract in contracts:
        if not hasattr(contract, 'risk_attributes'):
            continue
            
        attrs = contract.risk_attributes
        
        # Market
        market_levers = attrs.market.get_stress_levers()
        if market_levers:
            summary['market']['count'] += 1
            summary['market']['active_levers'].update(market_levers.keys())
        
        # Credit
        credit_levers = attrs.credit.get_stress_levers()
        if credit_levers:
            summary['credit']['count'] += 1
            summary['credit']['active_levers'].update(credit_levers.keys())
        
        # Behavioral
        behavioral_levers = attrs.behavioral.get_stress_levers()
        if behavioral_levers:
            summary['behavioral']['count'] += 1
            summary['behavioral']['active_levers'].update(behavioral_levers.keys())
        
        # Control segmentation
        seg = attrs.control.get_segmentation()
        for dim, value in seg.items():
            if dim not in summary['control']['segments']:
                summary['control']['segments'][dim] = {}
            summary['control']['segments'][dim][value] = summary['control']['segments'][dim].get(value, 0) + 1
    
    # Convert sets to lists for JSON serialization
    summary['market']['active_levers'] = list(summary['market']['active_levers'])
    summary['credit']['active_levers'] = list(summary['credit']['active_levers'])
    summary['behavioral']['active_levers'] = list(summary['behavioral']['active_levers'])
    
    return summary
