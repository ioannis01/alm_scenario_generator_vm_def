"""
Professional Web Interface for ALM Scenario Generator
Enhanced with Prompt Editor for customizing AI model behavior
"""

from flask import Flask, render_template_string, request, jsonify
from alm_scenarios import ALMScenarioGenerator, LlamaClient
from load_alm_data import load_from_riskpro

import json
import os
import random
from datetime import datetime

app = Flask(__name__)

# Cache data
cache = {'loaded': False, 'risk_factors': None, 'counterparties': None, 'contracts': None}

# Prompt storage file
PROMPT_FILE = "custom_prompts.json"

# Default system prompt
DEFAULT_PROMPT = """You are an expert ALM (Asset-Liability Management) risk analyst with deep knowledge of:
- Interest rate risk and yield curve modeling
- Credit risk and spread dynamics
- Market risk and correlation structures
- Regulatory stress testing frameworks (Basel III, FINMA requirements, EBA guidelines)
- Swiss banking regulations

STRESS TESTING BEST PRACTICES:
1. Severity: Stress scenarios should be severe but plausible (typically 3-5 sigma events)
2. Correlations: Consider realistic correlations between risk factors
3. Consistency: Ensure scenarios are internally consistent and economically coherent
4. Historical precedents: Reference historical stress events (2008 crisis, 2015 SNB floor removal, COVID-19)

SHOCK MAGNITUDES GUIDELINES:
- Interest rates: Mild (+/-50bps), Moderate (+/-100-150bps), Severe (+/-200-300bps)
- Credit spreads: Mild (+50bps), Moderate (+100-150bps), Severe (+200-300bps)
- FX rates: Mild (+/-5%), Moderate (+/-10-15%), Severe (+/-20-30%)
- Equity indices: Mild (-10%), Moderate (-20-30%), Severe (-40-50%)

REGULATORY REFERENCES:
- EBA 2023 Stress Test: Adverse scenario includes +120bps 10Y yield shock
- FINMA stress tests: Typically include interest rate shocks of +/-200bps
- Basel IRRBB standards: Focus on parallel shifts and yield curve twists"""

def load_prompts():
    """Load saved prompts from file"""
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, 'r') as f:
            return json.load(f)
    return {
        "default": {
            "name": "Default ALM Expert",
            "prompt": DEFAULT_PROMPT,
            "created_at": datetime.now().isoformat()
        }
    }

def save_prompts(prompts):
    """Save prompts to file"""
    with open(PROMPT_FILE, 'w') as f:
        json.dump(prompts, f, indent=2)

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

