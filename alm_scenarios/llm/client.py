"""
LLM Client

Handles communication with local Llama 3 models via Ollama or Open WebUI.
"""

from typing import Literal
import json
import requests


class LlamaClient:
    """
    Client for interacting with local Llama 3 model via Open WebUI or Ollama.
    
    This is designed to be easily adaptable to your specific setup.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "llama3",
        api_type: Literal["ollama", "openwebui"] = "ollama",
        timeout: int = 300,   # 🔧 was 120 – give the model more time
    ):
        """
        Initialize the Llama client.
        
        Args:
            base_url: Base URL of the Llama service
            model_name: Name of the model to use
            api_type: Type of API ("ollama" or "openwebui")
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.api_type = api_type
        self.timeout = timeout
    
    def call_llm(self, prompt: str) -> str:
        """
        Call the local Llama 3 model with a prompt.
        
        Args:
            prompt: The prompt to send to the model
        
        Returns:
            The model's response as a string
        
        Raises:
            requests.RequestException / RuntimeError: If the API call fails
        """
        
        if self.api_type == "ollama":
            # Ollama API format
            # Documentation: https://github.com/ollama/ollama/blob/main/docs/api.md
            endpoint = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more deterministic output
                    "top_p": 0.9,
                    # Optional: limit output length to keep runtime under control
                    # "num_predict": 1024,
                }
            }
            
            try:
                response = requests.post(
                    endpoint,
                    json=payload,
                    timeout=self.timeout,  # now 300s by default
                )
                response.raise_for_status()
            except requests.exceptions.ReadTimeout as e:
                # Make this visible in your Flask log / UI
                raise RuntimeError(
                    f"LLM request timed out after {self.timeout} seconds. "
                    "Try reducing the number of scenarios or using a smaller/faster model."
                ) from e
            except requests.RequestException as e:
                raise RuntimeError(f"Error calling LLM backend: {e}") from e

            return response.json()["response"]

        elif self.api_type == "openwebui":
            # Open WebUI API format (similar to OpenAI API)
            endpoint = f"{self.base_url}/api/chat/completions"
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 4000,
            }
            
            # If you don't use auth yet, define empty headers
            headers = {}  # 🔧 avoid 'headers' being undefined

            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        
        # If somehow api_type is wrong:
        raise ValueError(f"Unsupported api_type: {self.api_type}")
    
    def _get_mock_response(self) -> str:
        """
        Mock LLM response for testing without a real LLM connection.
        
        Returns a realistic JSON response that the parser can handle.
        """
        mock_response = {
            "scenarios": [
                {
                    "name": "Severe_Rate_Shock_2008_Style",
                    "description": "Parallel +250 bps shift in all yield curves similar to 2008 financial crisis, with credit spreads widening significantly and equity markets declining sharply",
                    "scenario_type": "stress",
                    "shocks": [
                        {
                            "factor_type": "yield_curve",
                            "factor_id": "CHF_SWAP",
                            "shock_type": "parallel_shift_bps",
                            "value": 250,
                            "description": "Sharp rate increase due to flight to safety"
                        },
                        {
                            "factor_type": "yield_curve",
                            "factor_id": "EUR_SWAP",
                            "shock_type": "parallel_shift_bps",
                            "value": 250,
                            "description": "Parallel EUR rate shock"
                        },
                        {
                            "factor_type": "spread_curve",
                            "factor_id": "CHF_CORP_BBB",
                            "shock_type": "parallel_shift_bps",
                            "value": 200,
                            "description": "Credit spread widening for BBB corporates"
                        },
                        {
                            "factor_type": "spread_curve",
                            "factor_id": "CHF_CORP_A",
                            "shock_type": "parallel_shift_bps",
                            "value": 150,
                            "description": "Credit spread widening for A-rated corporates"
                        },
                        {
                            "factor_type": "equity_index",
                            "factor_id": "SMI",
                            "shock_type": "multiplicative",
                            "value": 0.70,
                            "description": "30% equity market decline"
                        },
                        {
                            "factor_type": "fx_rate",
                            "factor_id": "EURCHF",
                            "shock_type": "multiplicative",
                            "value": 1.15,
                            "description": "EUR strengthening due to safe haven flows"
                        }
                    ]
                },
                {
                    "name": "Moderate_Recession_Scenario",
                    "description": "Moderate recession with rising unemployment, declining GDP, modest rate cuts, and moderate credit deterioration",
                    "scenario_type": "stress",
                    "shocks": [
                        {
                            "factor_type": "macro_factor",
                            "factor_id": "CH_GDP_GROWTH",
                            "shock_type": "absolute_change",
                            "value": -2.5,
                            "description": "GDP contraction of 2.5%"
                        },
                        {
                            "factor_type": "macro_factor",
                            "factor_id": "CH_UNEMPLOYMENT",
                            "shock_type": "absolute_change",
                            "value": 2.0,
                            "description": "Unemployment rises by 2 percentage points"
                        },
                        {
                            "factor_type": "yield_curve",
                            "factor_id": "CHF_SWAP",
                            "shock_type": "parallel_shift_bps",
                            "value": -100,
                            "description": "Rate cuts to stimulate economy"
                        },
                        {
                            "factor_type": "spread_curve",
                            "factor_id": "CHF_CORP_BBB",
                            "shock_type": "parallel_shift_bps",
                            "value": 100,
                            "description": "Moderate credit spread widening"
                        },
                        {
                            "factor_type": "equity_index",
                            "factor_id": "SMI",
                            "shock_type": "multiplicative",
                            "value": 0.85,
                            "description": "15% equity decline"
                        }
                    ]
                },
                {
                    "name": "Currency_Crisis_CHF_Appreciation",
                    "description": "Sudden CHF appreciation shock similar to SNB floor removal in 2015, with currency pairs moving sharply",
                    "scenario_type": "stress",
                    "shocks": [
                        {
                            "factor_type": "fx_rate",
                            "factor_id": "EURCHF",
                            "shock_type": "multiplicative",
                            "value": 0.85,
                            "description": "EUR/CHF drops 15% as CHF appreciates"
                        },
                        {
                            "factor_type": "fx_rate",
                            "factor_id": "USDCHF",
                            "shock_type": "multiplicative",
                            "value": 0.80,
                            "description": "USD/CHF drops 20% as CHF surges"
                        },
                        {
                            "factor_type": "equity_index",
                            "factor_id": "SMI",
                            "shock_type": "multiplicative",
                            "value": 0.90,
                            "description": "Swiss equity market declines on export concerns"
                        },
                        {
                            "factor_type": "yield_curve",
                            "factor_id": "CHF_SWAP",
                            "shock_type": "parallel_shift_bps",
                            "value": -50,
                            "description": "Flight to CHF safety lowers rates"
                        }
                    ]
                }
            ]
        }
        
        return json.dumps(mock_response, indent=2)
