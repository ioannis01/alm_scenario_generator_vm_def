"""
Simple Web Interface for ALM Scenario Generator
"""

from flask import Flask, render_template_string, request, jsonify
from alm_scenarios import ALMScenarioGenerator, LlamaClient
from load_alm_data import load_from_riskpro

app = Flask(__name__)

# Cache data
cache = {'loaded': False, 'risk_factors': None, 'counterparties': None, 'contracts': None}

def load_data():
    if not cache['loaded']:
        print("Loading ALM data...")
        cache['risk_factors'], cache['counterparties'], cache['contracts'] = load_from_riskpro(limit_contracts=1000)
        cache['loaded'] = True
        print(f"✓ Loaded {len(cache['contracts'])} contracts")
    return cache['risk_factors'], cache['counterparties'], cache['contracts']

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ALM Scenario Generator</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            max-width: 1200px; 
            margin: 50px auto; 
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #2c3e50; margin-bottom: 10px; }
        .subtitle { color: #7f8c8d; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #34495e; }
        textarea { 
            width: 100%; 
            height: 150px; 
            padding: 12px; 
            font-size: 14px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-family: inherit;
            resize: vertical;
        }
        textarea:focus { border-color: #3498db; outline: none; }
        input[type="number"], select {
            padding: 8px 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        button { 
            background: #3498db; 
            color: white; 
            padding: 12px 30px; 
            border: none; 
            cursor: pointer; 
            font-size: 16px;
            border-radius: 5px;
            font-weight: bold;
            transition: background 0.3s;
        }
        button:hover { background: #2980b9; }
        button:disabled { background: #95a5a6; cursor: not-allowed; }
        .result { 
            margin-top: 30px; 
            padding: 20px; 
            background: #f8f9fa; 
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        .loading { 
            display: none; 
            color: #3498db; 
            margin-left: 15px;
            font-weight: bold;
        }
        .scenario { 
            margin: 20px 0; 
            padding: 20px; 
            background: white; 
            border-left: 4px solid #3498db;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .scenario h3 { margin-top: 0; color: #2c3e50; }
        .scenario-meta { 
            background: #ecf0f1; 
            padding: 10px; 
            border-radius: 5px; 
            margin: 10px 0;
        }
        .shocks-list { 
            list-style: none; 
            padding: 0; 
        }
        .shocks-list li { 
            padding: 8px 12px; 
            margin: 5px 0; 
            background: #f8f9fa;
            border-radius: 4px;
            border-left: 3px solid #3498db;
        }
        .success-message {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 12px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .error-message {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 12px;
            border-radius: 5px;
        }
        .params-row {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        .example {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 ALM Scenario Generator</h1>
        <p class="subtitle">Generate stress and stochastic scenarios for your RiskPro portfolio</p>
        
        <div class="example">
            <strong>💡 Example:</strong> Generate 3 severe stress scenarios:<br>
            1. Financial crisis with +200 bps rate shock and credit spread widening<br>
            2. Recession with rising unemployment<br>
            3. Currency crisis with CHF appreciation
        </div>
        
        <div class="form-group">
            <label for="instruction">Scenario Instruction:</label>
            <textarea id="instruction" placeholder="Describe the scenarios you want to generate...

Example:
Generate 3 stress scenarios for interest rate risk, credit spreads, and FX rates"></textarea>
        </div>
        
        <div class="params-row">
            <div>
                <label for="numScenarios">Number of scenarios:</label>
                <input type="number" id="numScenarios" value="3" min="1" max="10">
            </div>
            <div>
                <label for="scenarioType">Type:</label>
                <select id="scenarioType">
                    <option value="stress">Stress</option>
                    <option value="stochastic">Stochastic</option>
                    <option value="both">Both</option>
                </select>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <button onclick="generate()" id="generateBtn">Generate Scenarios</button>
            <span class="loading" id="loading">⏳ Generating scenarios from RiskPro...</span>
        </div>
        
        <div id="result" style="display:none;"></div>
    </div>
    
    <script>
        function generate() {
            const instruction = document.getElementById('instruction').value;
            const numScenarios = document.getElementById('numScenarios').value;
            const scenarioType = document.getElementById('scenarioType').value;
            
            if (!instruction.trim()) {
                alert('Please enter scenario instructions');
                return;
            }
            
            document.getElementById('loading').style.display = 'inline';
            document.getElementById('result').style.display = 'none';
            document.getElementById('generateBtn').disabled = true;
            
            fetch('/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    instruction: instruction, 
                    num_scenarios: parseInt(numScenarios), 
                    scenario_type: scenarioType
                })
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('generateBtn').disabled = false;
                if (data.success) {
                    displayResults(data.scenarios, data.csv_file);
                } else {
                    document.getElementById('result').innerHTML = 
                        '<div class="error-message">Error: ' + data.error + '</div>';
                    document.getElementById('result').style.display = 'block';
                }
            })
            .catch(err => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('generateBtn').disabled = false;
                document.getElementById('result').innerHTML = 
                    '<div class="error-message">Connection error: ' + err + '</div>';
                document.getElementById('result').style.display = 'block';
            });
        }
        
        function displayResults(scenarios, csvFile) {
            let html = '<div class="success-message">';
            html += '<strong>✅ Success!</strong> Generated ' + scenarios.length + ' scenarios from RiskPro portfolio';
            html += '</div>';
            
            scenarios.forEach((s, i) => {
                html += '<div class="scenario">';
                html += '<h3>' + (i+1) + '. ' + s.name + '</h3>';
                html += '<div class="scenario-meta">';
                html += '<strong>Type:</strong> ' + s.type + ' | ';
                html += '<strong>Shocks:</strong> ' + s.num_shocks;
                html += '</div>';
                html += '<p><strong>Description:</strong><br>' + s.description + '</p>';
                html += '<h4>Applied Shocks (first 10):</h4>';
                html += '<ul class="shocks-list">';
                s.shocks.slice(0, 10).forEach(shock => {
                    html += '<li><strong>' + shock.factor_type + '</strong> | ' + 
                           shock.factor_id + ' → ' + shock.shock_type + ' = <strong>' + 
                           shock.value + '</strong></li>';
                });
                if (s.num_shocks > 10) {
                    html += '<li style="background:#e8f4f8;">... and <strong>' + 
                           (s.num_shocks - 10) + '</strong> more shocks</li>';
                }
                html += '</ul></div>';
            });
            
            html += '<div class="success-message" style="margin-top:20px;">';
            html += '<strong>📊 Results saved to:</strong> ' + csvFile;
            html += '</div>';
            
            document.getElementById('result').innerHTML = html;
            document.getElementById('result').style.display = 'block';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        instruction = data.get('instruction', '')
        num_scenarios = data.get('num_scenarios', 3)
        scenario_type = data.get('scenario_type', 'stress')
        
        print(f"\n{'='*60}")
        print(f"Web request:")
        print(f"  Instruction: {instruction[:100]}...")
        print(f"  Num scenarios: {num_scenarios}")
        print(f"  Type: {scenario_type}")
        print(f"{'='*60}\n")
        
        risk_factors, counterparties, contracts = load_data()
        
        llm_client = LlamaClient(base_url="http://localhost:11434", model_name="llama3")
        generator = ALMScenarioGenerator(llm_client)
        
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
        csv_file = "scenarios_output.csv"
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
        
        return jsonify({'success': True, 'scenarios': result, 'csv_file': csv_file})
    except Exception as e:
        import traceback
        print(f"✗ Error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("ALM SCENARIO GENERATOR - WEB INTERFACE")
    print("=" * 60)
    print("Open in browser: http://localhost:8081")
    print("Or from other computers: http://YOUR_IP:8081")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8081, debug=False)
