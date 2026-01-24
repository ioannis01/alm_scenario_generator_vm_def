"""
ALM Scenario Generator

A production-ready framework for generating stress and stochastic scenarios
using local Llama 3 models for Asset-Liability Management (ALM) systems.
"""

__version__ = "1.0.0"
__author__ = "ALM Risk Engineering Team"

from .models import (
    RiskFactor, RiskFactorType, ShockType,
    YieldCurve, SpreadCurve, FXRate, EquityIndex, MacroFactor,
    Counterparty,
    Contract, ContractType,
    Scenario, Shock
)

from .llm import LlamaClient, PromptBuilder
from .parsers import ScenarioParser
from .generators import ALMScenarioGenerator
from .utils import create_sample_universe

__all__ = [
    # Models
    'RiskFactor', 'RiskFactorType', 'ShockType',
    'YieldCurve', 'SpreadCurve', 'FXRate', 'EquityIndex', 'MacroFactor',
    'Counterparty',
    'Contract', 'ContractType',
    'Scenario', 'Shock',
    # LLM
    'LlamaClient', 'PromptBuilder',
    # Parsers
    'ScenarioParser',
    # Generators
    'ALMScenarioGenerator',
    # Utils
    'create_sample_universe',
]
