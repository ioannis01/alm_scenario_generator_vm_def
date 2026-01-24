# Quick Integration Guide

## Connecting to Your Real Llama 3 Instance

This guide shows you exactly what to uncomment and modify to connect the scenario generator to your actual Llama 3 / Open WebUI instance.

---

## Step 1: Install Llama 3 Locally

### Option A: Ollama (Recommended - Easiest)

```bash
# On Ubuntu
curl -fsSL https://ollama.com/install.sh | sh

# Pull Llama 3
ollama pull llama3

# Or pull a larger model for better quality
ollama pull llama3:70b

# Verify it's running
ollama list
```

Ollama will automatically start on `http://localhost:11434`

### Option B: Open WebUI

Follow instructions at: https://docs.openwebui.com/getting-started/

---

## Step 2: Test Your Llama Connection

### Test Ollama

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "Say hello",
  "stream": false
}'
```

You should get a JSON response with the model's output.

### Test Open WebUI

```bash
curl http://localhost:8080/api/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "messages": [{"role": "user", "content": "Say hello"}]
  }'
```

---

## Step 3: Modify the Code

Open `alm_scenario_generator.py` and find the `LlamaClient.call_llm()` method (around line 540).

### For Ollama - Uncomment These Lines:

```python
def call_llm(self, prompt: str) -> str:
    if self.api_type == "ollama":
        endpoint = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
            }
        }
        
        # UNCOMMENT THESE 4 LINES:
        response = requests.post(
            endpoint,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()["response"]
        
        # COMMENT OUT THIS LINE:
        # return self._get_mock_response()
```

### For Open WebUI - Uncomment These Lines:

```python
def call_llm(self, prompt: str) -> str:
    elif self.api_type == "openwebui":
        endpoint = f"{self.base_url}/api/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        # If authentication is required, add:
        headers = {
            "Authorization": f"Bearer {your_api_key}",
            "Content-Type": "application/json"
        }
        
        # UNCOMMENT THESE 5 LINES:
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,  # if auth required, otherwise remove this
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
        
        # COMMENT OUT THIS LINE:
        # return self._get_mock_response()
```

---

## Step 4: Update Configuration

Edit `config.py`:

```python
LLM_CONFIG = {
    "ollama": {
        "base_url": "http://localhost:11434",  # Change if different
        "model_name": "llama3",  # Or "llama3:70b" for better quality
        "timeout": 120,
        "temperature": 0.3,
    },
    "active": "ollama"  # Or "openwebui"
}
```

---

## Step 5: Test the Real Connection

```python
from alm_scenario_generator import LlamaClient

# Initialize client
client = LlamaClient(
    base_url="http://localhost:11434",
    model_name="llama3",
    api_type="ollama"
)

# Test with a simple prompt
response = client.call_llm("Say hello in JSON format: {\"message\": \"...\"}")
print(response)
```

You should see actual output from your Llama model!

---

## Step 6: Run End-to-End

```bash
python alm_scenario_generator.py
```

This time it will call your **real** Llama instance and generate scenarios based on actual LLM inference!

---

## Troubleshooting

### Error: Connection refused
**Problem**: Llama isn't running
**Solution**: 
```bash
# For Ollama
ollama serve

# For Open WebUI
# Check the Open WebUI documentation
```

### Error: Model not found
**Problem**: The model isn't downloaded
**Solution**:
```bash
ollama pull llama3
# or
ollama pull llama3:70b
```

### Error: JSON parsing failed
**Problem**: LLM output isn't valid JSON
**Solutions**:
1. Lower temperature to 0.1-0.2 for more deterministic output
2. Try a larger model (llama3:70b)
3. Add more examples to the prompt
4. Check the LLM response manually to see what it's outputting

### Slow responses
**Solutions**:
1. Use a quantized model: `ollama pull llama3:Q4_K_M`
2. Reduce max_tokens
3. Use GPU if available
4. Use a smaller model for simple scenarios

---

## Performance Tips

### Use Quantized Models for Speed

```bash
# Smaller, faster models
ollama pull llama3:Q4_K_M
ollama pull llama3:Q5_K_M
```

Update config:
```python
"model_name": "llama3:Q4_K_M"
```

### Adjust Temperature

- **Lower (0.1-0.3)**: More deterministic, better for structured output
- **Higher (0.7-0.9)**: More creative scenarios, but less consistent format

### Increase Timeout for Large Requests

```python
LLM_CONFIG = {
    "ollama": {
        "timeout": 300,  # 5 minutes for complex scenarios
    }
}
```

---

## Model Recommendations

| Use Case | Model | Pros | Cons |
|----------|-------|------|------|
| **Testing** | llama3 | Fast, good quality | Medium quality |
| **Production** | llama3:70b | Best quality | Slower, needs more RAM |
| **Speed** | llama3:Q4_K_M | Fastest | Lower quality |
| **Balance** | llama3 or llama3:Q5_K_M | Good speed/quality | - |

---

## Example: Full Working Setup

```python
# config.py
LLM_CONFIG = {
    "ollama": {
        "base_url": "http://localhost:11434",
        "model_name": "llama3",
        "timeout": 180,
        "temperature": 0.2,  # Lower for better JSON
    },
    "active": "ollama"
}

# test_real_llm.py
from alm_scenario_generator import (
    ALMScenarioGenerator,
    LlamaClient,
    create_sample_universe
)

# 1. Initialize with real LLM
llm_client = LlamaClient(
    base_url="http://localhost:11434",
    model_name="llama3",
    api_type="ollama"
)

generator = ALMScenarioGenerator(llm_client)

# 2. Load universe
risk_factors, counterparties, contracts = create_sample_universe()

# 3. Generate real scenarios
scenarios, df = generator.generate_scenarios(
    risk_factors=risk_factors,
    counterparties=counterparties,
    contracts=contracts,
    user_instruction="""
    Generate 3 stress scenarios:
    1. Severe interest rate shock
    2. Credit crisis
    3. FX crisis
    """,
    num_scenarios=3
)

# 4. View results
print(df)
df.to_csv("real_scenarios.csv")
```

---

## Next: Loading Real ALM Data

Once the LLM connection works, replace the sample data:

```python
def load_from_your_alm_system():
    """Replace this with your actual data loading logic"""
    
    # Load from database, files, API, etc.
    risk_factors = load_yield_curves() + load_spreads() + ...
    counterparties = load_counterparties_from_db()
    contracts = load_portfolio_positions()
    
    return risk_factors, counterparties, contracts

# Use in main:
risk_factors, counterparties, contracts = load_from_your_alm_system()
```

---

**You're now ready to generate AI-powered scenarios for your ALM system!** 🚀