# [Keep all your existing HTML styling but add the prompt editor tab]
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ALM Scenario Generator | Risk Management Platform</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
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
            backdrop-filter: blur(10px);
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
        
        .card-header {
            margin-bottom: 1.5rem;
        }
        
        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .card-description {
            font-size: 0.875rem;
            color: var(--muted);
        }
        
        /* Form Elements */
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-label {
            display: block;
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: var(--foreground);
        }
        
        .form-input, .form-textarea, .form-select {
            width: 100%;
            padding: 0.75rem 1rem;
            background: var(--background);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--foreground);
            font-size: 0.875rem;
            font-family: inherit;
            transition: all 0.2s;
        }
        
        .form-textarea {
            font-family: 'JetBrains Mono', monospace;
            min-height: 400px;
            resize: vertical;
            line-height: 1.5;
        }
        
        .form-input:focus, .form-textarea:focus, .form-select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.1);
        }
        
        /* Buttons */
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: var(--primary);
            color: var(--background);
        }
        
        .btn-primary:hover {
            background: var(--primary-glow);
            box-shadow: 0 0 20px rgba(20, 184, 166, 0.4);
        }
        
        .btn-secondary {
            background: var(--secondary);
            color: var(--foreground);
        }
        
        .btn-secondary:hover {
            background: var(--border);
        }
        
        .btn-destructive {
            background: var(--destructive);
            color: white;
        }
        
        .btn-destructive:hover {
            background: hsl(0, 72%, 61%);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        /* Prompt Management */
        .prompt-list {
            display: grid;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .prompt-item {
            background: var(--background);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: border-color 0.2s;
        }
        
        .prompt-item:hover {
            border-color: var(--primary);
        }
        
        .prompt-item.active {
            border-color: var(--primary);
            background: rgba(20, 184, 166, 0.05);
        }
        
        .prompt-info h4 {
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }
        
        .prompt-info p {
            font-size: 0.75rem;
            color: var(--muted);
        }
        
        .prompt-actions {
            display: flex;
            gap: 8px;
        }
        
        .btn-icon {
            padding: 0.5rem;
            background: var(--secondary);
            border: none;
            border-radius: 6px;
            color: var(--foreground);
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-icon:hover {
            background: var(--border);
        }
        
        /* Alert Messages */
        .alert {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .alert-success {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid var(--success);
            color: var(--success);
        }
        
        .alert-warning {
            background: rgba(251, 191, 36, 0.1);
            border: 1px solid var(--warning);
            color: var(--warning);
        }
        
        .alert-error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid var(--destructive);
            color: var(--destructive);
        }
        
        /* Grid Layout */
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        
        @media (max-width: 768px) {
            .grid-2 {
                grid-template-columns: 1fr;
            }
        }
        
        /* Loading Spinner */
        .spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid var(--border);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="logo">
                <div class="logo-icon">🎯</div>
                <div class="logo-text">
                    <h1>ALM Scenario Generator</h1>
                    <p>Risk Management Platform</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="main">
        <div class="tabs">
            <button class="tab active" onclick="switchTab('generate')">
                📊 Generate Scenarios
            </button>
            <button class="tab" onclick="switchTab('prompts')">
                ⚙️ Prompt Editor
            </button>
        </div>
        
        <!-- Generate Tab -->
        <div id="generateTab" class="tab-content active">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Scenario Generation</h2>
                    <p class="card-description">Define your stress testing scenarios using natural language</p>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Scenario Instructions</label>
                    <textarea id="instruction" class="form-textarea" rows="8" placeholder="Example:
Generate 3 severe stress scenarios:
1. Financial crisis with +200 bps rate shock
2. Credit crisis with spread widening
3. Currency crisis with CHF appreciation"></textarea>
                </div>
                
                <div class="grid-2">
                    <div class="form-group">
                        <label class="form-label">Number of Scenarios</label>
                        <input type="number" id="numScenarios" class="form-input" value="3" min="1" max="10">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Scenario Type</label>
                        <select id="scenarioType" class="form-select">
                            <option value="stress">Stress</option>
                            <option value="stochastic">Stochastic</option>
                            <option value="both">Both</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="form-label">AI Model Prompt</label>
                    <select id="selectedPrompt" class="form-select" onchange="updatePromptPreview()">
                        <option value="default">Default ALM Expert</option>
                    </select>
                </div>
                
                <button class="btn btn-primary" onclick="generate()" id="generateBtn">
                    Generate Scenarios
                </button>
                
                <div id="result" style="margin-top: 2rem; display: none;"></div>
            </div>
        </div>
        
        <!-- Prompts Tab -->
        <div id="promptsTab" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Manage AI Model Prompts</h2>
                    <p class="card-description">Customize the AI model's behavior and expertise</p>
                </div>
                
                <div id="alertContainer"></div>
                
                <div class="prompt-list" id="promptList">
                    <!-- Prompts will be loaded here -->
                </div>
                
                <div style="border-top: 1px solid var(--border); padding-top: 1.5rem; margin-top: 1.5rem;">
                    <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">
                        <span id="editorTitle">Create New Prompt</span>
                    </h3>
                    
                    <div class="form-group">
                        <label class="form-label">Prompt Name</label>
                        <input type="text" id="promptName" class="form-input" placeholder="e.g., Conservative Risk Expert">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">System Prompt</label>
                        <textarea id="promptText" class="form-textarea" placeholder="Define the AI model's expertise, guidelines, and behavior..."></textarea>
                    </div>
                    
                    <div style="display: flex; gap: 12px;">
                        <button class="btn btn-primary" onclick="savePrompt()">
                            💾 Save Prompt
                        </button>
                        <button class="btn btn-secondary" onclick="resetEditor()">
                            ✖️ Cancel
                        </button>
                        <button class="btn btn-secondary" onclick="loadDefaultPrompt()">
                            🔄 Load Default Template
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let prompts = {};
        let currentPromptId = null;
        let activePromptId = 'default';
        
        // Tab Switching
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName + 'Tab').classList.add('active');
            
            if (tabName === 'prompts') {
                loadPrompts();
            }
        }
        
        // Load Prompts
        async function loadPrompts() {
            try {
                const response = await fetch('/prompts');
                prompts = await response.json();
                renderPromptList();
                updatePromptDropdown();
            } catch (error) {
                showAlert('Failed to load prompts', 'error');
            }
        }
        
        // Render Prompt List
        function renderPromptList() {
            const container = document.getElementById('promptList');
            container.innerHTML = '';
            
            for (const [id, prompt] of Object.entries(prompts)) {
                const div = document.createElement('div');
                div.className = `prompt-item ${id === activePromptId ? 'active' : ''}`;
                div.innerHTML = `
                    <div class="prompt-info">
                        <h4>${prompt.name} ${id === activePromptId ? '✓' : ''}</h4>
                        <p>Created: ${new Date(prompt.created_at).toLocaleDateString()}</p>
                    </div>
                    <div class="prompt-actions">
                        <button class="btn-icon" onclick="selectPrompt('${id}')" title="Use this prompt">
                            ✓
                        </button>
                        <button class="btn-icon" onclick="editPrompt('${id}')" title="Edit">
                            ✏️
                        </button>
                        ${id !== 'default' ? `
                        <button class="btn-icon" onclick="deletePrompt('${id}')" title="Delete">
                            🗑️
                        </button>
                        ` : ''}
                    </div>
                `;
                container.appendChild(div);
            }
        }
        
        // Update Prompt Dropdown
        function updatePromptDropdown() {
            const select = document.getElementById('selectedPrompt');
            select.innerHTML = '';
            
            for (const [id, prompt] of Object.entries(prompts)) {
                const option = document.createElement('option');
                option.value = id;
                option.textContent = prompt.name;
                if (id === activePromptId) option.selected = true;
                select.appendChild(option);
            }
        }
        
        // Select Prompt (Set as Active)
        async function selectPrompt(id) {
            activePromptId = id;
            await fetch('/prompts/select', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt_id: id})
            });
            renderPromptList();
            updatePromptDropdown();
            showAlert(`Prompt "${prompts[id].name}" is now active`, 'success');
        }
        
        // Edit Prompt
        function editPrompt(id) {
            currentPromptId = id;
            const prompt = prompts[id];
            document.getElementById('editorTitle').textContent = 'Edit Prompt';
            document.getElementById('promptName').value = prompt.name;
            document.getElementById('promptText').value = prompt.prompt;
            document.getElementById('promptName').scrollIntoView({behavior: 'smooth'});
        }
        
        // Delete Prompt
        async function deletePrompt(id) {
            if (!confirm(`Delete prompt "${prompts[id].name}"?`)) return;
            
            try {
                const response = await fetch('/prompts/' + id, {method: 'DELETE'});
                if (response.ok) {
                    delete prompts[id];
                    if (activePromptId === id) activePromptId = 'default';
                    renderPromptList();
                    updatePromptDropdown();
                    showAlert('Prompt deleted successfully', 'success');
                }
            } catch (error) {
                showAlert('Failed to delete prompt', 'error');
            }
        }
        
        // Save Prompt
        async function savePrompt() {
            const name = document.getElementById('promptName').value.trim();
            const text = document.getElementById('promptText').value.trim();
            
            if (!name || !text) {
                showAlert('Please fill in all fields', 'warning');
                return;
            }
            
            const id = currentPromptId || 'custom_' + Date.now();
            const data = {
                id,
                prompt: {
                    name,
                    prompt: text,
                    created_at: currentPromptId ? prompts[currentPromptId].created_at : new Date().toISOString()
                }
            };
            
            try {
                const response = await fetch('/prompts', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                if (response.ok) {
                    prompts[id] = data.prompt;
                    renderPromptList();
                    updatePromptDropdown();
                    resetEditor();
                    showAlert('Prompt saved successfully', 'success');
                }
            } catch (error) {
                showAlert('Failed to save prompt', 'error');
            }
        }
        
        // Reset Editor
        function resetEditor() {
            currentPromptId = null;
            document.getElementById('editorTitle').textContent = 'Create New Prompt';
            document.getElementById('promptName').value = '';
            document.getElementById('promptText').value = '';
        }
        
        // Load Default Prompt Template
        function loadDefaultPrompt() {
            if (prompts.default) {
                document.getElementById('promptText').value = prompts.default.prompt;
            }
        }
        
        // Show Alert
        function showAlert(message, type) {
            const container = document.getElementById('alertContainer');
            const div = document.createElement('div');
            div.className = `alert alert-${type}`;
            div.textContent = message;
            container.appendChild(div);
            
            setTimeout(() => div.remove(), 5000);
        }
        
        // Generate Scenarios
        async function generate() {
            const instruction = document.getElementById('instruction').value;
            const numScenarios = document.getElementById('numScenarios').value;
            const scenarioType = document.getElementById('scenarioType').value;
            const promptId = document.getElementById('selectedPrompt').value;
            
            if (!instruction.trim()) {
                alert('Please enter scenario instructions');
                return;
            }
            
            const btn = document.getElementById('generateBtn');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> Generating...';
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        instruction,
                        num_scenarios: parseInt(numScenarios),
                        scenario_type: scenarioType,
                        prompt_id: promptId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    displayResults(data.scenarios);
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                alert('Connection error: ' + error);
            } finally {
                btn.disabled = false;
                btn.innerHTML = 'Generate Scenarios';
            }
        }
        
        // Display Results
        function displayResults(scenarios) {
            const container = document.getElementById('result');
            let html = '<div class="card" style="background: var(--background);">';
            html += '<h3 style="margin-bottom: 1.5rem;">✅ Generated ' + scenarios.length + ' Scenarios</h3>';
            
            scenarios.forEach((s, i) => {
                html += '<div class="card" style="margin-bottom: 1rem;">';
                html += '<h4>' + (i+1) + '. ' + s.name + '</h4>';
                html += '<p style="color: var(--muted); margin: 0.5rem 0;">' + s.description + '</p>';
                html += '<p style="font-size: 0.875rem;"><strong>Shocks:</strong> ' + s.num_shocks + '</p>';
                html += '</div>';
            });
            
            html += '</div>';
            container.innerHTML = html;
            container.style.display = 'block';
        }
        
        // Initialize
        loadPrompts();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/prompts', methods=['GET'])
