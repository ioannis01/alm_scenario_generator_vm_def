"""
Scenario Parser

Parses LLM JSON responses into structured scenario objects.
"""

from typing import List
import json
import pandas as pd

from ..models import Scenario, Shock


class ScenarioParser:
    """Parse LLM responses into structured scenario objects"""
    
    @staticmethod
    def parse_llm_response(response_text: str) -> List[Scenario]:
        """
        Parse the LLM's JSON response into Scenario objects.
        """
        # Clean input
        response_text = response_text.strip()
        
        # Extract JSON part
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON object found in response")
        
        json_text = response_text[json_start:json_end]

        # -------------------------------------------------------------
        # 🔧 CLEANUP STEP (handles common LLM JSON issues)
        # -------------------------------------------------------------
        import re

        # 1) Remove trailing commas before '}' or ']'
        json_text = re.sub(r',\s*([}\]])', r'\1', json_text)

        # 2) Optional fix: Convert single quotes to double quotes
        # (Enable only if needed, can break apostrophes inside text)
        # json_text = json_text.replace("'", '"')

        # 3) Optional: remove comments (if model outputs // or #)
        json_text = re.sub(r'//.*?\n|#.*?\n', '\n', json_text)
        # -------------------------------------------------------------

        # DEBUG PRINT
        print("\n================ RAW LLM JSON TEXT ================\n")
        print(json_text)
        print("\n===================================================\n")

        # Parse cleaned JSON
        data = json.loads(json_text)
        # -------------------------------------------------------------

        # Convert to Scenario objects
        scenarios = []
        for scenario_data in data.get("scenarios", []):
            shocks = [
                Shock(
                    factor_type=shock.get("factor_type"),
                    factor_id=shock.get("factor_id"),
                    shock_type=shock.get("shock_type"),
                    value=shock.get("value"),
                    description=shock.get("description")
                )
                for shock in scenario_data.get("shocks", [])
            ]
            
            scenario = Scenario(
                name=scenario_data.get("name"),
                description=scenario_data.get("description"),
                scenario_type=scenario_data.get("scenario_type", "stress"),
                probability=scenario_data.get("probability"),
                shocks=shocks
            )
            scenarios.append(scenario)
        
        return scenarios

    
    @staticmethod
    def scenarios_to_dataframe(scenarios: List[Scenario]) -> pd.DataFrame:
        """
        Convert scenarios to a pandas DataFrame for easy analysis.
        
        Args:
            scenarios: List of Scenario objects
        
        Returns:
            DataFrame with columns: scenario_name, scenario_type, factor_type,
            factor_id, shock_type, shock_value, shock_description
        """
        rows = []
        
        for scenario in scenarios:
            for shock in scenario.shocks:
                rows.append({
                    "scenario_name": scenario.name,
                    "scenario_description": scenario.description,
                    "scenario_type": scenario.scenario_type,
                    "probability": scenario.probability,
                    "factor_type": shock.factor_type,
                    "factor_id": shock.factor_id,
                    "shock_type": shock.shock_type,
                    "shock_value": shock.value,
                    "shock_description": shock.description
                })
        
        return pd.DataFrame(rows)
