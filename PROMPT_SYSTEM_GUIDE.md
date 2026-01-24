# Enhanced Prompt System - Implementation Guide

## 📋 Overview

This guide explains how to install and use the enhanced prompt system for your ALM Scenario Generator.

## 🎯 What's New

1. **alm_prompts.py** - Separate configuration file with 6 pre-built expert prompts
2. **Enhanced prompt_builder.py** - Supports loading custom prompts
3. **Easy customization** - Edit prompts without touching core code

## 📦 Installation Steps

### Step 1: Copy Files to Your Project

```bash
cd ~/alm_scenario_generator

# Copy the prompts configuration file
cp /mnt/user-data/outputs/alm_prompts.py ./

# Backup your current prompt_builder.py
cp alm_scenarios/llm/prompt_builder.py alm_scenarios/llm/prompt_builder.py.backup

# Replace with enhanced version
cp /mnt/user-data/outputs/prompt_builder_enhanced.py alm_scenarios/llm/prompt_builder.py
```

### Step 2: Verify Installation

```bash
# Test that alm_prompts.py loads correctly
python3 -c "import alm_prompts; print('✓ alm_prompts.py loaded successfully')"

# List available prompts
python3 -c "import alm_prompts; print(alm_prompts.list_available_prompts())"
```

Expected output:
```
✓ alm_prompts.py loaded successfully
{'default': 'Balanced ALM expert - General purpose scenarios',
 'conservative': 'Conservative analyst - Upper bounds and worst-case focus',
 'regulatory': 'Compliance specialist - Meets FINMA, EBA, Basel requirements',
 'historical': 'Financial historian - Event-based scenarios (2008, 2015, etc.)',
 'swiss': 'Swiss banking expert - CHF focus, FINMA compliance, mortgage risk',
 'stochastic': 'Quant analyst - Probabilistic Monte Carlo scenarios'}
```

## 🚀 Usage

### Option 1: Use from Command Line

No changes needed! Your existing web interface will use the 'default' prompt automatically.

```bash
cd ~/alm_scenario_generator
python3 web_interface.py
```

### Option 2: Programmatically Select Prompt

Update your `alm_scenarios/generator.py` to pass the prompt name:

```python
# In alm_scenarios/generator.py - Find the generate_scenarios method

def generate_scenarios(
    self,
    risk_factors: List[RiskFactor],
    counterparties: List[Counterparty],
    contracts: List[Contract],
    user_instruction: str,
    num_scenarios: int = 3,
    scenario_type: str = "stress",
    system_prompt_name: str = "default"  # ← ADD THIS PARAMETER
):
    # Build prompt with custom system prompt
    prompt = build_scenario_generation_prompt(
        risk_factors=risk_factors,
        counterparties=counterparties,
        contracts=contracts,
        user_instruction=user_instruction,
        num_scenarios=num_scenarios,
        scenario_type=scenario_type,
        system_prompt_name=system_prompt_name  # ← PASS IT HERE
    )
    
    # Rest of the method remains the same...
```

Then in `web_interface.py`:

```python
@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    instruction = data.get('instruction', '')
    num_scenarios = data.get('num_scenarios', 3)
    scenario_type = data.get('scenario_type', 'stress')
    prompt_type = data.get('prompt_type', 'default')  # ← ADD THIS
    
    # ... load data ...
    
    scenarios, df = generator.generate_scenarios(
        risk_factors=risk_factors,
        counterparties=counterparties,
        contracts=contracts,
        user_instruction=instruction,
        num_scenarios=num_scenarios,
        scenario_type=scenario_type,
        system_prompt_name=prompt_type  # ← PASS IT HERE
    )
```

### Option 3: Add Prompt Selector to Web Interface

Update your HTML form to include a prompt selector:

```html
<!-- In web_interface.py HTML section, add this after scenario_type -->
<div class="form-group">
    <label for="promptType">AI Expert Prompt:</label>
    <select id="promptType">
        <option value="default">Default - Balanced ALM Expert</option>
        <option value="conservative">Conservative - Worst-Case Focus</option>
        <option value="regulatory">Regulatory - FINMA/EBA Compliance</option>
        <option value="historical">Historical - Event-Based (2008, 2015, etc.)</option>
        <option value="swiss">Swiss Banking - CHF & FINMA Focus</option>
        <option value="stochastic">Stochastic - Monte Carlo Probabilistic</option>
    </select>
</div>
```

Update JavaScript:

```javascript
function generate() {
    const instruction = document.getElementById('instruction').value;
    const numScenarios = document.getElementById('numScenarios').value;
    const scenarioType = document.getElementById('scenarioType').value;
    const promptType = document.getElementById('promptType').value;  // ← ADD THIS
    
    fetch('/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            instruction: instruction,
            num_scenarios: parseInt(numScenarios),
            scenario_type: scenarioType,
            prompt_type: promptType  // ← ADD THIS
        })
    })
    // ... rest of function ...
}
```

## 📝 Available Prompts

### 1. **default** - Balanced ALM Expert
- General purpose scenarios
- Balanced approach between severity and plausibility
- Good for most use cases

### 2. **conservative** - Conservative Analyst
- Focuses on worst-case scenarios
- Uses upper bounds of shock ranges
- Emphasizes tail risks and compound events
- Best for: Risk-averse stress testing

### 3. **regulatory** - Compliance Specialist
- Meets FINMA, EBA, and Basel requirements
- References specific regulatory scenarios
- Includes mandatory minimum shocks
- Best for: Regulatory reporting and compliance

