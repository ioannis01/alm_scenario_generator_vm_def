"""
ALM Scenario Generator API
Runs on your PC, accessible from Ubuntu VM
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

from alm_scenarios import ALMScenarioGenerator, LlamaClient
from load_alm_data import load_from_riskpro

app = Flask(__name__)
CORS(app)  # Allow requests from VM

# Cache data
cache = {'loaded': False, 'risk_factors': None, 'counterparties': None, 'contracts': None}


def load_data():
    if not cache['loaded']:
        print("Loading ALM data from RiskPro...")
        try:
            cache['risk_factors'], cache['counterparties'], cache['contracts'] = load_from_riskpro(
                limit_contracts=1000
            )
            cache['loaded'] = True
            print(f"✓ Loaded {len(cache['contracts'])} contracts")
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
    return cache['risk_factors'], cache['counterparties'], cache['contracts']


@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        instruction = data.get('instruction', '')
        num_scenarios = data.get('num_scenarios', 3)
        
        if not instruction:
            return jsonify({'success': False, 'error': 'Instruction required'}), 400
        
        print(f"\n{'='*60}")
        print(f"New request received")
        print(f"Instruction: {instruction[:100]}...")
        print(f"{'='*60}")
        
        # Load data
        risk_factors, counterparties, contracts = load_data()
        print(f"Data loaded: {len(risk_factors)} risk factors, {len(contracts)} contracts")
        
        # Generate scenarios
        llm_client = LlamaClient(
            base_url="http://localhost:11434",  # Ollama on same PC
            model_name="llama3"
        )
        generator = ALMScenarioGenerator(llm_client)
        
        print("Generating scenarios...")
        scenarios, df = generator.generate_scenarios(
            risk_factors=risk_factors,
            counterparties=counterparties,
            contracts=contracts,
            user_instruction=instruction,
            num_scenarios=min(num_scenarios, 10)
        )
        
        print(f"✓ Generated {len(scenarios)} scenarios")
        
        # Save CSV
        csv_path = "generated_scenarios.csv"
        df.to_csv(csv_path, index=False)
        print(f"✓ Saved to {csv_path}")
        
        # Format response
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
                        'value': sh.value,
                        'description': sh.description
                    }
                    for sh in s.shocks
                ]
            })
        
        return jsonify({
            'success': True,
            'num_scenarios': len(scenarios),
            'total_shocks': len(df),
            'scenarios': result
        })
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'data_loaded': cache['loaded'],
        'num_contracts': len(cache['contracts']) if cache['loaded'] else 0
    })


@app.route('/status', methods=['GET'])
def status():
    """Detailed status endpoint"""
    return jsonify({
        'api_running': True,
        'data_loaded': cache['loaded'],
        'risk_factors': len(cache['risk_factors']) if cache['loaded'] else 0,
        'counterparties': len(cache['counterparties']) if cache['loaded'] else 0,
        'contracts': len(cache['contracts']) if cache['loaded'] else 0,
        'ollama_url': 'http://localhost:11434',
        'riskpro_db': 'RP_1225'
    })


if __name__ == '__main__':
    print("=" * 80)
    print("ALM SCENARIO GENERATOR API")
    print("=" * 80)
    print()
    print("Starting API server...")
    print(f"  Host: 0.0.0.0 (accessible from network)")
    print(f"  Port: 5000")
    print()
    print("Endpoints:")
    print(f"  POST http://172.27.192.1:5000/generate - Generate scenarios")
    print(f"  GET  http://172.27.192.1:5000/health - Health check")
    print(f"  GET  http://172.27.192.1:5000/status - Detailed status")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 80)
    print()
    
    # Run on all interfaces so VM can access it
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)