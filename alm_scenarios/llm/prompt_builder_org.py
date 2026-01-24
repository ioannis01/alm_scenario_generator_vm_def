"""
Prompt Builder

Constructs prompts for the LLM to generate scenarios.
"""

from typing import List, Dict, Any, Literal
import json

from ..models import RiskFactor, Counterparty, Contract
from ..models import YieldCurve, SpreadCurve, FXRate, EquityIndex, MacroFactor
from ..models.risk_factors import RiskFactorType


class PromptBuilder:
    """Builds prompts for the LLM to generate scenarios"""
    
    @staticmethod
    def summarize_risk_factors(risk_factors: List[RiskFactor]) -> str:
        """Create a concise summary of current risk factors"""
        summary_lines = []
        
        # Group by type
        by_type: Dict[RiskFactorType, List[RiskFactor]] = {}
        for rf in risk_factors:
            if rf.factor_type not in by_type:
                by_type[rf.factor_type] = []
            by_type[rf.factor_type].append(rf)
        
        # Summarize each type
        for factor_type, factors in by_type.items():
            summary_lines.append(f"\n{factor_type.value.upper()}:")
            for factor in factors:
                factor_dict = factor.to_dict()
                if isinstance(factor, YieldCurve):
                    summary_lines.append(
                        f"  - {factor.factor_id} ({factor.currency}): "
                        f"avg rate = {factor_dict['avg_rate']:.2f}%, "
                        f"tenors = {len(factor.tenors)}"
                    )
                elif isinstance(factor, SpreadCurve):
                    summary_lines.append(
                        f"  - {factor.factor_id} ({factor.currency}, {factor.rating}): "
                        f"avg spread = {factor_dict['avg_spread_bps']:.0f} bps"
                    )
                elif isinstance(factor, FXRate):
                    summary_lines.append(
                        f"  - {factor.factor_id}: {factor.spot_rate:.4f}"
                    )
                elif isinstance(factor, EquityIndex):
                    summary_lines.append(
                        f"  - {factor.factor_id}: level = {factor.current_level:.2f}"
                    )
                elif isinstance(factor, MacroFactor):
                    summary_lines.append(
                        f"  - {factor.factor_id} ({factor.macro_type}): "
                        f"{factor.current_value:.2f}{factor.unit}"
                    )
        
        return "\n".join(summary_lines)
    
    @staticmethod
    def summarize_counterparties(counterparties: List[Counterparty]) -> str:
        """Create a concise summary of counterparties"""
        summary_lines = ["\nCOUNTERPARTIES:"]
        
        for cp in counterparties:
            summary_lines.append(
                f"  - {cp.counterparty_id} ({cp.name}): "
                f"Rating={cp.rating}, PD={cp.pd*100:.2f}%, "
                f"Recovery={cp.recovery_rate*100:.0f}%"
            )
        
        return "\n".join(summary_lines)
    
    @staticmethod
    def summarize_portfolio(contracts: List[Contract]) -> str:
        """Create a concise summary of the portfolio"""
        summary_lines = ["\nPORTFOLIO SUMMARY:"]
        
        # Count by type and currency
        by_type: Dict[str, int] = {}
        by_currency: Dict[str, float] = {}
        
        for contract in contracts:
            ct = contract.contract_type.value
            by_type[ct] = by_type.get(ct, 0) + 1
            
            notional = contract.notional if contract.is_asset else -contract.notional
            by_currency[contract.currency] = by_currency.get(contract.currency, 0) + notional
        
        summary_lines.append(f"  Total contracts: {len(contracts)}")
        summary_lines.append("  By type:")
        for ctype, count in by_type.items():
            summary_lines.append(f"    - {ctype}: {count}")
        
        summary_lines.append("  Net notional by currency:")
        for curr, notional in by_currency.items():
            summary_lines.append(f"    - {curr}: {notional:,.0f}")
        
        return "\n".join(summary_lines)
    
    @staticmethod
    def build_prompt(
        risk_factors: List[RiskFactor],
        counterparties: List[Counterparty],
        contracts: List[Contract],
        user_instruction: str,
        num_scenarios: int = 3,
        scenario_type: Literal["stress", "stochastic", "both"] = "stress"
    ) -> str:
        """
        Build a complete prompt for the LLM to generate scenarios.
        
        Args:
            risk_factors: List of all risk factors in the system
            counterparties: List of all counterparties
            contracts: List of all contracts/positions
            user_instruction: Free-text instruction from the user
            num_scenarios: Number of scenarios to generate
            scenario_type: Type of scenarios ("stress", "stochastic", or "both")
        
        Returns:
            Complete prompt string ready to send to the LLM
        """
        
        # Build prompt sections
        prompt_parts = [
            "You are an expert quantitative risk analyst specializing in Asset-Liability Management (ALM) and scenario generation.",
            "",
            "I need you to generate scenario definitions for stress testing and risk analysis.",
            "",
            "=" * 70,
            "CURRENT RISK FACTOR STATE",
            "=" * 70,
            PromptBuilder.summarize_risk_factors(risk_factors),
            "",
            PromptBuilder.summarize_counterparties(counterparties),
            "",
            PromptBuilder.summarize_portfolio(contracts),
            "",
            "=" * 70,
            "SCENARIO GENERATION REQUEST",
            "=" * 70,
            f"Scenario Type: {scenario_type.upper()}",
            f"Number of Scenarios: {num_scenarios}",
            "",
            "User Instruction:",
            user_instruction,
            "",
            "=" * 70,
            "OUTPUT FORMAT REQUIREMENTS",
            "=" * 70,
            "",
            "You MUST output your response as a valid JSON object with the following structure:",
            "",
            json.dumps({
                "scenarios": [
                    {
                        "name": "Scenario_Name_Here",
                        "description": "Detailed description of the scenario",
                        "scenario_type": "stress or stochastic",
                        "probability": "optional float for stochastic scenarios",
                        "shocks": [
                            {
                                "factor_type": "yield_curve, spread_curve, fx_rate, equity_index, or macro_factor",
                                "factor_id": "exact factor_id from the risk factors above",
                                "shock_type": "parallel_shift_bps, parallel_shift_pct, or multiplicative",
                                "value": "numeric shock value (e.g., 200 for +200bps, or 0.80 for -20%)",
                                "description": "optional brief shock description"
                            }
                        ]
                    }
                ]
            }, indent=2),
            "",
            "CRITICAL INSTRUCTIONS:",
            "1. Use ONLY factor_id values that appear in the risk factors listed above",
            "2. For yield_curve and spread_curve shocks, use 'parallel_shift_bps' (value in basis points)",
            "3. For fx_rate, equity_index, and macro_factor shocks, use 'parallel_shift_pct' or 'multiplicative'",
            "4. Ensure all shocks are realistic and internally consistent",
            "5. For credit stress scenarios, increase PD values by suggesting shocks to counterparty ratings",
            "6. Output ONLY the JSON object - no additional text before or after",
            "7. Ensure the JSON is valid and can be parsed by Python's json.loads()",
            "",
            "Generate the scenarios now:"
        ]
        
        return "\n".join(prompt_parts)
