"""
Simple API for ALM Scenario Generation
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

from alm_scenarios import ALMScenarioGenerator, LlamaClient
from load_alm_data import load_from_riskpro

app = Flask(__name__)
CORS(app)

cache = {'loaded': False, 'risk_factors': None, 'counterparties': None, 'contracts': None}

def load_data():
    if not cache['loaded']:
        print("Loading ALM data from RiskPro...")
        cache['risk_factors'], cache['counterparties'], cache['contracts'] = load_from_riskpro(
            limit_contracts=1000
        )
        cache['loaded'] = True
        print(f"✓ Loaded {len(cache['contracts'])} contracts")
    return cache['risk_factors'], cache['counterparties'], cache['contracts']

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        instruction = data.get('instruction', '')
        num_scenarios = data.get('num_scenarios', 3)
        
        print(f"\nRequest: {instruction[:80]}...")
        
        risk_factors, counterparties, contracts = load_data()
        
        llm_client = LlamaClient(
            base_url="http://localhost:11434",
            model_name="llama3"
        )
        generator = ALMScenarioGenerator(llm_client)
        
        print("Generating scenarios...")
        scenarios, df = generator.generate_scenarios(
            risk_factors=risk_factors,
            counterparties=counterparties,
            contracts=contracts,
            user_instruction=instruction,
            num_scenarios=num_scenarios
        )
        
        print(f"✓ Generated {len(scenarios)} scenarios")
        
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
        
        return jsonify({'success': True, 'scenarios': result})
    except Exception as e:
        import traceback
        print(f"✗ Error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'data_loaded': cache['loaded']})

if __name__ == '__main__':
    print("="*60)
    print("ALM SCENARIO API SERVER")
    print("="*60)
    print("Starting on http://0.0.0.0:5000")
    print("Press Ctrl+C to stop")
    print("="*60)
    app.run(host='0.0.0.0', port=5000, debug=False)
