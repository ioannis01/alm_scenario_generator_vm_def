<<<<<<< HEAD
# ALM Scenario Generator with LLM

**Production-ready Python framework for generating stress and stochastic scenarios using local Llama 3 models**

---

## 📋 Overview

This framework enables Asset-Liability Management (ALM) systems to leverage Large Language Models (LLMs) for intelligent scenario generation. Instead of manually defining stress scenarios, you can describe the conditions you want to test in natural language, and the LLM will generate comprehensive, realistic scenario definitions.

### Key Features

- ✅ **Comprehensive Risk Factor Coverage**: Yield curves, credit spreads, FX rates, equity indices, macro factors
- ✅ **Credit Risk Integration**: Counterparty-level PD, ratings, and recovery rates
- ✅ **Flexible Scenario Types**: Stress scenarios and stochastic scenarios
- ✅ **Smart Prompt Engineering**: Context-aware prompts that include current portfolio state
- ✅ **Structured JSON Output**: Machine-parseable scenario definitions
- ✅ **Easy Integration**: Simple API to connect to Ollama or Open WebUI
- ✅ **Production Ready**: Type hints, error handling, comprehensive documentation

---

## 🏗️ Architecture

### Layer 1: Data Model
Defines the domain objects for risk factors, counterparties, and contracts:

```
RiskFactor (abstract)
├── YieldCurve: Term structure of interest rates
├── SpreadCurve: Credit or liquidity spreads
├── FXRate: Foreign exchange rates
├── EquityIndex: Stock market indices
└── MacroFactor: GDP, inflation, unemployment, etc.

Counterparty: Credit risk attributes (PD, rating, recovery)

Contract: Financial positions linked to risk factors and counterparties
```

### Layer 2: Prompt Engineering
Builds intelligent prompts that:
1. Summarize current risk factor state
2. Describe portfolio characteristics
3. Include user instructions
4. Specify strict JSON output format

### Layer 3: LLM Interface
Connects to local Llama 3 via:
- **Ollama API** (default): Simple REST API
- **Open WebUI**: OpenAI-compatible API

### Layer 4: Response Parsing
Converts LLM JSON responses into:
- Python `Scenario` objects
- Pandas DataFrames for analysis
- Structured shock definitions

### Layer 5: Integration
Orchestrates the full workflow through `ALMScenarioGenerator`

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install pandas requests --break-system-packages
```

### 2. Set Up Llama 3 Locally

**Option A: Using Ollama (Recommended)**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull Llama 3
ollama pull llama3

# Verify it's running (default: http://localhost:11434)
ollama list
```

