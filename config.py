"""
Configuration file for ALM Scenario Generator

Copy this file and customize it for your environment.
"""

from typing import Dict, Any

# =============================================================================
# LLM Configuration
# =============================================================================

LLM_CONFIG = {
    # Ollama Configuration (Local deployment)
    "ollama": {
        "base_url": "http://localhost:11434",
        "model_name": "llama3",
        "timeout": 120,
        "temperature": 0.3,
        "top_p": 0.9,
        "max_tokens": 4000
    },
    
    # Open WebUI Configuration
    "openwebui": {
        "base_url": "http://localhost:8080",
        "model_name": "llama3",
        "api_key": None,  # Set this if authentication required
        "timeout": 120,
        "temperature": 0.3,
        "max_tokens": 4000
    },
    
    # Active configuration (choose "ollama" or "openwebui")
    "active": "ollama"
}

# =============================================================================
# Scenario Generation Defaults
# =============================================================================

SCENARIO_DEFAULTS = {
    # Default number of scenarios to generate
    "num_scenarios": 3,
    
    # Default scenario type ("stress", "stochastic", or "both")
    "scenario_type": "stress",
    
    # Whether to include counterparty credit risk in scenarios
    "include_credit_risk": True,
    
    # Whether to include behavioral risk factors
    "include_behavioral_risk": False,
}

# =============================================================================
# Validation Settings
# =============================================================================

VALIDATION_CONFIG = {
    # Maximum absolute shock for interest rates (in basis points)
    "max_rate_shock_bps": 500,
    
    # Maximum multiplicative shock for equity indices (as decimal)
    "max_equity_shock": 0.50,  # 50% decline
    
    # Maximum FX rate shock (as decimal)
    "max_fx_shock": 0.30,  # 30% movement
    
    # Maximum credit spread shock (in basis points)
    "max_spread_shock_bps": 500,
    
    # Whether to validate factor IDs against known universe
    "validate_factor_ids": True,
    
    # Whether to validate shock types match factor types
    "validate_shock_types": True,
}

# =============================================================================
# Output Settings
# =============================================================================

OUTPUT_CONFIG = {
    # Directory for saving scenario outputs
    "output_dir": "/mnt/user-data/outputs",
    
    # File format for scenarios ("csv", "excel", "json", or "all")
    "output_format": "csv",
    
    # Whether to include detailed shock descriptions
    "include_descriptions": True,
    
    # Whether to create summary statistics
    "create_summary": True,
    
    # Timestamp format for output files
    "timestamp_format": "%Y%m%d_%H%M%S",
}

# =============================================================================
# Prompt Engineering Settings
# =============================================================================

PROMPT_CONFIG = {
    # System role description for the LLM
    "system_role": "You are an expert quantitative risk analyst specializing in Asset-Liability Management (ALM) and scenario generation.",
    
    # Additional instructions to include in every prompt
    "additional_instructions": [
        "Ensure all shocks are realistic and internally consistent",
        "Consider correlations between different risk factors",
        "Provide clear descriptions for each scenario",
    ],
    
    # Examples to include in the prompt (few-shot learning)
    "include_examples": False,
    
    # Verbosity level for prompt context ("minimal", "standard", "detailed")
    "context_verbosity": "standard",
}

# =============================================================================
# Risk Factor Defaults
# =============================================================================

RISK_FACTOR_DEFAULTS = {
    # Default tenors for yield curves (if not specified)
    "yield_curve_tenors": ["1M", "3M", "6M", "1Y", "2Y", "5Y", "10Y", "30Y"],
    
    # Default tenors for spread curves
    "spread_curve_tenors": ["1Y", "2Y", "5Y", "10Y"],
    
    # Default currencies to support
    "supported_currencies": ["CHF", "EUR", "USD", "GBP"],
    
    # Credit rating scale
    "rating_scale": ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", 
                     "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", 
                     "B+", "B", "B-", "CCC", "CC", "C", "D"],
}

# =============================================================================
# Performance Settings
# =============================================================================

PERFORMANCE_CONFIG = {
    # Enable caching of LLM responses
    "enable_caching": True,
    
    # Cache TTL in seconds (3600 = 1 hour)
    "cache_ttl": 3600,
    
    # Maximum cache size (number of entries)
    "cache_max_size": 100,
    
    # Enable parallel processing for batch operations
    "enable_parallel": False,
    
    # Number of worker threads for parallel processing
    "num_workers": 4,
}

# =============================================================================
# Logging Configuration
# =============================================================================

LOGGING_CONFIG = {
    # Logging level ("DEBUG", "INFO", "WARNING", "ERROR")
    "level": "INFO",
    
    # Log file path (None for console only)
    "log_file": None,
    
    # Log format
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    
    # Whether to log prompts sent to LLM
    "log_prompts": True,
    
    # Whether to log LLM responses
    "log_responses": True,
}

# =============================================================================
# Database Connection (Optional - for loading from ALM system)
# =============================================================================

DATABASE_CONFIG = {
    # Database type ("postgresql", "oracle", "mssql", "sqlite")
    "db_type": "postgresql",
    
    # Connection string (adjust based on your database)
    "connection_string": None,  # e.g., "postgresql://user:pass@localhost:5432/alm_db"
    
    # Query timeout in seconds
    "query_timeout": 30,
    
    # Table names in your ALM system
    "tables": {
        "risk_factors": "risk_factors",
        "yield_curves": "yield_curves",
        "spread_curves": "spread_curves",
        "fx_rates": "fx_rates",
        "counterparties": "counterparties",
        "contracts": "contracts",
    }
}

# =============================================================================
# Helper Functions
# =============================================================================

def get_active_llm_config() -> Dict[str, Any]:
    """Get the active LLM configuration"""
    active = LLM_CONFIG["active"]
    return LLM_CONFIG[active]

def get_output_path(filename: str) -> str:
    """Get full output path for a file"""
    import os
    from datetime import datetime
    
    timestamp = datetime.now().strftime(OUTPUT_CONFIG["timestamp_format"])
    base_name, ext = os.path.splitext(filename)
    timestamped_name = f"{base_name}_{timestamp}{ext}"
    
    return os.path.join(OUTPUT_CONFIG["output_dir"], timestamped_name)

# =============================================================================
# Environment-Specific Overrides
# =============================================================================

def load_environment_config():
    """
    Load configuration from environment variables.
    Useful for containerized deployments.
    """
    import os
    
    # Override LLM settings from environment
    if os.getenv("LLM_BASE_URL"):
        LLM_CONFIG["ollama"]["base_url"] = os.getenv("LLM_BASE_URL")
    
    if os.getenv("LLM_MODEL_NAME"):
        LLM_CONFIG["ollama"]["model_name"] = os.getenv("LLM_MODEL_NAME")
    
    if os.getenv("LLM_API_KEY"):
        LLM_CONFIG["openwebui"]["api_key"] = os.getenv("LLM_API_KEY")
    
    # Override database connection from environment
    if os.getenv("DATABASE_URL"):
        DATABASE_CONFIG["connection_string"] = os.getenv("DATABASE_URL")
    
    # Override output directory from environment
    if os.getenv("OUTPUT_DIR"):
        OUTPUT_CONFIG["output_dir"] = os.getenv("OUTPUT_DIR")

# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Print current configuration
    print("Active LLM Configuration:")
    print(get_active_llm_config())
    
    print("\nScenario Defaults:")
    print(SCENARIO_DEFAULTS)
    
    print("\nValidation Config:")
    print(VALIDATION_CONFIG)
    
    # Example: Get output path
    output_file = get_output_path("scenarios.csv")
    print(f"\nExample output path: {output_file}")
