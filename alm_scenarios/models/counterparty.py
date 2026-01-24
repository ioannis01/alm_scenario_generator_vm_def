"""
Counterparty Model

Defines counterparty entities with credit risk attributes.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Counterparty:
    """Counterparty / obligor with credit risk attributes"""
    counterparty_id: str
    name: str
    rating: str  # e.g., "AAA", "A", "BBB", "BB", etc.
    pd: float  # Probability of default (annualized, as decimal, e.g., 0.02 = 2%)
    recovery_rate: float  # Recovery rate (as decimal, e.g., 0.40 = 40%)
    sector: Optional[str] = None
    country: Optional[str] = None
    
    @property
    def lgd(self) -> float:
        """Loss Given Default = 1 - Recovery Rate"""
        return 1.0 - self.recovery_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "counterparty_id": self.counterparty_id,
            "name": self.name,
            "rating": self.rating,
            "pd": self.pd,
            "recovery_rate": self.recovery_rate,
            "lgd": self.lgd,
            "sector": self.sector,
            "country": self.country
        }
