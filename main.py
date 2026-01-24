"""
ALM Scenario Generator - Main Demo

This is the main entry point that demonstrates the end-to-end workflow.
"""

from alm_scenarios import (
    ALMScenarioGenerator,
    LlamaClient,
    create_sample_universe # Keep this for fallback
)

from load_alm_data import load_from_riskpro


def main():
    """Main demo function"""
    
    print("=" * 80)
    print("ALM SCENARIO GENERATOR - DEMO")
    print("=" * 80)
    print()
    
    # Step 1: Load from RiskPro OR use sample data
    print("Step 1: Loading ALM data...")

    """
    # Option A: Use real RiskPro data
    try:
        risk_factors, counterparties, contracts = load_from_riskpro(limit_contracts=1000)
        print("  ✓ Loaded from RiskPro database")
    except Exception as e:
        print(f"  ⚠ Could not load from RiskPro: {e}")
        print("  ↳ Falling back to sample data...")
        # Option B: Create sample universe
        print("Step 1: Creating sample universe...")
        risk_factors, counterparties, contracts = create_sample_universe()
        print(f"  ✓ Created {len(risk_factors)} risk factors")
        print(f"  ✓ Created {len(counterparties)} counterparties")
        print(f"  ✓ Created {len(contracts)} contracts")
        print()
    """
    # Data loading strategy selector
    data_source = input("Select data source:\n  1: RiskPro database\n  2: Sample universe\n  3: Sample risk factors + RiskPro counterparties/contracts\nEnter choice (1/2/3, default=1): ").strip() or "1"
    
    if data_source == "1":
        # Option A: Use real RiskPro data
        try:
            risk_factors, counterparties, contracts = load_from_riskpro(limit_contracts=1000)
            print("  ✓ Loaded from RiskPro database")
        except Exception as e:
            print(f"  ⚠ Could not load from RiskPro: {e}")
            print("  ↳ Falling back to sample data...")
            # Fallback to Option B
            print("Step 1: Creating sample universe...")
            risk_factors, counterparties, contracts = create_sample_universe()
            print(f"  ✓ Created {len(risk_factors)} risk factors")
            print(f"  ✓ Created {len(counterparties)} counterparties")
            print(f"  ✓ Created {len(contracts)} contracts")
            print()
    
    elif data_source == "2":
        # Option B: Create sample universe
        print("Step 1: Creating sample universe...")
        risk_factors, counterparties, contracts = create_sample_universe()
        print(f"  ✓ Created {len(risk_factors)} risk factors")
        print(f"  ✓ Created {len(counterparties)} counterparties")
        print(f"  ✓ Created {len(contracts)} contracts")
        print()
    
    elif data_source == "3":
        # Option C: Hybrid - Sample risk factors + RiskPro counterparties/contracts
        print("Step 1: Loading hybrid data (Sample risk factors + RiskPro counterparties/contracts)...")
        try:
            # Load counterparties and contracts from RiskPro
            _, counterparties, contracts = load_from_riskpro(limit_contracts=1000)
            print(f"  ✓ Loaded {len(counterparties)} counterparties from RiskPro database")
            print(f"  ✓ Loaded {len(contracts)} contracts from RiskPro database")
            
            # Create sample risk factors
            risk_factors, _, _ = create_sample_universe()
            print(f"  ✓ Created {len(risk_factors)} sample risk factors")
            print()
        except Exception as e:
            print(f"  ⚠ Could not load counterparties/contracts from RiskPro: {e}")
            print("  ↳ Falling back to full sample data...")
            # Fallback to Option B
            risk_factors, counterparties, contracts = create_sample_universe()
            print(f"  ✓ Created {len(risk_factors)} risk factors")
            print(f"  ✓ Created {len(counterparties)} counterparties")
            print(f"  ✓ Created {len(contracts)} contracts")
            print()
    
    else:
        print(f"  ⚠ Invalid choice '{data_source}', defaulting to RiskPro database")
        # Default to Option A
        try:
            risk_factors, counterparties, contracts = load_from_riskpro(limit_contracts=1000)
            print("  ✓ Loaded from RiskPro database")
        except Exception as e:
            print(f"  ⚠ Could not load from RiskPro: {e}")
            print("  ↳ Falling back to sample data...")
            risk_factors, counterparties, contracts = create_sample_universe()
            print(f"  ✓ Created {len(risk_factors)} risk factors")
            print(f"  ✓ Created {len(counterparties)} counterparties")
            print(f"  ✓ Created {len(contracts)} contracts")
            print()



    # Step 2: Initialize LLM client and generator
    print("Step 2: Initializing LLM client...")
    llm_client = LlamaClient(
        base_url="http://localhost:11434",  # Adjust to your setup
        model_name="llama3",
        api_type="ollama" # or "openwebui" or "ollama"
    )
    generator = ALMScenarioGenerator(llm_client)
    print("  ✓ LLM client initialized")
    print()
    
    # Step 3: Define scenario request
    print("Step 3: Building scenario request...")
    user_instruction = """
    Generate 3 severe but plausible stress scenarios that could impact our Swiss-based
    ALM portfolio. Please include:
    
    1. A financial crisis scenario driven by the regualtors with sharp rate movements and credit spread widening
    2. A moderate recession scenario with rising unemployment and modest credit deterioration
    3. A currency crisis scenario similar to the 2015 SNB floor removal
    
    Each scenario should affect yield curves, credit spreads, FX rates, equity indices,
    and macro factors in a realistic and correlated manner.
    """
    print("  ✓ User instruction defined")
    print()
    
    # Step 4: Generate scenarios
    print("Step 4: Calling LLM to generate scenarios...")
    print("  (Using mock response for demo - replace with real API call)")
    scenarios, scenarios_df = generator.generate_scenarios(
        risk_factors=risk_factors,
        counterparties=counterparties,
        contracts=contracts,
        user_instruction=user_instruction,
        num_scenarios=3,
        scenario_type="stress" # or "stochastic" or "both"
    )
    print(f"  ✓ Generated {len(scenarios)} scenarios")
    print()
    
    # Step 5: Display results
    print("Step 5: Displaying generated scenarios...")
    print("=" * 80)
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\nSCENARIO {i}: {scenario.name}")
        print(f"Description: {scenario.description}")
        print(f"Type: {scenario.scenario_type}")
        print(f"Number of shocks: {len(scenario.shocks)}")
        print()
    
    print("=" * 80)
    print("\nSCENARIOS DATAFRAME:")
    print("=" * 80)
    print(scenarios_df.to_string(index=False))
    print()
    
    # Step 6: Save to CSV
    output_file = "scenarios_output.csv"
    scenarios_df.to_csv(output_file, index=False)
    print(f"✓ Scenarios saved to: {output_file}")
    print()
    
    # Step 7: Summary statistics
    print("=" * 80)
    print("SUMMARY STATISTICS:")
    print("=" * 80)
    print(f"Total scenarios: {scenarios_df['scenario_name'].nunique()}")
    print(f"Total shocks: {len(scenarios_df)}")
    print("\nShocks by factor type:")
    print(scenarios_df['factor_type'].value_counts())
    print("\nShocks by shock type:")
    print(scenarios_df['shock_type'].value_counts())
    print()
    
    print("=" * 80)
    print("FIRST STEP COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Configure the LlamaClient with your actual Open WebUI / Ollama endpoint")
    print("2. Uncomment the real API call code in alm_scenarios/llm/client.py")
    print("3. Replace sample universe with real data from your ALM system")
    print("4. Integrate the scenarios DataFrame into your ALM engine for scenario analysis")
    print()


if __name__ == "__main__":
    main()
