"""
Scenario Generator

Main orchestrator for end-to-end scenario generation workflow.
"""

from typing import List, Literal, Tuple
import pandas as pd

from ..models import RiskFactor, Counterparty, Contract, Scenario
from ..llm import LlamaClient, PromptBuilder
from ..parsers import ScenarioParser


class ALMScenarioGenerator:
    """
    Main class that orchestrates the end-to-end scenario generation workflow.
    """
    
    def __init__(self, llm_client: LlamaClient):
        """
        Initialize the scenario generator.
        
        Args:
            llm_client: Configured LlamaClient instance
        """
        self.llm_client = llm_client
        self.prompt_builder = PromptBuilder()
        self.parser = ScenarioParser()
    
    def generate_scenarios(
        self,
        risk_factors: List[RiskFactor],
        counterparties: List[Counterparty],
        contracts: List[Contract],
        user_instruction: str,
        num_scenarios: int = 3,
        scenario_type: Literal["stress", "stochastic", "both"] = "stress"
    ) -> Tuple[List[Scenario], pd.DataFrame]:
        """
        Generate scenarios using the LLM.
        
        Args:
            risk_factors: List of risk factors
            counterparties: List of counterparties
            contracts: List of contracts
            user_instruction: User's scenario request
            num_scenarios: Number of scenarios to generate
            scenario_type: Type of scenarios to generate
        
        Returns:
            Tuple of (List of Scenario objects, DataFrame of shocks)
        """
        # Build prompt
        prompt = self.prompt_builder.build_prompt(
            risk_factors=risk_factors,
            counterparties=counterparties,
            contracts=contracts,
            user_instruction=user_instruction,
            num_scenarios=num_scenarios,
            scenario_type=scenario_type
        )
        
        # Call LLM
        response = self.llm_client.call_llm(prompt)
        
        # Parse response
        scenarios = self.parser.parse_llm_response(response)
        
        # Convert to DataFrame
        df = self.parser.scenarios_to_dataframe(scenarios)
        
        return scenarios, df