**Option B: Using Open WebUI**
Follow the [Open WebUI installation guide](https://docs.openwebui.com/)

### 3. Run the Demo

```bash
python alm_scenario_generator.py
```

This will:
- Create a sample ALM universe
- Generate a prompt
- Call the LLM (using mock response by default)
- Parse scenarios into a DataFrame
- Save results to CSV

---

## 📖 Usage Guide

### Basic Usage

```python
from alm_scenario_generator import (
    ALMScenarioGenerator,
    LlamaClient,
    create_sample_universe
)

# 1. Initialize LLM client
llm_client = LlamaClient(
    base_url="http://localhost:11434",
    model_name="llama3",
    api_type="ollama"
)

# 2. Create generator
generator = ALMScenarioGenerator(llm_client)

# 3. Load your risk factors, counterparties, and contracts
risk_factors, counterparties, contracts = create_sample_universe()
# Or load from your actual ALM system

# 4. Define scenario request
user_instruction = """
Generate 5 stochastic scenarios for a potential recession,
including:
- Rising unemployment (2-5%)
- Declining GDP growth (-1% to -3%)
- Central bank rate cuts (50-150 bps)
- Credit spread widening (50-200 bps)
- Equity market decline (10-30%)
"""

# 5. Generate scenarios
scenarios, scenarios_df = generator.generate_scenarios(
    risk_factors=risk_factors,
    counterparties=counterparties,
    contracts=contracts,
    user_instruction=user_instruction,
    num_scenarios=5,
    scenario_type="stochastic"
)

# 6. Use the scenarios
print(scenarios_df)
scenarios_df.to_csv("scenarios.csv")
```

### Connecting to Real LLM

Edit `LlamaClient.call_llm()` method:

**For Ollama:**
```python
def call_llm(self, prompt: str) -> str:
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
    
    response = requests.post(endpoint, json=payload, timeout=self.timeout)
    response.raise_for_status()
    return response.json()["response"]
```

**For Open WebUI with Authentication:**
```python
def call_llm(self, prompt: str) -> str:
    endpoint = f"{self.base_url}/api/chat/completions"
    headers = {
        "Authorization": f"Bearer {your_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": self.model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 4000
    }
    
    response = requests.post(
        endpoint,
        json=payload,
        headers=headers,
        timeout=self.timeout
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
```

---

## 🔧 Customization

### Adding New Risk Factor Types

```python
@dataclass
class CommodityPrice(RiskFactor):
    """Commodity price risk factor"""
    commodity: str
    spot_price: float
    unit: str = "USD/barrel"
    
    def __post_init__(self):
        self.factor_type = RiskFactorType.COMMODITY
        self.current_value = self.spot_price
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_id": self.factor_id,
            "factor_type": self.factor_type.value,
            "commodity": self.commodity,
            "spot_price": self.spot_price,
            "unit": self.unit
        }
```

### Custom Shock Types

Extend the `ShockType` enum and update the prompt instructions:

```python
class ShockType(Enum):
    PARALLEL_SHIFT_BPS = "parallel_shift_bps"
    STEEPENING = "steepening"
    FLATTENING = "flattening"
    BUTTERFLY = "butterfly"
    # ... your custom shock types
```

### Integration with Your ALM System

Replace `create_sample_universe()` with your data loader:

```python
def load_from_alm_system():
    """Load actual data from your ALM system"""
    
    # Example: Load from database
    risk_factors = []
    for curve in db.query("SELECT * FROM yield_curves"):
        risk_factors.append(YieldCurve(
            factor_id=curve['id'],
            currency=curve['currency'],
            tenors=curve['tenors'],
            rates=curve['rates']
        ))
    
    # Load counterparties
    counterparties = [...]
    
    # Load contracts
    contracts = [...]
    
    return risk_factors, counterparties, contracts
```

---

## 📊 Output Format

### Scenario DataFrame Structure

| Column | Type | Description |
|--------|------|-------------|
| `scenario_name` | str | Unique scenario identifier |
| `scenario_description` | str | Human-readable description |
| `scenario_type` | str | "stress" or "stochastic" |
| `probability` | float | Probability (for stochastic only) |
| `factor_type` | str | Type of risk factor |
| `factor_id` | str | Unique risk factor ID |
| `shock_type` | str | How to apply the shock |
| `shock_value` | float | Magnitude of the shock |
| `shock_description` | str | Optional shock description |

### Example Output

```
scenario_name                 factor_type    factor_id      shock_type            shock_value
Severe_Rate_Shock_2008_Style  yield_curve    CHF_SWAP       parallel_shift_bps    250
Severe_Rate_Shock_2008_Style  spread_curve   CHF_CORP_BBB   parallel_shift_bps    200
Severe_Rate_Shock_2008_Style  equity_index   SMI            multiplicative        0.70
```

---

## 🎯 Use Cases

### 1. Regulatory Stress Testing
```python
user_instruction = """
Generate scenarios for regulatory stress testing compliance:
1. Severe but plausible recession (BCBS guidelines)
2. Interest rate shock (±200 bps parallel)
3. Credit spread shock (+200 bps investment grade)
4. FX shock (±20% for major pairs)
"""
```

### 2. IRRBB (Interest Rate Risk in Banking Book)
```python
user_instruction = """
Generate interest rate scenarios for IRRBB analysis:
1. Parallel shift up (+200 bps)
2. Parallel shift down (-100 bps)
3. Steepener (short rates -100 bps, long rates +100 bps)
4. Flattener (short rates +100 bps, long rates -100 bps)
5. Short rate shock (±200 bps for maturities < 1Y)
"""
```

### 3. Climate Risk Scenarios
```python
user_instruction = """
Generate climate transition risk scenarios:
1. Orderly transition: Gradual carbon price increase
2. Disorderly transition: Sudden policy changes, asset stranding
3. Hot house world: Physical risks, no transition

Include impacts on:
- Energy sector credit spreads
- Carbon-intensive equity indices
- Green bond spreads
- Commodity prices (oil, gas, renewables)
"""
```

### 4. Geopolitical Scenarios
```python
user_instruction = """
Generate geopolitical stress scenarios:
1. Trade war escalation
2. Regional conflict affecting energy supply
3. Safe haven flows to CHF
4. Emerging market crisis

Ensure realistic correlations between FX, rates, and credit.
"""
```

---

## 🔍 Validation and Quality Checks

### Built-in Validations

The framework includes several quality checks:

1. **Factor ID Validation**: Ensures shocks reference valid risk factors
2. **JSON Schema Validation**: Verifies LLM output structure
3. **Shock Type Consistency**: Checks shock types match factor types
4. **Value Range Checks**: Can add custom validators for realistic ranges

### Adding Custom Validators

```python
def validate_scenarios(scenarios: List[Scenario], risk_factors: List[RiskFactor]) -> bool:
    """Custom validation logic"""
    factor_ids = {rf.factor_id for rf in risk_factors}
    
    for scenario in scenarios:
        for shock in scenario.shocks:
            # Check factor exists
            if shock.factor_id not in factor_ids:
                raise ValueError(f"Unknown factor: {shock.factor_id}")
            
            # Check shock magnitude is realistic
            if shock.shock_type == "parallel_shift_bps":
                if abs(shock.value) > 500:
                    raise ValueError(f"Unrealistic shock: {shock.value} bps")
    
    return True
```

---

## 🧪 Testing

### Unit Tests

```python
def test_yield_curve_creation():
    curve = YieldCurve(
        factor_id="TEST_CURVE",
        currency="CHF",
        tenors=["1Y", "2Y"],
        rates=[2.0, 2.5]
    )
    assert curve.factor_type == RiskFactorType.YIELD_CURVE
    assert len(curve.tenors) == 2

def test_prompt_builder():
    risk_factors, counterparties, contracts = create_sample_universe()
    prompt = PromptBuilder.build_prompt(
        risk_factors, counterparties, contracts,
        "Generate stress scenario", 3, "stress"
    )
    assert "CRITICAL INSTRUCTIONS" in prompt
    assert "JSON" in prompt

def test_scenario_parsing():
    mock_json = '{"scenarios": [{"name": "Test", "shocks": []}]}'
    scenarios = ScenarioParser.parse_llm_response(mock_json)
    assert len(scenarios) == 1
```

---

## 🛠️ Troubleshooting

### Issue: LLM returns invalid JSON

**Solution**: The prompt includes strict instructions, but LLMs can still fail. The parser attempts to extract JSON from surrounding text:

```python
# Already handled in ScenarioParser.parse_llm_response()
json_start = response_text.find('{')
json_end = response_text.rfind('}') + 1
json_text = response_text[json_start:json_end]
```

If this fails, try:
1. Lowering temperature (0.1-0.3)
2. Adding more examples to the prompt
3. Using a more capable model (llama3:70b or llama3.1:405b)

### Issue: Scenarios are unrealistic

**Solutions**:
1. Add more context in `user_instruction`
2. Include historical examples
3. Add validation constraints in the prompt
4. Implement post-processing validators

### Issue: LLM is too slow

**Solutions**:
1. Use quantized models (Q4, Q5)
2. Reduce `max_tokens` parameter
3. Use smaller models for simple scenarios
4. Consider GPU acceleration

---

## 📈 Performance Optimization

### Batch Processing

```python
def generate_scenario_library(themes: List[str]) -> pd.DataFrame:
    """Generate multiple scenario sets efficiently"""
    all_scenarios = []
    
    for theme in themes:
        scenarios, df = generator.generate_scenarios(
            risk_factors, counterparties, contracts,
            user_instruction=theme,
            num_scenarios=3
        )
        all_scenarios.append(df)
    
    return pd.concat(all_scenarios, ignore_index=True)

# Example usage
themes = [
    "Generate recession scenarios",
    "Generate inflation scenarios",
    "Generate geopolitical scenarios"
]
library = generate_scenario_library(themes)
```

### Caching

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_llm_call(prompt_hash: str, prompt: str) -> str:
    """Cache LLM responses by prompt hash"""
    return llm_client.call_llm(prompt)

# Usage
prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
response = cached_llm_call(prompt_hash, prompt)
```

---

## 🔐 Security Considerations

1. **Input Validation**: Sanitize user instructions to prevent prompt injection
2. **Output Validation**: Always validate LLM outputs before using in production
3. **API Security**: Use authentication for Open WebUI
4. **Data Privacy**: Ensure sensitive portfolio data is not logged

---

## 📚 References

- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Open WebUI Documentation](https://docs.openwebui.com/)
- [BCBS Stress Testing Principles](https://www.bis.org/publ/bcbs155.htm)
- [IRRBB Standards](https://www.bis.org/bcbs/publ/d368.htm)

---

## 🤝 Contributing

This framework is designed to be extensible. Common extension points:

1. **New Risk Factor Types**: Add to the data model
2. **Custom Shock Types**: Extend `ShockType` enum
3. **Alternative LLM Providers**: Implement new client classes
4. **Advanced Prompt Strategies**: Enhance `PromptBuilder`
5. **Scenario Validation**: Add custom validators

---

## 📄 License

This code is provided as-is for ALM risk management and quantitative finance applications.

---

## 🆘 Support

For questions or issues:
1. Check the troubleshooting section
2. Review the code comments and docstrings
3. Consult the Ollama/Open WebUI documentation
4. Validate your setup with the included demo

---

**Happy scenario generation! 🎲📊**
=======
# alm-scenario-generator-wsl



## Getting started

To make it easy for you to get started with GitLab, here's a list of recommended next steps.

Already a pro? Just edit this README.md and make it your own. Want to make it easy? [Use the template at the bottom](#editing-this-readme)!

## Add your files

- [ ] [Create](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#create-a-file) or [upload](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#upload-a-file) files
- [ ] [Add files using the command line](https://docs.gitlab.com/topics/git/add_files/#add-files-to-a-git-repository) or push an existing Git repository with the following command:

```
cd existing_repo
git remote add origin https://gitlab.uzh.ch/ioannis.akkizidis/alm-scenario-generator-wsl.git
git branch -M main
git push -uf origin main
```

## Integrate with your tools

- [ ] [Set up project integrations](https://gitlab.uzh.ch/ioannis.akkizidis/alm-scenario-generator-wsl/-/settings/integrations)

## Collaborate with your team

- [ ] [Invite team members and collaborators](https://docs.gitlab.com/ee/user/project/members/)
- [ ] [Create a new merge request](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)
- [ ] [Automatically close issues from merge requests](https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#closing-issues-automatically)
- [ ] [Enable merge request approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
- [ ] [Set auto-merge](https://docs.gitlab.com/user/project/merge_requests/auto_merge/)

## Test and Deploy

Use the built-in continuous integration in GitLab.

- [ ] [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/quick_start/)
- [ ] [Analyze your code for known vulnerabilities with Static Application Security Testing (SAST)](https://docs.gitlab.com/ee/user/application_security/sast/)
- [ ] [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/ee/topics/autodevops/requirements.html)
- [ ] [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/ee/user/clusters/agent/)
- [ ] [Set up protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

***

# Editing this README

When you're ready to make this README your own, just edit this file and use the handy template below (or feel free to structure it however you want - this is just a starting point!). Thanks to [makeareadme.com](https://www.makeareadme.com/) for this template.

## Suggestions for a good README

Every project is different, so consider which of these sections apply to yours. The sections used in the template are suggestions for most open source projects. Also keep in mind that while a README can be too long and detailed, too long is better than too short. If you think your README is too long, consider utilizing another form of documentation rather than cutting out information.

## Name
Choose a self-explaining name for your project.

## Description
Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

## Badges
On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Visuals
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Installation
Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support
Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
>>>>>>> 78015f287c11eec09776b4e5e5e5b8608c4cd51d
