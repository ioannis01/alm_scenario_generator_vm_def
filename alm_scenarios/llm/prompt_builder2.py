"""
Prompt Builder

Constructs prompts for the LLM to generate scenarios.
Enhanced to support customizable system prompts from alm_prompts.py
"""

from typing import List, Dict, Any, Literal, Optional
import json
import os
import sys

from ..models import RiskFactor, Counterparty, Contract
from ..models import YieldCurve, SpreadCurve, FXRate, EquityIndex, MacroFactor
from ..models.risk_factors import RiskFactorType


class PromptBuilder:
    """Builds prompts for the LLM to generate scenarios"""
    
    # Cache for loaded prompts
    _prompts_module = None
    
    @staticmethod
    def _load_prompts_module():
        """Lazy load the alm_prompts module"""
        if PromptBuilder._prompts_module is None:
            try:
                # Try to import alm_prompts from parent directory
                parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                
                import alm_prompts
                PromptBuilder._prompts_module = alm_prompts
                print("✓ Loaded custom system prompts from alm_prompts.py")
            except ImportError:
                print("⚠ alm_prompts.py not found, using default prompt")
                PromptBuilder._prompts_module = None
        
        return PromptBuilder._prompts_module
    
    @staticmethod
    def get_system_prompt(prompt_name: Optional[str] = None) -> str:
        """
        Get system prompt by name from alm_prompts.py
        
        Args:
            prompt_name: Name of prompt ('default', 'conservative', 'regulatory', etc.)
                        If None, uses 'default'
        
        Returns:
            System prompt string
        """
        prompts_module = PromptBuilder._load_prompts_module()
        
        if prompts_module and hasattr(prompts_module, 'get_system_prompt'):
            return prompts_module.get_system_prompt(prompt_name or 'default')
        else:
            # Fallback default prompt if alm_prompts.py not available
            return """You are an expert quantitative risk analyst specializing in Asset-Liability Management (ALM) and scenario generation.

EXPERTISE:
- Deep knowledge of interest rate risk, credit risk, and market risk
- Expert in regulatory frameworks (Basel III, FINMA, EBA)
- Strong understanding of correlation structures during stress

SHOCK GUIDELINES:
- Interest Rates: Mild (±50bps), Moderate (±100-150bps), Severe (±200-300bps)
- Credit Spreads: Mild (+50bps), Moderate (+100-150bps), Severe (+200-300bps)
- FX Rates: Mild (±5%), Moderate (±10-15%), Severe (±20-30%)

Generate realistic, internally consistent scenarios based on historical precedents."""
    
    @staticmethod
    def list_available_prompts() -> Dict[str, str]:
        """
        List available system prompts
        
        Returns:
            Dictionary of {prompt_name: description}
        """
        prompts_module = PromptBuilder._load_prompts_module()
        
        if prompts_module and hasattr(prompts_module, 'list_available_prompts'):
            return prompts_module.list_available_prompts()
        else:
            return {'default': 'Standard ALM expert prompt'}
    
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
        
        # Show first 10, then summarize
        for i, cp in enumerate(counterparties[:10]):
            summary_lines.append(
                f"  - {cp.counterparty_id} ({cp.name}): "
                f"Rating={cp.rating}, PD={cp.pd*100:.2f}%, "
                f"Recovery={cp.recovery_rate*100:.0f}%"
            )
        
        if len(counterparties) > 10:
            summary_lines.append(f"  ... and {len(counterparties) - 10} more counterparties")
        
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
        for ctype, count in sorted(by_type.items(), key=lambda x: -x[1]):
            summary_lines.append(f"    - {ctype}: {count}")
        
        summary_lines.append("  Net notional by currency:")
        for curr, notional in sorted(by_currency.items(), key=lambda x: -abs(x[1])):
            summary_lines.append(f"    - {curr}: {notional:,.0f}")
        
        return "\n".join(summary_lines)
    
    @staticmethod
    def build_prompt(
        risk_factors: List[RiskFactor],
        counterparties: List[Counterparty],
        contracts: List[Contract],
        user_instruction: str,
        num_scenarios: int = 3,
        scenario_type: Literal["stress", "stochastic", "both"] = "stress",
        system_prompt_name: Optional[str] = None,
        custom_system_prompt: Optional[str] = None
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
            system_prompt_name: Name of pre-defined prompt from alm_prompts.py
                               ('default', 'conservative', 'regulatory', 'historical', 
                                'swiss', 'stochastic')
            custom_system_prompt: Optional custom system prompt string (overrides system_prompt_name)
        
        Returns:
            Complete prompt string ready to send to the LLM
        """
        
        # Get system prompt
        if custom_system_prompt:
            system_prompt = custom_system_prompt
            print(f"  Using custom system prompt ({len(custom_system_prompt)} chars)")
        elif system_prompt_name:
            system_prompt = PromptBuilder.get_system_prompt(system_prompt_name)
            print(f"  Using system prompt: '{system_prompt_name}'")
        else:
            system_prompt = PromptBuilder.get_system_prompt('default')
            print(f"  Using default system prompt")
        
        # Build prompt sections
        prompt_parts = [
            system_prompt,
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
                        "description": "Detailed description of the scenario and its economic drivers",
                        "scenario_type": "stress or stochastic",
                        "probability": "optional float for stochastic scenarios (e.g., 0.05 for 5%)",
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
            "3. For fx_rate shocks, use 'multiplicative' (e.g., 1.15 for +15%, 0.85 for -15%)",
            "4. For equity_index shocks, use 'multiplicative' (e.g., 0.70 for -30% drop)",
            "5. For macro_factor shocks, use 'parallel_shift_pct' (percentage point change)",
            "6. Ensure all shocks are realistic and internally consistent",
            "7. Include economic narrative explaining the scenario drivers",
            "8. Output ONLY the JSON object - no additional text before or after",
            "9. Ensure the JSON is valid and can be parsed by Python's json.loads()",
            "",
            "Generate the scenarios now:"
        ]
        
        prompt = "\n".join(prompt_parts)
        
        # Log prompt statistics
        prompt_lines = len(prompt_parts)
        prompt_chars = len(prompt)
        print(f"  Prompt built: {prompt_lines} lines, {prompt_chars:,} characters")
        
        return prompt


# Convenience function for backward compatibility
def build_scenario_generation_prompt(
    risk_factors: List[RiskFactor],
    counterparties: List[Counterparty],
    contracts: List[Contract],
    user_instruction: str,
    num_scenarios: int = 3,
    scenario_type: Literal["stress", "stochastic", "both"] = "stress",
    system_prompt_name: Optional[str] = None,
    custom_system_prompt: Optional[str] = None
) -> str:
    """
    Convenience function that calls PromptBuilder.build_prompt()
    
    This maintains backward compatibility with existing code.
    """
    return PromptBuilder.build_prompt(
        risk_factors=risk_factors,
        counterparties=counterparties,
        contracts=contracts,
        user_instruction=user_instruction,
        num_scenarios=num_scenarios,
        scenario_type=scenario_type,
        system_prompt_name=system_prompt_name,
        custom_system_prompt=custom_system_prompt
    )
