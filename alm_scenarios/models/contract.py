"""
Contract Model

Defines financial contracts and positions in the ALM portfolio.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, Dict, Any
from enum import Enum


class ContractType(Enum):
    """Enumeration of contract types"""
    LOAN = "loan"
    DEPOSIT = "deposit"
    BOND = "bond"
    SWAP = "swap"
    FORWARD = "forward"
    OPTION = "option"
    FACILITY = "facility"


@dataclass
class Contract:
    """Financial contract / position in the ALM portfolio"""
    contract_id: str
    contract_type: ContractType
    currency: str
    notional: float
    maturity_date: date
    
    # Links to risk factors
    linked_yield_curve: Optional[str] = None
    linked_spread_curve: Optional[str] = None
    linked_fx_pair: Optional[str] = None
    linked_equity: Optional[str] = None
    
    # Link to counterparty
    counterparty_id: Optional[str] = None
    
    # Additional attributes
    is_asset: bool = True  # True for assets, False for liabilities
    rate: Optional[float] = None  # Fixed rate if applicable (%)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "contract_id": self.contract_id,
            "contract_type": self.contract_type.value,
            "currency": self.currency,
            "notional": self.notional,
            "maturity_date": self.maturity_date.isoformat(),
            "linked_yield_curve": self.linked_yield_curve,
            "linked_spread_curve": self.linked_spread_curve,
            "linked_fx_pair": self.linked_fx_pair,
            "linked_equity": self.linked_equity,
            "counterparty_id": self.counterparty_id,
            "is_asset": self.is_asset,
            "rate": self.rate
        }
