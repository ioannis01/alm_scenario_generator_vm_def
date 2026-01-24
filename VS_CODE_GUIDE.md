# Visual Studio Code Setup Guide

## 📥 Quick Setup for VS Code

### Step 1: Download the Project

Download the entire `alm_scenario_generator` folder to your local machine.

### Step 2: Open in VS Code

```bash
# Open VS Code in the project directory
cd alm_scenario_generator
code .
```

### Step 3: Install Python Extension

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X or Cmd+Shift+X)
3. Search for "Python"
4. Install the official Python extension by Microsoft

### Step 4: Create Virtual Environment (Recommended)

```bash
# In VS Code terminal (Ctrl+` or Cmd+`)
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Run the Demo

```bash
python main.py
```

You should see the complete demo output!

---

## 🎨 Recommended VS Code Settings

Create `.vscode/settings.json` in the project root:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.analysis.typeCheckingMode": "basic",
    "editor.formatOnSave": true,
    "editor.rulers": [88],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/.pytest_cache": true
    }
}
```

Create `.vscode/launch.json` for debugging:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Main Demo",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "justMyCode": true
        }
    ]
}
```

---

## 🔍 Project Navigation in VS Code

### Quick File Navigation
- **Ctrl+P** (Cmd+P): Quick file open
- Type filename to jump to it

### Go to Definition
- **F12**: Go to definition
- **Ctrl+Click**: Jump to definition
- **Alt+F12**: Peek definition

### Find References
- **Shift+F12**: Find all references
- Right-click → "Find All References"

### Example Navigation Flow

```python
# In main.py, click on ALMScenarioGenerator
# Press F12 to jump to its definition in:
# alm_scenarios/generators/scenario_generator.py

# Click on LlamaClient, press F12 to go to:
# alm_scenarios/llm/client.py

# Click on YieldCurve, press F12 to go to:
# alm_scenarios/models/risk_factors.py
```

---

## 🐛 Debugging in VS Code

### Set Breakpoints
1. Click in the gutter (left of line numbers)
2. Red dot appears = breakpoint set

### Start Debugging
1. Press **F5** or click "Run and Debug"
2. Select "Python: Main Demo"
3. Execution will pause at breakpoints

### Debug Controls
- **F5**: Continue
- **F10**: Step over
- **F11**: Step into
- **Shift+F11**: Step out
- **Ctrl+Shift+F5**: Restart

### Inspect Variables
- Hover over variables to see values
- Use the Variables pane (left sidebar)
- Use the Debug Console to evaluate expressions

---

## 📦 Package Structure in VS Code

```
alm_scenario_generator/          ← Open this folder in VS Code
├── main.py                       ← Run this to start
├── config.py                     ← Configuration settings
├── requirements.txt              ← Dependencies
├── README.md                     ← Main documentation
├── INTEGRATION_GUIDE.md          ← Setup guide
│
└── alm_scenarios/                ← Main package
    ├── __init__.py               ← Package exports
    │
    ├── models/                   ← Data models
    │   ├── __init__.py
    │   ├── risk_factors.py       ← YieldCurve, SpreadCurve, etc.
    │   ├── counterparty.py       ← Counterparty model
    │   ├── contract.py           ← Contract model
    │   └── scenario.py           ← Scenario and Shock
    │
    ├── llm/                      ← LLM interface
    │   ├── __init__.py
    │   ├── client.py             ← LlamaClient (edit here for real API)
    │   └── prompt_builder.py     ← Prompt engineering
    │
    ├── parsers/                  ← Response parsing
    │   ├── __init__.py
    │   └── scenario_parser.py    ← JSON parser
    │
    ├── generators/               ← Main orchestration
    │   ├── __init__.py
    │   └── scenario_generator.py ← ALMScenarioGenerator
    │
    └── utils/                    ← Utilities
        ├── __init__.py
        └── sample_data.py        ← Sample data creation
```

---

## 💡 Usage Examples in VS Code

### Example 1: Import and Use

Create a new file `my_scenario_test.py`:

```python
from alm_scenarios import (
    ALMScenarioGenerator,
    LlamaClient,
    create_sample_universe
)

