"""
title: ALM Scenario Generator
author: Your Name
version: 1.0
description: Generate stress and stochastic scenarios for ALM systems
required_open_webui_version: 0.3.0
"""

import os
import sys
from typing import Callable, Any
import json

# Add the path to your scenario generator
sys.path.append('/c/Users/OneDrive - Wolters Kluwer/Product Managemant/Product Managemant/OPEN_AI/alm_scenario_generator')  # UPDATE THIS PATH

from alm_scenarios import ALMScenarioGenerator, LlamaClient
from load_alm_data import load_from_riskpro


class Tools:
    def __init__(self):
        self.citation = True
        
        # Cache loaded data to avoid reloading on every call
        self.data_loaded = False
        self.risk_factors = None
        self.counterparties = None
        self.contracts = None
    
    def load_alm_data(self):
        """Load ALM data from RiskPro (cached)"""
        if not self.data_loaded:
            print("Loading ALM data from RiskPro...")
            self.risk_factors, self.counterparties, self.contracts = load_from_riskpro(
                limit_contracts=1000
            )
            self.data_loaded = True
            print(f"✓ Loaded {len(self.risk_factors)} risk factors, "
                  f"{len(self.counterparties)} counterparties, "
                  f"{len(self.contracts)} contracts")
        return self.risk_factors, self.counterparties, self.contracts
    
    async def generate_alm_scenarios(
        self,
        user_instruction: str,
        num_scenarios: int = 3,
        scenario_type: str = "stress",
        __event_emitter__: Callable[[dict], Any] = None
    ) -> str:
        """
        Generate ALM stress or stochastic scenarios.
        
        :param user_instruction: Description of scenarios to generate
        :param num_scenarios: Number of scenarios (1-10)
        :param scenario_type: Type of scenarios ("stress", "stochastic", or "both")
        """
        
        try:
            # Emit status update
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": "Loading ALM data from RiskPro...", "done": False}
                })
            
            # Load ALM data
            risk_factors, counterparties, contracts = self.load_alm_data()
            
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": f"Loaded {len(contracts)} contracts. Generating scenarios...", "done": False}
                })
            
            # Initialize scenario generator (using the same Ollama instance)
            llm_client = LlamaClient(
                base_url="http://localhost:11434",
                model_name="llama3",
                api_type="ollama"
            )
            generator = ALMScenarioGenerator(llm_client)
            
            # Generate scenarios
            scenarios, scenarios_df = generator.generate_scenarios(
                risk_factors=risk_factors,
                counterparties=counterparties,
                contracts=contracts,
                user_instruction=user_instruction,
                num_scenarios=min(num_scenarios, 10),
                scenario_type=scenario_type
            )
            
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": f"Generated {len(scenarios)} scenarios!", "done": True}
                })
            
            # Format results for display
            result = f"# Generated {len(scenarios)} ALM Scenarios\n\n"
            
            for i, scenario in enumerate(scenarios, 1):
                result += f"## Scenario {i}: {scenario.name}\n\n"
                result += f"**Type:** {scenario.scenario_type}\n\n"
                result += f"**Description:** {scenario.description}\n\n"
                result += f"**Number of shocks:** {len(scenario.shocks)}\n\n"
                
                result += "**Shocks:**\n"
                for shock in scenario.shocks[:10]:  # Show first 10 shocks
                    result += f"- {shock.factor_type} | {shock.factor_id}: "
                    result += f"{shock.shock_type} = {shock.value}\n"
                
                if len(scenario.shocks) > 10:
                    result += f"- ... and {len(scenario.shocks) - 10} more shocks\n"
                
                result += "\n---\n\n"
            
            # Save to CSV
            csv_path = "/tmp/alm_scenarios.csv"
            scenarios_df.to_csv(csv_path, index=False)
            result += f"\n📊 **Full scenarios saved to:** `{csv_path}`\n"
            result += f"📈 **Total shocks:** {len(scenarios_df)}\n"
            
            return result
            
        except Exception as e:
            error_msg = f"❌ Error generating scenarios: {str(e)}\n\n"
            error_msg += "Please check:\n"
            error_msg += "- RiskPro database connection\n"
            error_msg += "- Ollama is running\n"
            error_msg += "- Path to alm_scenario_generator is correct\n"
            return error_msg