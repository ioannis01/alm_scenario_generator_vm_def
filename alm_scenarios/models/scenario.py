"""
Scenario Models

Defines scenarios and shocks for stress testing.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Shock:
    """Individual shock to a risk factor"""
    factor_type: str
    factor_id: str
    shock_type: str
    value: float
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "factor_type": self.factor_type,
            "factor_id": self.factor_id,
            "shock_type": self.shock_type,
            "value": self.value,
            "description": self.description
        }


@dataclass
class Scenario:
    """Stress or stochastic scenario"""
    name: str
    description: str
    shocks: List[Shock] = field(default_factory=list)
    scenario_type: str = "stress"  # "stress" or "stochastic"
    probability: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "scenario_type": self.scenario_type,
            "probability": self.probability,
            "shocks": [s.to_dict() for s in self.shocks]
        }