# VS Code will show autocomplete suggestions!
llm_client = LlamaClient(  # Ctrl+Space for autocomplete
    base_url="http://localhost:11434",
    model_name="llama3"
)

# Hover over functions to see docstrings
generator = ALMScenarioGenerator(llm_client)

# Load sample data
risk_factors, counterparties, contracts = create_sample_universe()

# Generate scenarios
scenarios, df = generator.generate_scenarios(
    risk_factors=risk_factors,
    counterparties=counterparties,
    contracts=contracts,
    user_instruction="Generate 3 stress scenarios"
)

print(df)
```

### Example 2: Add New Risk Factor

Edit `alm_scenarios/models/risk_factors.py`:

```python
@dataclass
class CommodityPrice(RiskFactor):
    """Commodity price risk factor"""
    commodity: str = field(default="")
    spot_price: float = field(default=0.0)
    unit: str = field(default="USD/barrel")
    
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

Then update `models/__init__.py` to export it:
```python
from .risk_factors import CommodityPrice

__all__ = [..., 'CommodityPrice']
```

---

## 🧪 Testing in VS Code

### Install pytest

```bash
pip install pytest pytest-cov
```

### Create Test File

Create `tests/test_models.py`:

```python
from alm_scenarios.models import YieldCurve

def test_yield_curve_creation():
    curve = YieldCurve(
        factor_id="TEST",
        currency="CHF",
        tenors=["1Y"],
        rates=[2.0]
    )
    assert curve.factor_id == "TEST"
    assert len(curve.tenors) == 1

def test_yield_curve_to_dict():
    curve = YieldCurve(
        factor_id="TEST",
        currency="CHF",
        tenors=["1Y", "2Y"],
        rates=[2.0, 2.5]
    )
    d = curve.to_dict()
    assert d["avg_rate"] == 2.25
```

### Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=alm_scenarios tests/

# Run in VS Code:
# Use Testing panel (flask icon in left sidebar)
```

---

## 🔧 Customization Workflow

### To Connect Real LLM:

1. Open `alm_scenarios/llm/client.py`
2. Find the `call_llm()` method
3. Uncomment the API call section:

```python
# BEFORE (line ~50):
return self._get_mock_response()

# AFTER:
response = requests.post(
    endpoint,
    json=payload,
    timeout=self.timeout
)
response.raise_for_status()
return response.json()["response"]
```

### To Load Your ALM Data:

1. Open `alm_scenarios/utils/sample_data.py`
2. Create a new function:

```python
def load_from_database():
    """Load from your ALM database"""
    import psycopg2
    
    conn = psycopg2.connect("your_connection_string")
    # ... load data
    return risk_factors, counterparties, contracts
```

3. Use in `main.py`:

```python
from alm_scenarios.utils import load_from_database

risk_factors, counterparties, contracts = load_from_database()
```

---

## 🎯 Keyboard Shortcuts Summary

| Action | Windows/Linux | Mac |
|--------|---------------|-----|
| Quick Open | Ctrl+P | Cmd+P |
| Command Palette | Ctrl+Shift+P | Cmd+Shift+P |
| Go to Definition | F12 | F12 |
| Find References | Shift+F12 | Shift+F12 |
| Toggle Terminal | Ctrl+` | Cmd+` |
| Run Python File | Ctrl+F5 | Cmd+F5 |
| Start Debugging | F5 | F5 |
| Format Document | Shift+Alt+F | Shift+Opt+F |

---

## ✅ Verification Checklist

- [ ] VS Code installed
- [ ] Python extension installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Can run `python main.py` successfully
- [ ] Autocomplete works (try typing `from alm_scenarios import ` and see suggestions)
- [ ] Can navigate with F12 (Go to Definition)
- [ ] Can set breakpoints and debug

---

## 🆘 Troubleshooting

### "Module not found" error
```bash
# Make sure you're in the project root
cd alm_scenario_generator

# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### Autocomplete not working
1. Reload VS Code window (Ctrl+Shift+P → "Reload Window")
2. Select Python interpreter (Ctrl+Shift+P → "Python: Select Interpreter")
3. Choose the venv interpreter

### Import errors
- Make sure you're running from the project root
- Check that `__init__.py` files exist in all package directories

---

**You're all set up! Happy coding in VS Code! 🚀**
