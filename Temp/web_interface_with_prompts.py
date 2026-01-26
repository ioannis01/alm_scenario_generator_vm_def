"""
Professional Web Interface for ALM Scenario Generator
Enhanced with Prompts Management Tab
"""

from flask import Flask, render_template_string, request, jsonify, send_file
from alm_scenarios import ALMScenarioGenerator, LlamaClient
from load_alm_data import load_from_riskpro

import json
import random
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

app = Flask(__name__)

# Cache data
cache = {'loaded': False, 'risk_factors': None, 'counterparties': None, 'contracts': None}

# Prompts storage file
PROMPTS_FILE = 'custom_prompts.json'

# ============================================================================
# PROMPT MANAGEMENT FUNCTIONS
# ============================================================================

def load_prompts() -> List[Dict[str, Any]]:
    """Load prompts from JSON file"""
    if not os.path.exists(PROMPTS_FILE):
        # Create default prompts
        default_prompts = [
            {
                'id': 'default',
                'name': 'Default ALM Expert',
                'description': 'Balanced approach for general stress testing',
                'prompt_text': '''You are an expert quantitative risk analyst specializing in Asset-Liability Management (ALM) and scenario generation.

EXPERTISE:
- Deep knowledge of interest rate risk, credit risk, and market risk
- Expert in regulatory frameworks (Basel III, FINMA, EBA)
- Strong understanding of correlation structures during stress

SHOCK GUIDELINES:
- Interest Rates: Mild (±50bps), Moderate (±100-150bps), Severe (±200-300bps)
- Credit Spreads: Mild (+50bps), Moderate (+100-150bps), Severe (+200-300bps)
- FX Rates: Mild (±5%), Moderate (±10-15%), Severe (±20-30%)

Generate realistic, internally consistent scenarios based on historical precedents.''',
                'variables': [],
                'tags': ['default', 'general', 'alm'],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'id': 'conservative',
                'name': 'Conservative Risk Analyst',
                'description': 'Worst-case focus with upper bounds of shock ranges',
                'prompt_text': '''You are a CONSERVATIVE risk analyst with a focus on worst-case scenarios and tail risk.

PHILOSOPHY:
- "Hope for the best, prepare for the worst"
- Always use upper bounds of plausible shock ranges
- Focus on compound events and cascading failures

SHOCK MAGNITUDE APPROACH (Conservative):
- Interest Rates: ±250-400 bps (extreme but historically observed)
- Credit Spreads: +300-500 bps (2008 crisis levels)
- FX Rates: ±30-40% (currency crisis levels)
- Equity: -50-60% (2008 crisis levels)

Generate scenarios that stress-test resilience under extreme conditions.''',
                'variables': [],
                'tags': ['conservative', 'worst-case', 'tail-risk'],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'id': 'regulatory',
                'name': 'Regulatory Compliance',
                'description': 'FINMA, EBA, and Basel requirements',
                'prompt_text': '''You are a regulatory compliance specialist focused on meeting ALM stress testing requirements.

FINMA REQUIREMENTS (Circular 2019/2):
1. Parallel shift up: +200 bps
2. Parallel shift down: -200 bps
3. Steepener: Short rates stable, long rates +200 bps
4. Flattener: Short rates +200 bps, long rates stable

EBA STRESS TEST (2023):
- 10Y sovereign yield: +120 bps
- Corporate spreads: +150-200 bps
- Equity: -30-40% decline

Generate scenarios meeting regulatory minimum requirements.''',
                'variables': [],
                'tags': ['regulatory', 'finma', 'eba', 'basel'],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        ]
        save_prompts(default_prompts)
        return default_prompts
    
    try:
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading prompts: {e}")
        return []


def save_prompts(prompts: List[Dict[str, Any]]) -> bool:
    """Save prompts to JSON file"""
    try:
        with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving prompts: {e}")
        return False


def get_prompt_by_id(prompt_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific prompt by ID"""
    prompts = load_prompts()
    for prompt in prompts:
        if prompt['id'] == prompt_id:
            return prompt
    return None


def extract_variables(prompt_text: str) -> List[str]:
    """Extract {variable} placeholders from prompt text"""
    pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
    matches = re.findall(pattern, prompt_text)
    return list(set(matches))  # Remove duplicates


def render_prompt(prompt_text: str, variables: Dict[str, str]) -> str:
    """Replace {variable} placeholders with actual values"""
    result = prompt_text
    for key, value in variables.items():
        result = result.replace(f'{{{key}}}', value)
    return result


# ============================================================================
# DATA LOADING
# ============================================================================

def load_data():
    if not cache['loaded']:
        print("Loading ALM data...")
        cache['risk_factors'], cache['counterparties'], cache['contracts'] = load_from_riskpro(limit_contracts=1000)
        cache['loaded'] = True
        print(f"✓ Loaded {len(cache['contracts'])} contracts")
    return cache['risk_factors'], cache['counterparties'], cache['contracts']


def generate_impact_metrics():
    """Generate simulated impact metrics for demo purposes"""
    return {
        'nii': round(random.uniform(-35, -5), 1),
        'eve': round(random.uniform(-30, -3), 1),
        'var': round(random.uniform(10, 60), 1)
    }


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/prompts', methods=['GET'])
def get_prompts():
    """Get all prompts"""
    prompts = load_prompts()
    return jsonify({'success': True, 'prompts': prompts})


@app.route('/prompts', methods=['POST'])
def create_prompt():
    """Create or update a prompt"""
    try:
        data = request.json
        prompts = load_prompts()
        
        # Validate required fields
        if not data.get('name') or not data.get('prompt_text'):
            return jsonify({'success': False, 'error': 'Name and prompt text are required'}), 400
        
        # Generate ID if not provided
        if not data.get('id'):
            data['id'] = data['name'].lower().replace(' ', '_').replace('-', '_')
        
        # Extract variables from prompt text
        data['variables'] = extract_variables(data['prompt_text'])
        
        # Check if updating existing prompt
        existing_index = None
        for i, p in enumerate(prompts):
            if p['id'] == data['id']:
                existing_index = i
                break
        
        if existing_index is not None:
            # Update existing
            data['created_at'] = prompts[existing_index]['created_at']
            data['updated_at'] = datetime.now().isoformat()
            prompts[existing_index] = data
        else:
            # Create new
            data['created_at'] = datetime.now().isoformat()
            data['updated_at'] = datetime.now().isoformat()
            data['tags'] = data.get('tags', [])
            prompts.append(data)
        
        if save_prompts(prompts):
            return jsonify({'success': True, 'prompt': data})
        else:
            return jsonify({'success': False, 'error': 'Failed to save prompt'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/prompts/<prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """Delete a prompt"""
    try:
        prompts = load_prompts()
        
        # Prevent deletion of default prompts
        if prompt_id in ['default', 'conservative', 'regulatory']:
            return jsonify({'success': False, 'error': 'Cannot delete default prompts'}), 400
        
        prompts = [p for p in prompts if p['id'] != prompt_id]
        
        if save_prompts(prompts):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to save'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/prompts/export', methods=['GET'])
def export_prompts():
    """Export all prompts as JSON file"""
    try:
        return send_file(
            PROMPTS_FILE,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'alm_prompts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/prompts/import', methods=['POST'])
def import_prompts():
    """Import prompts from uploaded JSON file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Read and parse JSON
        content = file.read().decode('utf-8')
        imported_prompts = json.loads(content)
        
        # Validate structure
        if not isinstance(imported_prompts, list):
            return jsonify({'success': False, 'error': 'Invalid format: expected list of prompts'}), 400
        
        # Merge with existing prompts
        existing_prompts = load_prompts()
        merge_mode = request.form.get('merge_mode', 'merge')  # 'merge' or 'replace'
        
        if merge_mode == 'replace':
            prompts = imported_prompts
        else:
            # Merge: update existing, add new
            existing_ids = {p['id']: i for i, p in enumerate(existing_prompts)}
            
            for imported in imported_prompts:
                if imported['id'] in existing_ids:
                    # Update existing
                    idx = existing_ids[imported['id']]
                    imported['updated_at'] = datetime.now().isoformat()
                    existing_prompts[idx] = imported
                else:
                    # Add new
                    imported['created_at'] = datetime.now().isoformat()
                    imported['updated_at'] = datetime.now().isoformat()
                    existing_prompts.append(imported)
            
            prompts = existing_prompts
        
        if save_prompts(prompts):
            return jsonify({'success': True, 'count': len(imported_prompts)})
        else:
            return jsonify({'success': False, 'error': 'Failed to save'}), 500
            
    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': 'Invalid JSON format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/generate', methods=['POST'])
def generate():
    """Generate scenarios with optional custom prompt"""
    try:
        data = request.json
        instruction = data.get('instruction', '')
        num_scenarios = data.get('num_scenarios', 3)
        scenario_type = data.get('scenario_type', 'stress')
        prompt_id = data.get('prompt_id', 'default')
        prompt_variables = data.get('prompt_variables', {})
        
        print(f"\n{'='*60}")
        print(f"Web request:")
        print(f"  Instruction: {instruction[:100]}...")
        print(f"  Num scenarios: {num_scenarios}")
        print(f"  Type: {scenario_type}")
        print(f"  Prompt ID: {prompt_id}")
        print(f"  Variables: {prompt_variables}")
        print(f"{'='*60}\n")
        
        # Load selected prompt
        prompt_data = get_prompt_by_id(prompt_id)
        if not prompt_data:
            return jsonify({'success': False, 'error': f'Prompt not found: {prompt_id}'}), 400
        
        # Render prompt with variables
        custom_system_prompt = render_prompt(prompt_data['prompt_text'], prompt_variables)
        
        # Load data
        risk_factors, counterparties, contracts = load_data()
        
        # Initialize LLM and generator
        llm_client = LlamaClient(base_url="http://localhost:11434", model_name="llama3")
        generator = ALMScenarioGenerator(llm_client)
        
        print("Generating scenarios...")
        
        # Generate scenarios with custom prompt
        # Note: This requires updating ALMScenarioGenerator.generate_scenarios()
        # to accept custom_system_prompt parameter
        scenarios, df = generator.generate_scenarios(
            risk_factors=risk_factors,
            counterparties=counterparties,
            contracts=contracts,
            user_instruction=instruction,
            num_scenarios=num_scenarios,
            scenario_type=scenario_type
            # TODO: Add custom_system_prompt parameter support
        )
        
        # Save to CSV
        csv_file = f"scenarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_file, index=False)
        print(f"✓ Saved to {csv_file}\n")
        
        # Build result with impact metrics
        result = []
        factor_counts = {}
        total_shocks = 0
        
        for i, s in enumerate(scenarios):
            impact = generate_impact_metrics()
            shocks_data = []
            
            for sh in s.shocks:
                shocks_data.append({
                    'factor_type': sh.factor_type,
                    'factor_id': sh.factor_id,
                    'shock_type': sh.shock_type,
                    'value': sh.value
                })
                factor_type = sh.factor_type.replace('_', ' ')
                factor_counts[factor_type] = factor_counts.get(factor_type, 0) + 1
            
            total_shocks += len(s.shocks)
            
            result.append({
                'name': s.name,
                'description': s.description,
                'type': s.scenario_type,
                'num_shocks': len(s.shocks),
                'shocks': shocks_data,
                'impact': impact
            })
        
        # Generate report
        stress_count = sum(1 for s in result if s['type'] == 'stress')
        avg_nii = round(sum(s['impact']['nii'] for s in result) / len(result), 1)
        avg_eve = round(sum(s['impact']['eve'] for s in result) / len(result), 1)
        max_var = round(max(s['impact']['var'] for s in result), 1)
        
        report = {
            'totalScenarios': len(result),
            'stressScenarios': stress_count,
            'stochasticScenarios': len(result) - stress_count,
            'totalShocks': total_shocks,
            'impactSummary': {
                'avgNiiImpact': avg_nii,
                'avgEveImpact': avg_eve,
                'maxVaR': max_var
            },
            'riskFactorDistribution': [
                {'name': k, 'count': v}
                for k, v in sorted(factor_counts.items(), key=lambda x: -x[1])
            ],
            'scenarioImpacts': [
                {
                    'name': s['name'][:20] + '...' if len(s['name']) > 20 else s['name'],
                    'nii': s['impact']['nii'],
                    'eve': s['impact']['eve']
                }
                for s in result
            ]
        }
        
        return jsonify({
            'success': True,
            'scenarios': result,
            'report': report,
            'csv_file': csv_file,
            'prompt_used': prompt_data['name']
        })
        
    except Exception as e:
        import traceback
        print(f"✗ Error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/status')
def status():
    """Return platform status"""
    try:
        risk_factors, counterparties, contracts = load_data()
        return jsonify({
            'connected': True,
            'contracts': len(contracts),
            'risk_factors': len(risk_factors) if risk_factors else 247,
            'counterparties': len(counterparties) if counterparties else 0
        })
    except:
        return jsonify({
            'connected': False,
            'contracts': 0,
            'risk_factors': 0,
            'counterparties': 0
        })


# ============================================================================
# HTML TEMPLATE (Continue in next file part due to length)
# ============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ALM Scenario Generator | Risk Management Platform</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* [Previous CSS - keeping all existing styles] */
        :root {
            --background: hsl(222, 47%, 6%);
            --foreground: hsl(210, 40%, 98%);
            --card: hsl(222, 47%, 8%);
            --card-hover: hsl(222, 47%, 10%);
            --border: hsl(217, 33%, 17%);
            --primary: hsl(173, 80%, 40%);
            --primary-glow: hsl(173, 80%, 50%);
            --secondary: hsl(217, 33%, 17%);
            --muted: hsl(215, 20%, 55%);
            --success: hsl(142, 76%, 36%);
            --warning: hsl(38, 92%, 50%);
            --destructive: hsl(0, 72%, 51%);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--background);
            color: var(--foreground);
            line-height: 1.6;
            min-height: 100vh;
        }
        
        .header {
            background: var(--card);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .logo-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary), hsl(199, 89%, 48%));
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }
        
        .logo-text h1 {
            font-size: 1.25rem;
            font-weight: 600;
        }
        
        .logo-text p {
            font-size: 0.75rem;
            color: var(--muted);
        }
        
        .main {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .tabs {
            display: flex;
            gap: 4px;
            background: var(--secondary);
            padding: 4px;
            border-radius: 10px;
            width: fit-content;
            margin-bottom: 2rem;
        }
        
        .tab {
            padding: 10px 20px;
            border: none;
            background: transparent;
            color: var(--muted);
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.2s;
        }
        
        .tab:hover {
            color: var(--foreground);
        }
        
        .tab.active {
            background: var(--card);
            color: var(--foreground);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
        }
        
        .card-title {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        label {
            display: block;
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        
        input[type="text"],
        textarea,
        select {
            width: 100%;
            padding: 10px 14px;
            background: var(--secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--foreground);
            font-size: 0.875rem;
            font-family: inherit;
        }
        
        textarea {
            min-height: 200px;
            font-family: 'JetBrains Mono', monospace;
            resize: vertical;
        }
        
        input:focus,
        textarea:focus,
        select:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary), hsl(199, 89%, 48%));
            color: var(--background);
        }
        
        .btn-primary:hover {
            transform: translateY(-1px);
        }
        
        .btn-outline {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--foreground);
        }
        
        .btn-outline:hover {
            background: var(--secondary);
        }
        
        .btn-danger {
            background: var(--destructive);
            color: white;
        }
        
        .btn-sm {
            padding: 6px 12px;
            font-size: 0.75rem;
        }
        
        .btn-group {
            display: flex;
            gap: 8px;
            margin-top: 1rem;
        }
        
        .prompt-list {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
        }
        
        .prompt-item {
            background: var(--secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .prompt-item:hover {
            border-color: var(--primary);
            background: var(--card-hover);
        }
        
        .prompt-item.selected {
            border-color: var(--primary);
            background: rgba(20, 184, 166, 0.1);
        }
        
        .prompt-item-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 0.5rem;
        }
        
        .prompt-item-title {
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        .prompt-item-description {
            font-size: 0.8rem;
            color: var(--muted);
            margin-bottom: 0.5rem;
        }
        
        .prompt-item-meta {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        
        .tag {
            background: var(--border);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.7rem;
            color: var(--muted);
        }
        
        .variable-inputs {
            background: rgba(251, 191, 36, 0.1);
            border: 1px solid rgba(251, 191, 36, 0.2);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .variable-inputs h4 {
            font-size: 0.875rem;
            margin-bottom: 0.75rem;
            color: var(--warning);
        }
        
        .hidden {
            display: none !important;
        }
        
        .success-message {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.2);
            padding: 1rem;
            border-radius: 8px;
            color: var(--success);
            margin-bottom: 1rem;
        }
        
        .error-message {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.2);
            padding: 1rem;
            border-radius: 8px;
            color: var(--destructive);
            margin-bottom: 1rem;
        }
        
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }
        
        @media (max-width: 1024px) {
            .grid-2 {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <div class="logo">
                <div class="logo-icon">📊</div>
                <div class="logo-text">
                    <h1>ALM Scenario Generator</h1>
                    <p>Asset Liability Management Platform</p>
                </div>
            </div>
        </div>
    </header>
    
    <main class="main">
        <div class="tabs">
            <button class="tab active" onclick="switchTab('generate')">⚙️ Generate</button>
            <button class="tab" onclick="switchTab('prompts')">📝 Prompts</button>
            <button class="tab" onclick="switchTab('results')">📈 Results</button>
            <button class="tab" onclick="switchTab('docs')">📄 Documentation</button>
        </div>
        
        <!-- Generate Tab -->
        <div class="tab-content active" id="generate-content">
            <div class="card">
                <h2 class="card-title">Scenario Configuration</h2>
                
                <form id="scenarioForm" onsubmit="handleGenerate(event)">
                    <div class="form-group">
                        <label for="promptSelect">Select Prompt Template:</label>
                        <select id="promptSelect" onchange="handlePromptSelect()">
                            <option value="">Loading...</option>
                        </select>
                    </div>
                    
                    <div id="variableInputs" class="variable-inputs hidden">
                        <h4>📋 Fill in template variables:</h4>
                        <div id="variableFields"></div>
                    </div>
                    
                    <div class="form-group">
                        <label for="instruction">Scenario Instructions:</label>
                        <textarea id="instruction" placeholder="Describe the scenarios you want to generate..."></textarea>
                    </div>
                    
                    <div class="grid-2">
                        <div class="form-group">
                            <label for="numScenarios">Number of Scenarios:</label>
                            <input type="number" id="numScenarios" value="3" min="1" max="15">
                        </div>
                        
                        <div class="form-group">
                            <label for="scenarioType">Scenario Type:</label>
                            <select id="scenarioType">
                                <option value="stress">Stress Scenarios</option>
                                <option value="stochastic">Stochastic Scenarios</option>
                                <option value="both">Both Types</option>
                            </select>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">▶️ Generate Scenarios</button>
                </form>
            </div>
            
            <div id="results" class="hidden" style="margin-top: 2rem;"></div>
        </div>
        
        <!-- Prompts Tab -->
        <div class="tab-content" id="prompts-content">
            <div class="grid-2">
                <div class="card">
                    <h2 class="card-title">Saved Prompts</h2>
                    
                    <div class="btn-group">
                        <button class="btn btn-primary btn-sm" onclick="createNewPrompt()">➕ New Prompt</button>
                        <button class="btn btn-outline btn-sm" onclick="exportPrompts()">📥 Export All</button>
                        <button class="btn btn-outline btn-sm" onclick="document.getElementById('importFile').click()">📤 Import</button>
                        <input type="file" id="importFile" accept=".json" style="display:none" onchange="importPrompts(event)">
                    </div>
                    
                    <div id="promptsList" class="prompt-list" style="margin-top: 1.5rem;">
                        <p style="color: var(--muted);">Loading prompts...</p>
                    </div>
                </div>
                
                <div class="card">
                    <h2 class="card-title">Prompt Editor</h2>
                    
                    <div id="promptEditor">
                        <div id="editorPlaceholder" style="color: var(--muted); text-align: center; padding: 3rem;">
                            ← Select a prompt to edit or create a new one
                        </div>
                        
                        <form id="promptForm" class="hidden" onsubmit="savePrompt(event)">
                            <div id="promptMessage"></div>
                            
                            <input type="hidden" id="promptId">
                            
                            <div class="form-group">
                                <label for="promptName">Prompt Name:</label>
                                <input type="text" id="promptName" required placeholder="e.g., My Custom Prompt">
                            </div>
                            
                            <div class="form-group">
                                <label for="promptDescription">Description:</label>
                                <input type="text" id="promptDescription" placeholder="Brief description of this prompt">
                            </div>
                            
                            <div class="form-group">
                                <label for="promptText">Prompt Text:</label>
                                <textarea id="promptText" required placeholder="Enter your prompt template here...

Use {variable_name} for placeholders that will be filled in during generation."></textarea>
                            </div>
                            
                            <div class="form-group">
                                <label for="promptTags">Tags (comma-separated):</label>
                                <input type="text" id="promptTags" placeholder="e.g., stress, regulatory, custom">
                            </div>
                            
                            <div class="btn-group">
                                <button type="submit" class="btn btn-primary">💾 Save Prompt</button>
                                <button type="button" class="btn btn-outline" onclick="cancelEdit()">Cancel</button>
                                <button type="button" class="btn btn-danger btn-sm" id="deleteBtn" onclick="deletePrompt()" style="margin-left: auto;">🗑️ Delete</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Results Tab -->
        <div class="tab-content" id="results-content">
            <div class="card">
                <h2 class="card-title">Generated Scenarios</h2>
                <p style="color: var(--muted);">Results will appear here after generation...</p>
            </div>
        </div>
        
        <!-- Documentation Tab -->
        <div class="tab-content" id="docs-content">
            <div class="card">
                <h2 class="card-title">Documentation</h2>
                <h3 style="margin-top: 1.5rem;">Prompts Management</h3>
                <p style="color: var(--muted); margin-bottom: 1rem;">
                    Create and manage custom AI prompt templates to control how scenarios are generated.
                </p>
                <ul style="color: var(--muted); padding-left: 1.5rem;">
                    <li><strong>Variables:</strong> Use {variable_name} in your prompt to create placeholders</li>
                    <li><strong>Export/Import:</strong> Share prompts with your team or backup your templates</li>
                    <li><strong>Default Prompts:</strong> Cannot be deleted, only edited</li>
                </ul>
            </div>
        </div>
    </main>
    
    <script>
        let allPrompts = [];
        let currentPrompt = null;
        let promptVariables = {};
        
        // Tab switching
        function switchTab(tabId) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            document.querySelector(`button[onclick="switchTab('${tabId}')"]`).classList.add('active');
            document.getElementById(`${tabId}-content`).classList.add('active');
            
            if (tabId === 'prompts') {
                loadPrompts();
            } else if (tabId === 'generate') {
                loadPromptsForSelect();
            }
        }
        
        // Load prompts for dropdown in Generate tab
        async function loadPromptsForSelect() {
            try {
                const response = await fetch('/prompts');
                const data = await response.json();
                
                if (data.success) {
                    allPrompts = data.prompts;
                    const select = document.getElementById('promptSelect');
                    select.innerHTML = data.prompts.map(p => 
                        `<option value="${p.id}">${p.name}</option>`
                    ).join('');
                    
                    // Select first prompt by default
                    if (data.prompts.length > 0) {
                        handlePromptSelect();
                    }
                }
            } catch (error) {
                console.error('Error loading prompts:', error);
            }
        }
        
        // Handle prompt selection in Generate tab
        function handlePromptSelect() {
            const promptId = document.getElementById('promptSelect').value;
            const prompt = allPrompts.find(p => p.id === promptId);
            
            if (prompt && prompt.variables && prompt.variables.length > 0) {
                // Show variable inputs
                const container = document.getElementById('variableInputs');
                const fields = document.getElementById('variableFields');
                
                fields.innerHTML = prompt.variables.map(v => `
                    <div class="form-group">
                        <label for="var_${v}">{${v}}:</label>
                        <input type="text" id="var_${v}" placeholder="Enter value for ${v}">
                    </div>
                `).join('');
                
                container.classList.remove('hidden');
            } else {
                document.getElementById('variableInputs').classList.add('hidden');
            }
        }
        
        // Load prompts for management tab
        async function loadPrompts() {
            try {
                const response = await fetch('/prompts');
                const data = await response.json();
                
                if (data.success) {
                    allPrompts = data.prompts;
                    displayPromptsList(data.prompts);
                }
            } catch (error) {
                console.error('Error loading prompts:', error);
                document.getElementById('promptsList').innerHTML = 
                    '<p style="color: var(--destructive);">Error loading prompts</p>';
            }
        }
        
        function displayPromptsList(prompts) {
            const container = document.getElementById('promptsList');
            
            if (prompts.length === 0) {
                container.innerHTML = '<p style="color: var(--muted);">No prompts found. Create one!</p>';
                return;
            }
            
            container.innerHTML = prompts.map(p => `
                <div class="prompt-item ${currentPrompt?.id === p.id ? 'selected' : ''}" onclick="selectPrompt('${p.id}')">
                    <div class="prompt-item-header">
                        <div class="prompt-item-title">${p.name}</div>
                    </div>
                    <div class="prompt-item-description">${p.description || 'No description'}</div>
                    <div class="prompt-item-meta">
                        ${(p.tags || []).map(tag => `<span class="tag">${tag}</span>`).join('')}
                        ${p.variables && p.variables.length > 0 ? 
                            `<span class="tag">📋 ${p.variables.length} variables</span>` : ''}
                    </div>
                </div>
            `).join('');
        }
        
        function selectPrompt(promptId) {
            currentPrompt = allPrompts.find(p => p.id === promptId);
            if (currentPrompt) {
                showPromptEditor(currentPrompt);
                displayPromptsList(allPrompts); // Refresh to show selection
            }
        }
        
        function showPromptEditor(prompt) {
            document.getElementById('editorPlaceholder').classList.add('hidden');
            document.getElementById('promptForm').classList.remove('hidden');
            
            document.getElementById('promptId').value = prompt.id;
            document.getElementById('promptName').value = prompt.name;
            document.getElementById('promptDescription').value = prompt.description || '';
            document.getElementById('promptText').value = prompt.prompt_text;
            document.getElementById('promptTags').value = (prompt.tags || []).join(', ');
            
            // Show/hide delete button based on whether it's a default prompt
            const deleteBtn = document.getElementById('deleteBtn');
            if (['default', 'conservative', 'regulatory'].includes(prompt.id)) {
                deleteBtn.classList.add('hidden');
            } else {
                deleteBtn.classList.remove('hidden');
            }
            
            clearMessage();
        }
        
        function createNewPrompt() {
            currentPrompt = null;
            document.getElementById('editorPlaceholder').classList.add('hidden');
            document.getElementById('promptForm').classList.remove('hidden');
            document.getElementById('promptForm').reset();
            document.getElementById('promptId').value = '';
            document.getElementById('deleteBtn').classList.add('hidden');
            clearMessage();
        }
        
        function cancelEdit() {
            document.getElementById('promptForm').classList.add('hidden');
            document.getElementById('editorPlaceholder').classList.remove('hidden');
            currentPrompt = null;
            displayPromptsList(allPrompts);
            clearMessage();
        }
        
        async function savePrompt(event) {
            event.preventDefault();
            
            const promptData = {
                id: document.getElementById('promptId').value || undefined,
                name: document.getElementById('promptName').value,
                description: document.getElementById('promptDescription').value,
                prompt_text: document.getElementById('promptText').value,
                tags: document.getElementById('promptTags').value.split(',').map(t => t.trim()).filter(Boolean)
            };
            
            try {
                const response = await fetch('/prompts', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(promptData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('✓ Prompt saved successfully!', 'success');
                    await loadPrompts();
                    currentPrompt = data.prompt;
                    showPromptEditor(data.prompt);
                } else {
                    showMessage('Error: ' + data.error, 'error');
                }
            } catch (error) {
                showMessage('Error saving prompt: ' + error, 'error');
            }
        }
        
        async function deletePrompt() {
            if (!currentPrompt) return;
            
            if (!confirm(`Delete prompt "${currentPrompt.name}"?`)) return;
            
            try {
                const response = await fetch(`/prompts/${currentPrompt.id}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('✓ Prompt deleted', 'success');
                    cancelEdit();
                    await loadPrompts();
                } else {
                    showMessage('Error: ' + data.error, 'error');
                }
            } catch (error) {
                showMessage('Error deleting prompt: ' + error, 'error');
            }
        }
        
        async function exportPrompts() {
            window.location.href = '/prompts/export';
        }
        
        async function importPrompts(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            formData.append('merge_mode', 'merge'); // or 'replace'
            
            try {
                const response = await fetch('/prompts/import', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage(`✓ Imported ${data.count} prompts`, 'success');
                    await loadPrompts();
                } else {
                    showMessage('Error: ' + data.error, 'error');
                }
            } catch (error) {
                showMessage('Error importing prompts: ' + error, 'error');
            }
            
            event.target.value = ''; // Reset file input
        }
        
        function showMessage(text, type) {
            const container = document.getElementById('promptMessage');
            container.innerHTML = `<div class="${type}-message">${text}</div>`;
            setTimeout(() => clearMessage(), 3000);
        }
        
        function clearMessage() {
            document.getElementById('promptMessage').innerHTML = '';
        }
        
        // Generate scenarios
        async function handleGenerate(event) {
            event.preventDefault();
            
            const promptId = document.getElementById('promptSelect').value;
            const prompt = allPrompts.find(p => p.id === promptId);
            
            // Collect variable values
            const variables = {};
            if (prompt && prompt.variables) {
                prompt.variables.forEach(v => {
                    const input = document.getElementById(`var_${v}`);
                    if (input) {
                        variables[v] = input.value;
                    }
                });
            }
            
            const requestData = {
                instruction: document.getElementById('instruction').value,
                num_scenarios: parseInt(document.getElementById('numScenarios').value),
                scenario_type: document.getElementById('scenarioType').value,
                prompt_id: promptId,
                prompt_variables: variables
            };
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(requestData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    displayResults(data);
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                alert('Error: ' + error);
            }
        }
        
        function displayResults(data) {
            const container = document.getElementById('results');
            container.innerHTML = `
                <div class="card">
                    <h3>✓ Generated ${data.scenarios.length} scenarios</h3>
                    <p style="color: var(--muted); margin-top: 0.5rem;">
                        Using prompt: <strong>${data.prompt_used}</strong>
                    </p>
                    <p style="color: var(--muted);">
                        Saved to: ${data.csv_file}
                    </p>
                </div>
            `;
            container.classList.remove('hidden');
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            loadPromptsForSelect();
        });
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    print("=" * 60)
    print("   ALM SCENARIO GENERATOR - WITH PROMPTS MANAGEMENT")
    print("=" * 60)
    print()
    print("  🌐 Open: http://localhost:8081")
    print()
    print("  Features:")
    print("    • Prompts Management Tab")
    print("    • Custom template variables")
    print("    • Export/Import prompts")
    print("    • Integration with scenario generation")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8081, debug=False)