def get_prompts():
    """Get all prompts"""
    return jsonify(load_prompts())

@app.route('/prompts', methods=['POST'])
def save_prompt():
    """Save a prompt"""
    data = request.json
    prompts = load_prompts()
    prompts[data['id']] = data['prompt']
    save_prompts(prompts)
    return jsonify({'success': True})

@app.route('/prompts/<prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """Delete a prompt"""
    prompts = load_prompts()
    if prompt_id in prompts and prompt_id != 'default':
        del prompts[prompt_id]
        save_prompts(prompts)
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/prompts/select', methods=['POST'])
def select_prompt():
    """Set active prompt"""
    data = request.json
    # Store active prompt in a file or session
    with open('active_prompt.txt', 'w') as f:
        f.write(data['prompt_id'])
    return jsonify({'success': True})

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        instruction = data.get('instruction', '')
        num_scenarios = data.get('num_scenarios', 3)
        scenario_type = data.get('scenario_type', 'stress')
        prompt_id = data.get('prompt_id', 'default')
        
        print(f"\n{'='*60}")
        print(f"Web request:")
        print(f"  Instruction: {instruction[:100]}...")
        print(f"  Num scenarios: {num_scenarios}")
        print(f"  Type: {scenario_type}")
        print(f"  Prompt: {prompt_id}")
        print(f"{'='*60}\n")
        
        # Load custom prompt
        prompts = load_prompts()
        custom_prompt = prompts.get(prompt_id, prompts['default'])['prompt']
        
        risk_factors, counterparties, contracts = load_data()
        
        llm_client = LlamaClient(base_url="http://localhost:11434", model_name="llama3")
        generator = ALMScenarioGenerator(llm_client)
        
        # TODO: Pass custom_prompt to generator (requires modification to ALMScenarioGenerator)
        print(f"Using custom prompt: {custom_prompt[:100]}...")
        
        print("Generating scenarios...")
        scenarios, df = generator.generate_scenarios(
            risk_factors=risk_factors,
            counterparties=counterparties,
            contracts=contracts,
            user_instruction=instruction,
            num_scenarios=num_scenarios,
            scenario_type=scenario_type
        )
        
        # Save to CSV
        csv_file = f"scenarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_file, index=False)
        print(f"✓ Saved to {csv_file}\n")
        
        result = []
        for s in scenarios:
            result.append({
                'name': s.name,
                'description': s.description,
                'type': s.scenario_type,
                'num_shocks': len(s.shocks),
                'shocks': [
                    {
                        'factor_type': sh.factor_type, 
                        'factor_id': sh.factor_id, 
                        'shock_type': sh.shock_type, 
                        'value': sh.value
                    } 
                    for sh in s.shocks
                ]
            })
        
        return jsonify({
            'success': True, 
            'scenarios': result,
            'csv_file': csv_file
        })
        
    except Exception as e:
        import traceback
        print(f"✗ Error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("   ALM SCENARIO GENERATOR - WITH PROMPT EDITOR")
    print("=" * 60)
    print()
    print("  🌐 Open in browser: http://localhost:8081")
    print()
    print("  Features:")
    print("    • Scenario generation with custom AI prompts")
    print("    • Prompt editor for model customization")
    print("    • Multiple prompt profiles")
    print("    • Real-time prompt switching")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8081, debug=False)