"""
Risk Factor Models

This module defines all risk factor types used in the ALM system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from abc import ABC, abstractmethod


class RiskFactorType(Enum):
    """Enumeration of risk factor types"""
    YIELD_CURVE = "yield_curve"
    SPREAD_CURVE = "spread_curve"
    FX_RATE = "fx_rate"
    EQUITY_PRICE = "equity_price"
    EQUITY_INDEX = "equity_index"
    MACRO_FACTOR = "macro_factor"


class ShockType(Enum):
    """Enumeration of shock types that can be applied to risk factors"""
    PARALLEL_SHIFT_BPS = "parallel_shift_bps"
    PARALLEL_SHIFT_PCT = "parallel_shift_pct"
    TWIST = "twist"
    BUTTERFLY = "butterfly"
    MULTIPLICATIVE = "multiplicative"
    ABSOLUTE_CHANGE = "absolute_change"


@dataclass
class RiskFactor(ABC):
    """Base class for all risk factors"""
    factor_id: str
    factor_type: RiskFactorType = field(init=False)
    currency: Optional[str] = field(default=None)
    description: str = field(default="")
    current_value: Optional[float] = field(default=None)
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        pass


@dataclass
class YieldCurve(RiskFactor):
    """Yield curve risk factor (term structure of interest rates)"""
    tenors: List[str] = field(default_factory=list)
    rates: List[float] = field(default_factory=list)
    
    def __post_init__(self):
        self.factor_type = RiskFactorType.YIELD_CURVE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_id": self.factor_id,
            "factor_type": self.factor_type.value,
            "currency": self.currency,
            "description": self.description,
            "tenors": self.tenors,
            "rates": self.rates,
            "avg_rate": sum(self.rates) / len(self.rates) if self.rates else 0
        }


@dataclass
class SpreadCurve(RiskFactor):
    """Credit or liquidity spread curve"""
    rating: Optional[str] = field(default=None)
    spread_type: str = field(default="credit")
    tenors: List[str] = field(default_factory=list)
    spreads: List[float] = field(default_factory=list)
    
    def __post_init__(self):
        self.factor_type = RiskFactorType.SPREAD_CURVE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_id": self.factor_id,
            "factor_type": self.factor_type.value,
            "currency": self.currency,
            "rating": self.rating,
            "spread_type": self.spread_type,
            "tenors": self.tenors,
            "spreads": self.spreads,
            "avg_spread_bps": sum(self.spreads) / len(self.spreads) if self.spreads else 0
        }


@dataclass
class FXRate(RiskFactor):
    """Foreign exchange rate"""
    currency_pair: str = field(default="")
    base_currency: str = field(default="")
    quote_currency: str = field(default="")
    spot_rate: float = field(default=1.0)
    
    def __post_init__(self):
        self.factor_type = RiskFactorType.FX_RATE
        self.current_value = self.spot_rate
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_id": self.factor_id,
            "factor_type": self.factor_type.value,
            "currency_pair": self.currency_pair,
            "base_currency": self.base_currency,
            "quote_currency": self.quote_currency,
            "spot_rate": self.spot_rate
        }


@dataclass
class EquityIndex(RiskFactor):
    """Equity index level"""
    index_name: str = field(default="")
    current_level: float = field(default=0.0)
    
    def __post_init__(self):
        self.factor_type = RiskFactorType.EQUITY_INDEX
        self.current_value = self.current_level
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_id": self.factor_id,
            "factor_type": self.factor_type.value,
            "index_name": self.index_name,
            "current_level": self.current_level
        }


@dataclass
class MacroFactor(RiskFactor):
    """Macroeconomic factor (GDP, inflation, unemployment, etc.)"""
    macro_type: str = field(default="")
    unit: str = field(default="%")
    
    def __post_init__(self):
        self.factor_type = RiskFactorType.MACRO_FACTOR
        if self.current_value is None:
            self.current_value = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_id": self.factor_id,
            "factor_type": self.factor_type.value,
            "macro_type": self.macro_type,
            "current_value": self.current_value,
            "unit": self.unit
        }