### 4. **historical** - Financial Historian
- Bases all scenarios on actual historical events
- References 2008 crisis, 2015 SNB floor removal, COVID-19, etc.
- Includes documented shock magnitudes
- Best for: Historical scenario analysis

### 5. **swiss** - Swiss Banking Expert
- CHF safe-haven dynamics
- Swiss mortgage market focus
- FINMA-specific requirements
- SNB policy considerations
- Best for: Swiss banking institutions

### 6. **stochastic** - Quantitative Analyst
- Probabilistic scenarios for Monte Carlo
- Specifies probability levels (95th, 99th percentile)
- Includes volatility and correlation assumptions
- Best for: Monte Carlo simulations, VaR calculations

## ✏️ Customizing Prompts

### Edit Existing Prompts

Simply edit `alm_prompts.py`:

```bash
cd ~/alm_scenario_generator
nano alm_prompts.py
```

Find the prompt you want to modify (e.g., `CONSERVATIVE_SYSTEM_PROMPT`) and edit it.

Changes take effect immediately - no need to restart the server!

### Create New Custom Prompts

Add your own prompt to `alm_prompts.py`:

```python
# Add to alm_prompts.py

MY_CUSTOM_PROMPT = """You are a [YOUR EXPERTISE HERE].

[YOUR GUIDELINES]

[YOUR SHOCK MAGNITUDES]

[YOUR SPECIFIC REQUIREMENTS]
"""

# Add to the AVAILABLE_PROMPTS dictionary
AVAILABLE_PROMPTS = {
    'default': DEFAULT_SYSTEM_PROMPT,
    'conservative': CONSERVATIVE_SYSTEM_PROMPT,
    # ... existing prompts ...
    'my_custom': MY_CUSTOM_PROMPT  # ← ADD YOUR PROMPT
}
```

Then update `list_available_prompts()`:

```python
def list_available_prompts() -> dict:
    return {
        'default': 'Balanced ALM expert',
        # ... existing descriptions ...
        'my_custom': 'My custom prompt description'  # ← ADD DESCRIPTION
    }
```

## 🧪 Testing

### Test a Specific Prompt

```bash
cd ~/alm_scenario_generator

# Create test script
cat > test_prompt.py << 'EOF'
from alm_scenarios import ALMScenarioGenerator, LlamaClient
from load_alm_data import load_from_riskpro

# Load data
risk_factors, counterparties, contracts = load_from_riskpro(limit_contracts=100)

# Create generator
llm_client = LlamaClient(base_url="http://localhost:11434", model_name="llama3")
generator = ALMScenarioGenerator(llm_client)

# Test with conservative prompt
scenarios, df = generator.generate_scenarios(
    risk_factors=risk_factors,
    counterparties=counterparties,
    contracts=contracts,
    user_instruction="Generate 2 severe stress scenarios",
    num_scenarios=2,
    scenario_type="stress",
    system_prompt_name="conservative"  # ← TEST DIFFERENT PROMPTS
)

print(f"Generated {len(scenarios)} scenarios")
for s in scenarios:
    print(f"  - {s.name}: {len(s.shocks)} shocks")
EOF

# Run test
python3 test_prompt.py
```

### Compare Prompts

Generate scenarios with different prompts and compare results:

```bash
# Test default
python3 test_prompt.py > results_default.txt

# Edit test_prompt.py to use 'conservative'
# Run again
python3 test_prompt.py > results_conservative.txt

# Compare
diff results_default.txt results_conservative.txt
```

## 📊 Prompt Effectiveness

### Which Prompt to Use When:

| Use Case | Recommended Prompt | Why |
|----------|-------------------|-----|
| General stress testing | `default` | Balanced, covers all bases |
| Capital planning | `conservative` | Tests resilience under extreme stress |
| Regulatory submission | `regulatory` | Meets compliance requirements |
| Board presentations | `historical` | Relatable real-world scenarios |
| Swiss bank FINMA report | `swiss` | CHF-specific, FINMA requirements |
| VaR/Monte Carlo | `stochastic` | Probabilistic, for simulations |

## 🔧 Troubleshooting

### Prompt Not Loading

```bash
# Check if alm_prompts.py is in the right location
ls -l ~/alm_scenario_generator/alm_prompts.py

# Test import
python3 -c "import alm_prompts; print(alm_prompts.DEFAULT_SYSTEM_PROMPT[:100])"
```

### Syntax Errors in Custom Prompts

Python will show an error if your prompt has syntax issues:

```bash
# Validate syntax
python3 -m py_compile alm_prompts.py
```

### Prompt Not Taking Effect

The old prompt might be cached. Restart the web interface:

```bash
# Stop web interface (Ctrl+C)
# Start again
python3 web_interface.py
```

## 📚 Next Steps

1. **Start with 'default'** - Get comfortable with the system
2. **Try 'historical'** - See real event-based scenarios
3. **Test 'conservative'** - Compare stress levels
4. **Customize** - Edit prompts to match your needs
5. **Create new prompts** - Add company-specific expertise

## 💡 Tips

- **Shorter is better**: LLMs work better with concise, clear prompts
- **Use examples**: Include specific examples in your prompts
- **Test iteratively**: Try small changes and observe results
- **Document assumptions**: Include your rationale in prompt comments
- **Version control**: Keep backups when editing prompts

## 📧 Support

For questions or issues:
1. Check the troubleshooting section above
2. Review the prompt examples in `alm_prompts.py`
3. Test with the default prompt first
4. Check console output for error messages

---

**Last Updated**: 2026-01-23
**Version**: 1.0
