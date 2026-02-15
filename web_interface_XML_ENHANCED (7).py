"""
Professional Web Interface for ALM Scenario Generator
Enhanced with dark fintech theme, charts, and comprehensive reports
"""

from flask import Flask, render_template_string, request, jsonify, send_file
from werkzeug.utils import secure_filename
from alm_scenarios import ALMScenarioGenerator, LlamaClient
#from load_from_Risk HUB import load_from_Risk HUB
from load_alm_data import load_from_riskpro
from xml_loader_dynamic import load_from_xml

import json
import random
import os
import re
import xml.etree.ElementTree as ET
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

app = Flask(__name__)

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Configure file uploads
app.config['UPLOAD_FOLDER'] = '/tmp/alm_xml_uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Enhanced cache with metadata for state management
cache = {
    'loaded': False,
    'source': None,  # 'db' or 'xml'
    'risk_factors': None,
    'counterparties': None,
    'contracts': None,
    'model_id': None,
    'limit': None,
    'load_timestamp': None,
    'uploaded_files': {},  # For XML file tracking
    'counterparties_df': None,  # Enriched DataFrame with all counterparty attributes
    'discovered_schema': None,  # Counterparty schema discovery metadata
    'contracts_df': None,  # Enriched DataFrame with all contract attributes
    'contracts_schema': None,  # Contract schema discovery metadata
    'observations_df': None,  # Enriched DataFrame with all observation/risk factor attributes
    'observations_schema': None,  # Observations schema discovery metadata
    'model_params': None,  # Model parameters dictionary (NEW!)
    'model_params_df': None,  # Model parameters DataFrame (NEW!)
    'model_params_schema': None  # Model parameters schema discovery metadata (NEW!)
}

# Prompts storage file
PROMPTS_FILE = 'custom_prompts.json'


# ============================================================================
# PROMPT MANAGEMENT FUNCTIONS
# ============================================================================

def load_prompts() -> List[Dict[str, Any]]:
    """Load prompts from JSON file"""
    if not os.path.exists(PROMPTS_FILE):
        default_prompts = [
            {
                'id': 'default',
                'name': 'Default ALM Expert',
                'description': 'Balanced approach for general stress testing',
                'prompt_text': 'You are an expert quantitative risk analyst specializing in ALM.',
                'variables': [],
                'tags': ['default'],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'is_default': True
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

def extract_variables(prompt_text: str) -> List[str]:
    """Extract {variable} placeholders"""
    return list(set(re.findall(r'\{(\w+)\}', prompt_text)))

def generate_prompt_id(name: str) -> str:
    """Generate unique ID"""
    base_id = re.sub(r'[^a-z0-9_]', '_', name.lower())
    return f"{base_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

def load_data_with_config(model_id=None, limit=None, load_contracts=True, 
                          load_counterparties=True, load_risk_factors_from_db=False):
    """Load data with specific configuration and dataset selection, cache it"""
    print(f"📊 Loading data with config:")
    print(f"  model_id={model_id}, limit={limit}")
    print(f"  load_contracts={load_contracts}")
    print(f"  load_counterparties={load_counterparties}")
    print(f"  load_risk_factors_from_db={load_risk_factors_from_db}")
    
    # Call load_from_riskpro with dataset selection parameters
    risk_factors, counterparties, contracts = load_from_riskpro(
        model_id=model_id,
        limit_contracts=limit,
        load_risk_factors_from_db_flag=load_risk_factors_from_db,
        load_counterparties_flag=load_counterparties,
        load_contracts_flag=load_contracts
    )
    
    from risk_attributes_integration import enrich_contracts_with_risk_attributes
    if contracts:
        contracts = enrich_contracts_with_risk_attributes(contracts, counterparties)

    # Store in cache with metadata
    cache['loaded'] = True
    cache['risk_factors'] = risk_factors
    cache['counterparties'] = counterparties
    cache['contracts'] = contracts
    cache['model_id'] = model_id or 'All'
    cache['limit'] = limit
    cache['load_timestamp'] = datetime.now().isoformat()
    cache['load_risk_factors_from_db'] = load_risk_factors_from_db
    
    print(f"✓ Loaded: {len(contracts)} contracts, {len(counterparties)} counterparties, {len(risk_factors)} risk factors")
    print(f"✓ Data cached in memory")
    
    return risk_factors, counterparties, contracts

def get_cached_data():
    """Get data from cache - used by generate endpoint"""
    if not cache['loaded']:
        raise ValueError("No data loaded. Please load data first from the Data Loading tab.")
    return cache['risk_factors'], cache['counterparties'], cache['contracts']

def generate_impact_metrics():
    """Generate simulated impact metrics for demo purposes"""
    return {
        'nii': round(random.uniform(-35, -5), 1),
        'eve': round(random.uniform(-30, -3), 1),
        'var': round(random.uniform(10, 60), 1)
    }

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI on ALM & Risk | Regnology Risk Hub</title>
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
            --chart-1: hsl(173, 80%, 40%);
            --chart-2: hsl(199, 89%, 48%);
            --chart-3: hsl(271, 91%, 65%);
            --chart-4: hsl(38, 92%, 50%);
            --chart-5: hsl(0, 72%, 51%);
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
        
        /* Header */
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
            width: 48px;
            height: 48px;
            /* Removed gradient background to show logo */
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 4px;
        }
        
        .logo-icon img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        
        .logo-text h1 {
            font-size: 1.25rem;
            font-weight: 600;
            letter-spacing: -0.02em;
        }
        
        .logo-text p {
            font-size: 0.75rem;
            color: var(--muted);
        }
        
        .header-status {
            display: flex;
            gap: 24px;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.875rem;
            color: var(--muted);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* Main Content */
        .main {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        /* Tabs */
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
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .tab:hover {
            color: var(--foreground);
        }
        
        .tab.active {
            background: var(--card);
            color: var(--foreground);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        
        .tab-badge {
            background: var(--primary);
            color: var(--background);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.75rem;
            font-weight: 600;
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
        
        /* Grid Layout */
        .grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 2rem;
        }
        
        @media (max-width: 1024px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* Card */
        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            transition: border-color 0.3s;
        }
        
        .card:hover {
            border-color: rgba(20, 184, 166, 0.3);
        }
        
        .card-header {
            margin-bottom: 1.5rem;
        }
        
        .card-title {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        /* Form Elements */
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        label {
            display: block;
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: var(--foreground);
        }
        
        textarea {
            width: 100%;
            min-height: 140px;
            padding: 12px 16px;
            background: var(--secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--foreground);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            resize: vertical;
            transition: border-color 0.2s;
        }
        
        textarea:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        textarea::placeholder {
            color: var(--muted);
        }
        
        select, input[type="number"] {
            padding: 10px 14px;
            background: var(--secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--foreground);
            font-size: 0.875rem;
            min-width: 180px;
        }
        
        select:focus, input[type="number"]:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }
        
        .slider-container {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        
        .slider-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
            font-family: 'JetBrains Mono', monospace;
            min-width: 50px;
            text-align: right;
        }
        
        input[type="range"] {
            flex: 1;
            height: 6px;
            -webkit-appearance: none;
            background: var(--secondary);
            border-radius: 3px;
        }
        
        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 20px;
            height: 20px;
            background: var(--primary);
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 0 10px rgba(20, 184, 166, 0.5);
        }
        
        /* Buttons */
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--chart-2));
            color: var(--background);
            box-shadow: 0 4px 20px rgba(20, 184, 166, 0.3);
        }
        
        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 25px rgba(20, 184, 166, 0.4);
        }
        
        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-outline {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--foreground);
        }
        
        .btn-outline:hover {
            background: var(--secondary);
        }
        
        .btn-full {
            width: 100%;
            justify-content: center;
        }
        
        /* Quick Start Examples */
        .examples-box {
            background: rgba(251, 191, 36, 0.1);
            border: 1px solid rgba(251, 191, 36, 0.2);
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .examples-header {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--warning);
            font-weight: 500;
            margin-bottom: 0.75rem;
        }
        
        .example-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .example-chip {
            padding: 6px 12px;
            background: var(--secondary);
            border: none;
            border-radius: 20px;
            color: var(--foreground);
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .example-chip:hover {
            background: var(--card-hover);
        }
        
        /* Status Panel */
        .status-panel {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .status-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
        }
        
        .status-card h3 {
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 1rem;
        }
        
        .status-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            font-size: 0.875rem;
        }
        
        .status-label {
            color: var(--muted);
        }
        
        .status-value {
            font-family: 'JetBrains Mono', monospace;
        }
        
        .status-active {
            color: var(--success);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        /* Loading Spinner */
        .spinner {
            width: 20px;
            height: 20px;
            border: 2px solid var(--background);
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Results Section */
        .results-section {
            margin-top: 2rem;
        }
        
        /* Success Banner */
        .success-banner {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.2);
            border-radius: 12px;
            padding: 1rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
        }
        
        .success-content {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .success-icon {
            width: 24px;
            height: 24px;
            background: var(--success);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        
        .success-text h4 {
            color: var(--success);
            font-weight: 600;
        }
        
        .success-text p {
            font-size: 0.875rem;
            color: var(--muted);
        }
        
        .success-actions {
            display: flex;
            gap: 8px;
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        .stat-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.3s;
        }
        
        .stat-card:hover {
            border-color: rgba(20, 184, 166, 0.3);
        }
        
        .stat-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }
        
        .stat-label {
            font-size: 0.875rem;
            color: var(--muted);
            margin-bottom: 0.5rem;
        }
        
        .stat-value {
            font-size: 1.75rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .stat-value.negative {
            color: var(--destructive);
        }
        
        .stat-subtitle {
            font-size: 0.75rem;
            color: var(--muted);
            margin-top: 0.25rem;
        }
        
        .stat-icon {
            width: 36px;
            height: 36px;
            background: var(--secondary);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--primary);
        }
        
        /* Charts */
        .charts-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        @media (max-width: 1024px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .chart-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
        }
        
        .chart-title {
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 1rem;
        }
        
        .chart-container {
            height: 250px;
            position: relative;
        }
        
        /* Scenario Cards */
        .scenarios-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .scenario-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.3s;
        }
        
        .scenario-card:hover {
            border-color: rgba(20, 184, 166, 0.3);
        }
        
        .scenario-header {
            padding: 1.25rem;
        }
        
        .scenario-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.75rem;
        }
        
        .scenario-meta {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .scenario-id {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: var(--muted);
        }
        
        .scenario-badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .badge-stress {
            background: rgba(239, 68, 68, 0.2);
            color: var(--destructive);
        }
        
        .badge-stochastic {
            background: rgba(20, 184, 166, 0.2);
            color: var(--primary);
        }
        
        .scenario-impacts {
            display: flex;
            gap: 24px;
        }
        
        .impact-item {
            text-align: right;
        }
        
        .impact-label {
            font-size: 0.75rem;
            color: var(--muted);
        }
        
        .impact-value {
            font-size: 1.125rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .impact-value.negative {
            color: var(--destructive);
        }
        
        .impact-value.positive {
            color: var(--success);
        }
        
        .scenario-name {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .scenario-desc {
            font-size: 0.875rem;
            color: var(--muted);
            line-height: 1.5;
        }
        
        .scenario-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 1rem;
            margin-top: 1rem;
            border-top: 1px solid var(--border);
        }
        
        .shocks-count {
            font-size: 0.875rem;
            color: var(--muted);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .toggle-btn {
            background: transparent;
            border: none;
            color: var(--primary);
            font-size: 0.875rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .toggle-btn:hover {
            text-decoration: underline;
        }
        
        /* Shocks Detail */
        .shocks-detail {
            display: none;
            background: var(--secondary);
            padding: 1.25rem;
            border-top: 1px solid var(--border);
        }
        
        .shocks-detail.expanded {
            display: block;
            animation: slideDown 0.3s ease;
        }
        
        @keyframes slideDown {
            from { opacity: 0; max-height: 0; }
            to { opacity: 1; max-height: 500px; }
        }
        
        .shocks-title {
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 1rem;
        }
        
        .shocks-list {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .shock-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 1rem;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.875rem;
        }
        
        .shock-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .shock-type-badge {
            padding: 2px 8px;
            background: var(--secondary);
            border: 1px solid var(--border);
            border-radius: 4px;
            font-size: 0.75rem;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .shock-factor {
            color: var(--muted);
            font-family: 'JetBrains Mono', monospace;
        }
        
        .shock-value-info {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .shock-method {
            font-size: 0.75rem;
            color: var(--muted);
        }
        
        .shock-value {
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .more-shocks {
            text-align: center;
            padding: 0.75rem;
            background: rgba(20, 184, 166, 0.1);
            border-radius: 8px;
            color: var(--primary);
            font-size: 0.875rem;
        }
        
        /* Error State */
        .error-banner {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.2);
            border-radius: 12px;
            padding: 1rem 1.5rem;
            color: var(--destructive);
            margin-bottom: 1.5rem;
        }
        
        /* Documentation */
        .docs-content {
            max-width: 800px;
        }
        
        .docs-section {
            margin-bottom: 2rem;
        }
        
        .docs-section h3 {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
        }
        
        .docs-section p {
            color: var(--muted);
            margin-bottom: 0.5rem;
        }
        
        .docs-section ul {
            color: var(--muted);
            padding-left: 1.5rem;
        }
        
        .docs-section li {
            margin-bottom: 0.5rem;
        }
        
        .docs-section strong {
            color: var(--foreground);
        }
        
        /* Activity List */
        .activity-list {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }
        
        .activity-item {
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }
        
        .activity-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            margin-top: 8px;
        }
        
        .activity-dot.active {
            background: var(--primary);
        }
        
        .activity-dot.inactive {
            background: var(--muted);
        }
        
        .activity-text {
            font-size: 0.875rem;
            color: var(--muted);
        }
        
        .activity-time {
            font-size: 0.75rem;
            color: var(--muted);
            opacity: 0.6;
        }
        
        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            color: var(--muted);
        }
        
        .empty-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }
        
        /* Hide element */
        .hidden {
            display: none !important;
        }
        
        /* Radio Card Styles */
        .radio-card {
            display: block;
            cursor: pointer;
            position: relative;
        }
        
        .radio-card input[type="radio"] {
            position: absolute;
            opacity: 0;
            cursor: pointer;
        }
        
        .radio-card-content {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.5rem;
            padding: 1.25rem;
            background: var(--secondary);
            border: 2px solid var(--border);
            border-radius: 10px;
            transition: all 0.3s;
        }
        
        .radio-card input[type="radio"]:checked + .radio-card-content {
            border-color: var(--primary);
            background: rgba(20, 184, 166, 0.05);
        }
        
        .radio-card:hover .radio-card-content {
            border-color: var(--primary);
        }
        
        .radio-card-icon {
            font-size: 2rem;
        }
        
        .radio-card-title {
            font-weight: 600;
            font-size: 0.95rem;
            color: var(--foreground);
        }
        
        .radio-card-desc {
            font-size: 0.75rem;
            color: var(--muted);
            text-align: center;
        }
        
        /* Source Parameters */
        .source-params {
            animation: fadeIn 0.3s ease;
        }
        
        /* Upload Area Styles */
        .upload-area {
            border: 2px dashed var(--border);
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: var(--secondary);
        }
        
        .upload-area:hover {
            border-color: #8b5cf6;
            background: rgba(139, 92, 246, 0.05);
        }
        
        .upload-area.dragover {
            border-color: var(--primary);
            background: rgba(20, 184, 166, 0.1);
        }
        
        .upload-placeholder {
            pointer-events: none;
        }
        
        .upload-icon {
            font-size: 3rem;
            display: block;
            margin-bottom: 0.75rem;
        }
        
        .upload-hint {
            font-size: 0.75rem;
            color: var(--muted);
            margin-top: 0.5rem;
        }
        
        /* Selected Files */
        .selected-files {
            margin-top: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .file-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
            transition: all 0.2s;
        }
        
        .file-item:hover {
            border-color: var(--primary);
        }
        
        .file-icon {
            font-size: 1.5rem;
        }
        
        .file-name {
            flex: 1;
            font-size: 0.875rem;
            color: var(--foreground);
        }
        
        .file-size {
            font-size: 0.75rem;
            color: var(--muted);
        }
        
        .file-type {
            font-size: 0.7rem;
            padding: 2px 8px;
            background: rgba(20, 184, 166, 0.2);
            color: var(--primary);
            border-radius: 4px;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="header-content">
            <div class="logo">
                <div class="logo-icon">
                    <img src="data:image/webp;base64,UklGRj4CAABXRUJQVlA4IDICAABwEwCdASqWALQAPp1OoUwlpKMiJnn4ALATiWVu4XEr1oRqdFFym97pTDb25ehrbWeYDzkP8P6r95A3pbIexUbjHcY7jHcY7jHb+n2Z0If8VHQhj478gjQJMYBJ4zR/3hshV0hla+m5jIAMNkfcHCfBQBVIFM3TEOk93u1F+JXEJj1nx5UbDHoxS8plpPn3Z7FVCGbsIxP5BMbYbbDbYbZgAD+/Yqu//xKzv6azfhQMABW/oENxN9VhN2L6sio+628B8XtQV+JcJLcbW7xqFGIyxRTY6ul1AEIhYp6qXOyNnW/zVRN8+VK5H+sR8CxWdYPwFH9Enc0e4x11Rnowlti4FBd9APblcZWKTiMO/bttO4I9s/SnMLI7MgSCys355kGLNlzjPzanAkBsNHf1tzC1tDdJ/FFsx+BdqWdo+R7avbe6DfcXqfJSOdny77yPxcFLhqBIVE594vbeCU802JHa51AcAB0FvmCH/3tFqg4HBnaecfzzwrCqPdoqyrlJjRDhewDgOtPGb7B2z7ZPH31sWD/eEmgogIH+y0A4kxJOxJLZxCCRQQNxF2Jp14yeJcFmTlSwqq51D46grxgnHpn/wm+Bu4fN4ScsuBolQhpiYbMLh8MzNiA8oBtibN0yJN20zklTppxyRxJw9ME8OlpfnnhCkYinFBAcrLWSmhU0knWiWZVJkxac5FzgSfXYI+Q9uK5p2LIs+Vla0RjlzHyi2p9H6Ln5xs7k3agAAAA" 
                         alt="Regnology" 
                         style="width: 40px; height: 40px; object-fit: contain;">
                </div>
                <div class="logo-text">
                    <h1>AI on ALM & Risk</h1>
                    <p>Regnology Risk Hub</p>
                </div>
            </div>
            <div class="header-status">
                <div class="status-item">
                    <div class="status-dot"></div>
                    <span>Regnology Risk Hub Connected</span>
                </div>
                <div class="status-item">
                    <div class="status-dot" style="background: var(--success);"></div>
                    <span>Secure</span>
                </div>
            </div>
        </div>
    </header>
    
    <!-- Main Content -->
    <main class="main">
        <!-- Tabs -->
        <div class="tabs">
            <button class="tab active" data-tab="data" onclick="switchTab('data')">
                🗄️ Input Data
            </button>
            <button class="tab" data-tab="knowledge" onclick="switchTab('knowledge')">
                📚 Input Knowledge
                <span class="tab-badge" id="knowledgeBadge">0</span>
            </button>
            <button class="tab" data-tab="prompts" onclick="switchTab('prompts')">
                🧠 Expert's Knowledge
                <span class="tab-badge" id="promptsBadge">0</span>
            </button>
            <button class="tab" data-tab="generate" onclick="switchTab('generate')">
                ⚙️ Generate
            </button>
            <button class="tab" data-tab="results" onclick="switchTab('results')" id="resultsTab">
                📊 Reporting
                <span class="tab-badge hidden" id="resultsBadge">0</span>
            </button>
            <button class="tab" data-tab="docs" onclick="switchTab('docs')">
                📄 Documentation
            </button>
        </div>
        
        <!-- Data Loading Tab -->
        <div class="tab-content active" id="data-content">
            <div class="grid">
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">Data Loading Configuration</h2>
                        <p style="font-size: 0.875rem; color: var(--muted); margin-top: 0.5rem;">
                            Choose your data source and configure loading options
                        </p>
                    </div>
                    
                    <!-- Data Source Selection -->
                    <div class="form-group" style="margin-bottom: 2rem;">
                        <label style="font-weight: 600; margin-bottom: 0.75rem; display: block;">Data Source</label>
                        <div style="display: flex; gap: 1rem;">
                            <label class="radio-card" style="flex: 1;">
                                <input type="radio" name="dataSource" value="db" checked onchange="handleDataSourceChange()">
                                <div class="radio-card-content">
                                    <span class="radio-card-icon">🏦</span>
                                    <span class="radio-card-title">Regnology Risk Hub Database</span>
                                    <span class="radio-card-desc">Connect to Regnology Risk Hub DB</span>
                                </div>
                            </label>
                            <label class="radio-card" style="flex: 1;">
                                <input type="radio" name="dataSource" value="xml" onchange="handleDataSourceChange()">
                                <div class="radio-card-content">
                                    <span class="radio-card-icon">📁</span>
                                    <span class="radio-card-title">XML Files</span>
                                    <span class="radio-card-desc">Upload Regnology Risk Hub XML exports</span>
                                </div>
                            </label>
                        </div>
                    </div>
                    
                    <!-- DATABASE SOURCE PARAMETERS -->
                    <div id="dbParameters" class="source-params">
                        <div style="background: rgba(20, 184, 166, 0.05); border: 1px solid rgba(20, 184, 166, 0.2); border-radius: 10px; padding: 1.5rem;">
                            <div style="display: flex; align-items: center; gap: 8px; color: var(--primary); font-weight: 600; margin-bottom: 1rem; font-size: 1rem;">
                                🏦 Regnology Risk Hub Database Configuration
                            </div>
                            
                            <div class="form-group">
                                <label for="modelIdInput">Model ID</label>
                                <input type="text" 
                                       id="modelIdInput" 
                                       placeholder="Enter Model ID (e.g., 10002) or leave empty for all models" 
                                       style="width: 100%; padding: 10px 14px; background: var(--secondary); border: 1px solid var(--border); border-radius: 8px; color: var(--foreground); font-size: 0.875rem;">
                                <p style="font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem;">
                                    Leave empty to load from all models
                                </p>
                            </div>
                            
                            <div class="form-group">
                                <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; margin-bottom: 0.5rem;">
                                    <input type="checkbox" id="applyLimitCheck" checked>
                                    <span>Apply record limit</span>
                                </label>
                                <input type="number" id="limitInput" value="1000" min="1" max="100000" step="100" style="width: 100%;" placeholder="Maximum records to load">
                                <p style="font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem;">
                                    Recommended: 1000-5000 for testing. Uncheck for full load.
                                </p>
                            </div>
                            
                            <div class="form-group">
                                <label style="font-weight: 600; margin-bottom: 0.75rem; display: block;">Select Datasets to Load</label>
                                
                                <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                                    <label style="display: flex; align-items: center; gap: 10px; padding: 0.75rem; background: var(--secondary); border-radius: 8px; border: 1px solid var(--border); cursor: pointer;">
                                        <input type="checkbox" id="loadContractsCheck" checked style="width: 18px; height: 18px;">
                                        <div style="flex: 1;">
                                            <div style="font-weight: 500; color: var(--foreground);">📄 Contracts</div>
                                            <div style="font-size: 0.75rem; color: var(--muted); margin-top: 0.25rem;">Load contract data from CONTRACT table</div>
                                        </div>
                                    </label>
                                    
                                    <label style="display: flex; align-items: center; gap: 10px; padding: 0.75rem; background: var(--secondary); border-radius: 8px; border: 1px solid var(--border); cursor: pointer;">
                                        <input type="checkbox" id="loadCounterpartiesCheck" checked style="width: 18px; height: 18px;">
                                        <div style="flex: 1;">
                                            <div style="font-weight: 500; color: var(--foreground);">🏢 Counterparties</div>
                                            <div style="font-size: 0.75rem; color: var(--muted); margin-top: 0.25rem;">Load counterparty data from COUNTERPARTY table</div>
                                        </div>
                                    </label>
                                    
                                    <label style="display: flex; align-items: center; gap: 10px; padding: 0.75rem; background: var(--secondary); border-radius: 8px; border: 1px solid var(--border); cursor: pointer;">
                                        <input type="checkbox" id="loadRiskFactorsDBCheck" style="width: 18px; height: 18px;">
                                        <div style="flex: 1;">
                                            <div style="font-weight: 500; color: var(--foreground);">📊 Risk Factors (from Database)</div>
                                            <div style="font-size: 0.75rem; color: var(--muted); margin-top: 0.25rem;">Load from RES_DIM_* tables. If unchecked, uses sample data.</div>
                                        </div>
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- XML SOURCE PARAMETERS -->
                    <div id="xmlParameters" class="source-params" style="display: none;">
                        <div style="background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.2); border-radius: 10px; padding: 1.5rem;">
                            <div style="display: flex; align-items: center; gap: 8px; color: #8b5cf6; font-weight: 600; margin-bottom: 1rem; font-size: 1rem;">
                                📁 XML Files Configuration
                            </div>
                            
                            <div class="form-group">
                                <label style="font-weight: 600; margin-bottom: 0.75rem; display: block;">Upload XML Files</label>
                                <div class="upload-area" id="uploadArea" onclick="document.getElementById('xmlFileInput').click()">
                                    <input type="file" id="xmlFileInput" multiple accept=".xml" style="display: none;" onchange="handleFileSelect(event)">
                                    <div class="upload-placeholder">
                                        <span class="upload-icon">📂</span>
                                        <p style="font-size: 0.9rem; font-weight: 500; margin-bottom: 0.5rem;">Click to select XML files or drag & drop here</p>
                                        <p class="upload-hint">You can upload multiple files: model, contracts, counterparties, creditrisk, observations</p>
                                    </div>
                                </div>
                                
                                <div id="selectedFiles" class="selected-files"></div>
                            </div>
                            
                            <div class="form-group">
                                <label for="xmlLimit">Limit Contracts (optional)</label>
                                <input type="number" id="xmlLimit" placeholder="e.g., 1000 (leave empty for all)" min="1" style="width: 100%; padding: 10px 14px; background: var(--secondary); border: 1px solid var(--border); border-radius: 8px; color: var(--foreground); font-size: 0.875rem;">
                                <p style="font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem;">
                                    Optional: Limit number of contracts to load for testing
                                </p>
                            </div>
                            
                            <div style="background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.2); border-radius: 8px; padding: 1rem; margin-top: 1rem;">
                                <p style="font-size: 0.75rem; color: var(--muted); margin: 0;">
                                    <strong style="color: #fbbf24;">💡 Tip:</strong> XML filenames should contain keywords like 'model', 'contracts', 'counterparties', 'creditrisk', or 'observations' for automatic categorization.
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <div id="dataLoadMessage" style="margin-top: 1rem;"></div>
                    
                    <button class="btn btn-primary btn-full" onclick="confirmAndLoadData()" id="confirmLoadBtn" style="margin-top: 1.5rem;">
                        📥 Confirm & Load Data
                    </button>
                    <p style="font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem; text-align: center;">
                        Click to load data into memory. Data will be cached for scenario generation.
                    </p>
                </div>
                
                <!-- Status Panel -->
                <div class="status-panel">
                    <div class="status-card">
                        <h3>Current Data Status</h3>
                        <div class="status-row">
                            <span class="status-label">Data Loaded</span>
                            <span id="dataLoadedStatus" style="color: var(--muted);">No</span>
                        </div>
                        <div class="status-row">
                            <span class="status-label">Data Source</span>
                            <span id="dataSource" class="status-value">-</span>
                        </div>
                        <div class="status-row">
                            <span class="status-label">Model ID</span>
                            <span id="currentModelId" class="status-value">-</span>
                        </div>
                        <div class="status-row">
                            <span class="status-label">Applied Limit</span>
                            <span id="currentLimit" class="status-value">-</span>
                        </div>
                        <div class="status-row">
                            <span class="status-label">Risk Factors</span>
                            <span id="riskFactorsCount" class="status-value">0</span>
                        </div>
                        <div class="status-row">
                            <span class="status-label">Contracts</span>
                            <span id="contractsCount" class="status-value">0</span>
                        </div>
                        <div class="status-row">
                            <span class="status-label">Counterparties</span>
                            <span id="counterpartiesCount" class="status-value">0</span>
                        </div>
                        <div class="status-row">
                            <span class="status-label">Load Timestamp</span>
                            <span id="loadTimestamp" class="status-value" style="font-size: 0.75rem;">Never</span>
                        </div>
                    </div>
                    
                    <div class="status-card">
                        <h3>Instructions</h3>
                        <div style="font-size: 0.875rem; color: var(--muted); line-height: 1.6;">
                            <p style="margin-bottom: 0.75rem;"><strong style="color: var(--foreground);">Step 1:</strong> Choose data source (Database or XML)</p>
                            <p style="margin-bottom: 0.75rem;"><strong style="color: var(--foreground);">Step 2:</strong> Configure parameters or upload files</p>
                            <p style="margin-bottom: 0.75rem;"><strong style="color: var(--foreground);">Step 3:</strong> Click "Confirm & Load Data"</p>
                            <p style="margin-bottom: 0;"><strong style="color: var(--foreground);">Step 4:</strong> Go to Generate tab to create scenarios</p>
                        </div>
                    </div>
                    
                    <!-- Discovered Attributes Panel (shown only for XML source) -->
                    <div class="status-card" id="attributesPanel" style="display: none;">
                        <h3>Discovered Attributes ✨</h3>
                        <div id="attributesList" style="font-size: 0.75rem; color: var(--muted); max-height: 300px; overflow-y: auto;">
                            <p style="text-align: center; padding: 1rem;">Load XML data to see discovered attributes</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Input Knowledge Tab -->
        <div class="tab-content" id="knowledge-content">
            <div class="grid">
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">📚 Upload Knowledge Documents</h2>
                        <p style="color: var(--muted); font-size: 0.875rem; margin-top: 0.5rem;">
                            Upload documents to provide additional context for the LLM engine during scenario generation
                        </p>
                    </div>
                    
                    <!-- File Upload Area -->
                    <div style="margin-bottom: 2rem;">
                        <div style="border: 2px dashed var(--border); border-radius: 12px; padding: 2rem; text-align: center; background: var(--secondary); transition: all 0.3s;" 
                             id="knowledgeDropZone"
                             ondrop="handleKnowledgeDrop(event)" 
                             ondragover="handleKnowledgeDragOver(event)"
                             ondragleave="handleKnowledgeDragLeave(event)">
                            <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
                            <h3 style="color: var(--foreground); margin-bottom: 0.5rem;">Drop knowledge files here or click to browse</h3>
                            <p style="color: var(--muted); font-size: 0.875rem; margin-bottom: 1rem;">
                                Supported formats: TXT, DOC, DOCX, PDF
                            </p>
                            <input type="file" 
                                   id="knowledgeFileInput" 
                                   multiple 
                                   accept=".txt,.doc,.docx,.pdf"
                                   style="display: none;"
                                   onchange="handleKnowledgeFileSelect(event)">
                            <button class="btn btn-primary" onclick="document.getElementById('knowledgeFileInput').click()">
                                📁 Browse Files
                            </button>
                        </div>
                    </div>
                    
                    <!-- Uploaded Files List -->
                    <div class="card" style="background: var(--card-dark);">
                        <div class="card-header">
                            <h3 class="card-title">Uploaded Knowledge Files</h3>
                        </div>
                        <div id="knowledgeFilesList" style="min-height: 200px;">
                            <div style="text-align: center; padding: 2rem; color: var(--muted);">
                                <div style="font-size: 2rem; margin-bottom: 1rem;">📂</div>
                                <p>No knowledge files uploaded yet</p>
                                <p style="font-size: 0.875rem; margin-top: 0.5rem;">Upload documents to enhance LLM context</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Knowledge Stats & Info -->
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">📊 Knowledge Context Status</h2>
                    </div>
                    
                    <div class="status-card">
                        <h3>Current Status</h3>
                        <div style="margin-top: 1rem;">
                            <div class="status-row">
                                <span style="color: var(--muted);">Files Loaded:</span>
                                <span id="knowledgeFilesCount" style="color: var(--primary); font-weight: 600;">0</span>
                            </div>
                            <div class="status-row">
                                <span style="color: var(--muted);">Total Characters:</span>
                                <span id="knowledgeTotalChars" style="color: var(--primary); font-weight: 600;">0</span>
                            </div>
                            <div class="status-row">
                                <span style="color: var(--muted);">Context Size:</span>
                                <span id="knowledgeContextSize" style="color: var(--primary); font-weight: 600;">0 KB</span>
                            </div>
                            <div class="status-row">
                                <span style="color: var(--muted);">LLM Integration:</span>
                                <span id="knowledgeLLMStatus" style="color: var(--success); font-weight: 600;">✓ Ready</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="status-card" style="margin-top: 1rem;">
                        <h3>💡 How It Works</h3>
                        <ul style="margin: 1rem 0; padding-left: 1.5rem; color: var(--muted); font-size: 0.875rem;">
                            <li style="margin-bottom: 0.5rem;">Upload relevant documents (research, policies, guidelines)</li>
                            <li style="margin-bottom: 0.5rem;">Text is automatically extracted and processed</li>
                            <li style="margin-bottom: 0.5rem;">Content is added to LLM context for scenario generation</li>
                            <li style="margin-bottom: 0.5rem;">LLM uses this knowledge to create more informed scenarios</li>
                        </ul>
                    </div>
                    
                    <div class="status-card" style="margin-top: 1rem;">
                        <h3>📝 Best Practices</h3>
                        <ul style="margin: 1rem 0; padding-left: 1.5rem; color: var(--muted); font-size: 0.875rem;">
                            <li style="margin-bottom: 0.5rem;"><strong>Relevance:</strong> Upload domain-specific documents</li>
                            <li style="margin-bottom: 0.5rem;"><strong>Quality:</strong> Use well-structured, clear text</li>
                            <li style="margin-bottom: 0.5rem;"><strong>Size:</strong> Keep files focused (< 5MB each)</li>
                            <li style="margin-bottom: 0.5rem;"><strong>Format:</strong> PDF and DOCX preferred for formatted documents</li>
                        </ul>
                    </div>
                    
                    <button class="btn" style="width: 100%; margin-top: 1rem;" onclick="clearAllKnowledge()">
                        🗑️ Clear All Knowledge
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Generate Tab -->
        <div class="tab-content" id="generate-content">
            <div class="grid">
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">Scenario Configuration</h2>
                    </div>
                    
                    <!-- Quick Start Examples -->
                    <div class="examples-box">
                        <div class="examples-header">
                            💡 Quick Start Examples
                        </div>
                        <div class="example-chips">
                            <button class="example-chip" onclick="setExample('Generate severe stress scenarios with +200 bps rate shock and credit spread widening')">
                                Rate shock +200bps...
                            </button>
                            <button class="example-chip" onclick="setExample('Model a currency crisis with CHF appreciation and EUR depreciation')">
                                Currency crisis...
                            </button>
                            <button class="example-chip" onclick="setExample('Create recession scenarios with rising unemployment and falling asset prices')">
                                Recession scenarios...
                            </button>
                        </div>
                    </div>
                    
                    <!-- Data Status Indicator -->
                    <div id="generateDataStatus" style="padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; border: 1px solid;">
                        Loading status...
                    </div>
                    
                    <!-- LLM Prompt Selection -->
                    <div style="background: rgba(167, 139, 250, 0.1); border: 1px solid rgba(167, 139, 250, 0.2); border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem;">
                        <div style="display: flex; align-items: center; gap: 8px; color: var(--chart-3); font-weight: 600; margin-bottom: 1rem; font-size: 1rem;">
                            🤖 LLM Engine Configuration
                        </div>
                        
                        <div class="form-group">
                            <label for="promptSelect">Active Prompt</label>
                            <select id="promptSelect" style="width: 100%;" onchange="updatePromptInfo()">
                                <option value="">⚠ Select a prompt (required)</option>
                            </select>
                            <div id="promptInfo" style="margin-top: 0.75rem; padding: 0.75rem; background: var(--secondary); border-radius: 6px; display: none;">
                                <div style="font-size: 0.875rem; color: var(--muted);" id="promptDescription"></div>
                                <div style="font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem;">
                                    <span style="color: var(--foreground); font-weight: 500;">Engine:</span> 
                                    <span id="llmEngine">Llama 3</span>
                                </div>
                            </div>
                            <p style="font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem;">
                                The selected prompt will be injected into the LLM engine to guide scenario generation.
                            </p>
                        </div>
                    </div>
                    
                    <form id="scenarioForm" onsubmit="handleGenerate(event)">
                        <div class="form-group">
                            <label for="instruction">Scenario Instructions</label>
                            <textarea 
                                id="instruction" 
                                placeholder="Describe the scenarios you want to generate...

Example:
Generate 3 stress scenarios for interest rate risk, credit spreads, and FX rates with severe but plausible shocks based on historical crisis events."
                            ></textarea>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label>Number of Scenarios</label>
                                <div class="slider-container">
                                    <input type="range" id="numScenarios" min="1" max="15" value="3" oninput="updateSliderValue()">
                                    <span class="slider-value" id="sliderValue">3</span>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label for="scenarioType">Scenario Type</label>
                                <select id="scenarioType">
                                    <option value="stress">Stress Scenarios</option>
                                    <option value="stochastic">Stochastic Scenarios</option>
                                    <option value="both">Both Types</option>
                                </select>
                                <p style="font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem;" id="typeDescription">
                                    Deterministic scenarios based on specific events
                                </p>
                            </div>
                        </div>
                        
                        <button type="submit" class="btn btn-primary btn-full" id="generateBtn">
                            ▶️ Generate Scenarios
                        </button>
                    </form>
                    
                    <!-- Process Status Panel -->
                    <div id="processStatus" class="hidden" style="margin-top: 2rem; padding: 1.5rem; background: rgba(20, 184, 166, 0.1); border: 1px solid rgba(20, 184, 166, 0.2); border-radius: 12px;">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;">
                            <div class="spinner"></div>
                            <h3 style="font-size: 1rem; font-weight: 600;">Generating Scenarios...</h3>
                        </div>
                        <div id="processSteps" style="font-family: 'JetBrains Mono', monospace; font-size: 0.875rem; color: var(--muted); line-height: 1.8;">
                            <!-- Process steps will be added here -->
                        </div>
                    </div>
                </div>
                
                <!-- Status Panel -->
                <div class="status-panel">
                    <div class="status-card">
                        <h3>Platform Status</h3>
                        <div class="status-row">
                            <span class="status-label">Risk HUB Connection</span>
                            <span class="status-active">
                                <span class="status-dot"></span>
                                Active
                            </span>
                        </div>
                        <div class="status-row">
                            <span class="status-label">LLM Engine</span>
                            <span class="status-active">
                                <span class="status-dot"></span>
                                Llama 3
                            </span>
                        </div>
                        <div class="status-row">
                            <span class="status-label">Active Prompt</span>
                            <span class="status-value" id="platformActivePrompt">-</span>
                        </div>
                        <div class="status-row">
                            <span class="status-label">Contracts Loaded</span>
                            <span class="status-value" id="generateContractsCount">-</span>
                        </div>
                        <div class="status-row">
                            <span class="status-label">Counterparties Loaded</span>
                            <span class="status-value" id="generateCounterpartiesCount">-</span>
                        </div>
                        <div class="status-row">
                            <span class="status-label">Risk Factors</span>
                            <span class="status-value" id="generateRiskFactorsCount">-</span>
                        </div>
                    </div>
                    
                    <div class="status-card">
                        <h3>Recent Activity</h3>
                        <div class="activity-list">
                            <div class="activity-item">
                                <div class="activity-dot active"></div>
                                <div>
                                    <div class="activity-text">System initialized</div>
                                    <div class="activity-time">Just now</div>
                                </div>
                            </div>
                            <div class="activity-item">
                                <div class="activity-dot inactive"></div>
                                <div>
                                    <div class="activity-text">Data cache refreshed</div>
                                    <div class="activity-time">5 min ago</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        
        <!-- Prompts Tab -->
        <div class="tab-content" id="prompts-content">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Expert's Knowledge Templates</h2>
                    <p style="font-size: 0.875rem; color: var(--muted);">Manage your custom prompt templates</p>
                </div>
                
                <div id="promptMessage"></div>
                
                <div style="margin-bottom: 1.5rem;">
                    <table style="width: 100%; border-collapse: collapse;" id="promptsTable">
                        <thead>
                            <tr style="background: var(--secondary); border-bottom: 1px solid var(--border);">
                                <th style="padding: 12px; text-align: left; color: var(--muted); font-size: 0.875rem;">Name</th>
                                <th style="padding: 12px; text-align: left; color: var(--muted); font-size: 0.875rem;">Description</th>
                                <th style="padding: 12px; text-align: left; color: var(--muted); font-size: 0.875rem;">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="promptsTableBody">
                            <tr>
                                <td colspan="3" style="padding: 12px; text-align: center; color: var(--muted);">Loading...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div style="background: var(--secondary); padding: 1.5rem; border-radius: 8px;">
                    <h3 style="margin-bottom: 1rem;">Prompt Editor</h3>
                    
                    <input type="hidden" id="currentPromptId">
                    
                    <div class="form-group">
                        <label for="promptName">Name *</label>
                        <input type="text" id="promptName" placeholder="My Custom Prompt">
                    </div>
                    
                    <div class="form-group">
                        <label for="promptDescription">Description</label>
                        <input type="text" id="promptDescription" placeholder="Brief description">
                    </div>
                    
                    <div class="form-group">
                        <label for="promptText">Prompt Text *</label>
                        <textarea id="promptText" style="min-height: 200px;" placeholder="Enter your prompt..."></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="promptTags">Tags</label>
                        <input type="text" id="promptTags" placeholder="custom, banking">
                    </div>
                    
                    <div style="display: flex; gap: 8px;">
                        <button class="btn btn-primary" onclick="savePrompt()">💾 Save</button>
                        <button class="btn btn-outline" onclick="clearPromptEditor()">Clear</button>
                        <button class="btn btn-outline" onclick="exportPrompts()">📥 Export</button>
                        <button class="btn btn-outline" onclick="document.getElementById('importFileInput').click()">📤 Import</button>
                        <input type="file" id="importFileInput" accept=".json" style="display:none" onchange="importPrompts(event)">
                    </div>
                </div>
            </div>
        </div>
        
<!-- Results Tab -->
        <div class="tab-content" id="results-content">
            <div id="resultsContainer">
                <div class="empty-state">
                    <div class="empty-icon">📈</div>
                    <p>No scenarios generated yet</p>
                    <p style="font-size: 0.875rem;">Generate scenarios to view results</p>
                </div>
            </div>
        </div>
        
        <!-- Documentation Tab -->
        <div class="tab-content" id="docs-content">
            <div class="card docs-content">
                <div class="card-header">
                    <h2 class="card-title">Documentation</h2>
                </div>
                
                <div class="docs-section">
                    <h3>Overview</h3>
                    <p>
                        The ALM Scenario Generator creates stress and stochastic scenarios for your Regnology Risk Hub portfolio
                        using advanced LLM-powered analysis. Generate scenarios based on natural language instructions
                        to model various market conditions and risk events.
                    </p>
                </div>
                
                <div class="docs-section">
                    <h3>Scenario Types</h3>
                    <ul>
                        <li><strong>Stress Scenarios:</strong> Deterministic scenarios based on specific market events like financial crises, rate shocks, or currency devaluations</li>
                        <li><strong>Stochastic Scenarios:</strong> Probabilistic paths generated from statistical models using Monte Carlo simulations and historical distributions</li>
                    </ul>
                </div>
                
                <div class="docs-section">
                    <h3>Impact Metrics</h3>
                    <ul>
                        <li><strong>NII (Net Interest Income):</strong> Measures the impact on interest income from rate-sensitive assets and liabilities</li>
                        <li><strong>EVE (Economic Value of Equity):</strong> Measures the change in economic value of the balance sheet</li>
                        <li><strong>VaR (Value at Risk):</strong> Estimates the potential loss at a given confidence level</li>
                    </ul>
                </div>
                
                <div class="docs-section">
                    <h3>Best Practices</h3>
                    <ul>
                        <li>Use specific instructions describing the economic scenarios you want to model</li>
                        <li>Include magnitude hints (e.g., "+200 bps", "severe", "moderate")</li>
                        <li>Reference historical events for realistic calibration</li>
                        <li>Combine multiple risk factors for comprehensive analysis</li>
                    </ul>
                </div>
            </div>
        </div>
    </main>
    
    <script>
        // ====================================================================
        // GLOBAL VARIABLES
        // ====================================================================
        
        // Knowledge files storage (initialize early to prevent errors)
        let knowledgeFiles = [];
        
        // ====================================================================
        // KNOWLEDGE CONTEXT UTILITIES (defined early to prevent reference errors)
        // ====================================================================
        
        // Get all knowledge text for LLM context
        function getKnowledgeContext() {
            if (!knowledgeFiles || knowledgeFiles.length === 0) return '';
            
            let context = '\\n\\n=== ADDITIONAL KNOWLEDGE CONTEXT ===\\n\\n';
            for (const file of knowledgeFiles) {
                context += '--- From: ' + String(file.name) + ' ---\\n' + String(file.text) + '\\n\\n';
            }
            return context;
        }
        
        // Format file size helper
        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }
        
        // Get file icon based on extension
        function getFileIcon(fileName) {
            const ext = fileName.split('.').pop().toLowerCase();
            const icons = {
                'txt': '📄',
                'doc': '📘',
                'docx': '📘',
                'pdf': '📕'
            };
            return icons[ext] || '📄';
        }
        
        // ====================================================================
        // PROMPTS MANAGEMENT
        // ====================================================================
        
        let allPrompts = [];
        let currentPromptId = null;
        
        async function loadPrompts() {
            try {
                const response = await fetch('/api/prompts');
                const data = await response.json();
                if (data.success) {
                    allPrompts = data.prompts;
                    document.getElementById('promptsBadge').textContent = data.prompts.length;
                    renderPromptsTable(data.prompts);
                }
            } catch (error) {
                console.error('Error loading prompts:', error);
            }
        }
        
        function renderPromptsTable(prompts) {
            const tbody = document.getElementById('promptsTableBody');
            if (!tbody || prompts.length === 0) {
                if (tbody) tbody.innerHTML = '<tr><td colspan="3" style="padding:12px; text-align:center; color:var(--muted)">No prompts yet</td></tr>';
                return;
            }
            
            tbody.innerHTML = prompts.map(p => `
                <tr style="border-bottom: 1px solid var(--border); cursor: pointer;" onclick="editPrompt('${p.id}')">
                    <td style="padding: 12px; font-weight: 600; color: var(--primary);">${p.name}</td>
                    <td style="padding: 12px; color: var(--muted);">${p.description || '-'}</td>
                    <td style="padding: 12px;">
                        <button class="btn btn-outline" style="padding: 6px 12px; font-size: 0.75rem;" onclick="event.stopPropagation(); editPrompt('${p.id}')">Edit</button>
                        ${!p.is_default ? `<button class="btn" style="padding: 6px 12px; font-size: 0.75rem; background: var(--destructive); color: white;" onclick="event.stopPropagation(); deletePrompt('${p.id}')">Delete</button>` : ''}
                    </td>
                </tr>
            `).join('');
        }
        
        function editPrompt(promptId) {
            const prompt = allPrompts.find(p => p.id === promptId);
            if (!prompt) return;
            
            if (prompt.is_default) {
                showPromptMessage('Default prompts cannot be edited', 'error');
                return;
            }
            
            currentPromptId = promptId;
            document.getElementById('currentPromptId').value = promptId;
            document.getElementById('promptName').value = prompt.name;
            document.getElementById('promptDescription').value = prompt.description || '';
            document.getElementById('promptText').value = prompt.prompt_text;
            document.getElementById('promptTags').value = (prompt.tags || []).join(', ');
            
            document.querySelector('.card-header + div + div + div').scrollIntoView({ behavior: 'smooth' });
        }
        
        async function savePrompt() {
            const name = document.getElementById('promptName').value.trim();
            const text = document.getElementById('promptText').value.trim();
            
            if (!name || !text) {
                showPromptMessage('Name and prompt text are required', 'error');
                return;
            }
            
            const data = {
                id: currentPromptId,
                name: name,
                description: document.getElementById('promptDescription').value.trim(),
                prompt_text: text,
                tags: document.getElementById('promptTags').value.split(',').map(t => t.trim()).filter(Boolean)
            };
            
            try {
                const response = await fetch('/api/prompts', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                if (result.success) {
                    showPromptMessage('Prompt saved successfully!', 'success');
                    loadPrompts();
                    clearPromptEditor();
                } else {
                    showPromptMessage('Error: ' + result.error, 'error');
                }
            } catch (err) {
                showPromptMessage('Connection error: ' + err, 'error');
            }
        }
        
        async function deletePrompt(promptId) {
            if (!confirm('Delete this prompt?')) return;
            
            try {
                const response = await fetch(`/api/prompts/${promptId}`, { method: 'DELETE' });
                const data = await response.json();
                
                if (data.success) {
                    showPromptMessage('Prompt deleted', 'success');
                    loadPrompts();
                    clearPromptEditor();
                } else {
                    showPromptMessage('Error: ' + data.error, 'error');
                }
            } catch (err) {
                showPromptMessage('Error: ' + err, 'error');
            }
        }
        
        function clearPromptEditor() {
            currentPromptId = null;
            document.getElementById('currentPromptId').value = '';
            document.getElementById('promptName').value = '';
            document.getElementById('promptDescription').value = '';
            document.getElementById('promptText').value = '';
            document.getElementById('promptTags').value = '';
        }
        
        function exportPrompts() {
            window.location.href = '/api/prompts/export';
        }
        
        async function importPrompts(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = async function(e) {
                try {
                    const prompts = JSON.parse(e.target.result);
                    const response = await fetch('/api/prompts/import', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ prompts: prompts })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        showPromptMessage(`Imported ${data.imported} prompts!`, 'success');
                        loadPrompts();
                    } else {
                        showPromptMessage('Import error: ' + data.error, 'error');
                    }
                } catch (err) {
                    showPromptMessage('Invalid file: ' + err.message, 'error');
                }
            };
            reader.readAsText(file);
            event.target.value = '';
        }
        
        function showPromptMessage(text, type) {
            const container = document.getElementById('promptMessage');
            if (!container) return;
            
            const bgColor = type === 'success' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)';
            const borderColor = type === 'success' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)';
            const textColor = type === 'success' ? 'var(--success)' : 'var(--destructive)';
            
            container.innerHTML = `<div style="background: ${bgColor}; border: 1px solid ${borderColor}; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; color: ${textColor};">${text}</div>`;
            setTimeout(() => { container.innerHTML = ''; }, 3000);
        }
        
        // Load prompts when Prompts tab is opened
        document.addEventListener('DOMContentLoaded', function() {
            loadPrompts();
        });
        

        // Global state
        let currentScenarios = [];
        let currentReport = null;
        let impactChart = null;
        let distributionChart = null;
        
        // Data cache for state management
        let dataCache = {
            loaded: false,
            source: null,  // 'db' or 'xml'
            model_id: null,
            limit: null,
            risk_factors_count: 0,
            counterparties_count: 0,
            contracts_count: 0,
            timestamp: null
        };
        
        // LLM prompt cache
        let promptCache = {
            selected_prompt_id: null,
            selected_prompt_name: null,
            selected_prompt_description: null,
            prompts_loaded: false,
            prompts_list: []
        };
        
        // Load available prompts from Prompts tab
        async function loadAvailablePrompts() {
            try {
                const response = await fetch('/api/prompts');
                const data = await response.json();
                
                if (data.success) {
                    promptCache.prompts_list = data.prompts;
                    promptCache.prompts_loaded = true;
                    
                    // Populate dropdown
                    const select = document.getElementById('promptSelect');
                    select.innerHTML = '<option value="">⚠ Select a prompt (required)</option>';
                    
                    data.prompts.forEach(prompt => {
                        const option = document.createElement('option');
                        option.value = prompt.id;
                        option.textContent = prompt.name;
                        if (prompt.is_default) {
                            option.textContent += ' (Default)';
                        }
                        select.appendChild(option);
                    });
                    
                    // Auto-select default prompt
                    const defaultPrompt = data.prompts.find(p => p.is_default);
                    if (defaultPrompt) {
                        select.value = defaultPrompt.id;
                        updatePromptInfo();
                    }
                    
                    console.log('✓ Loaded', data.prompts.length, 'prompts');
                } else {
                    console.error('Failed to load prompts:', data.error);
                }
            } catch (error) {
                console.error('Error loading prompts:', error);
            }
        }
        
        // Update prompt info when selection changes
        function updatePromptInfo() {
            const select = document.getElementById('promptSelect');
            const promptId = select.value;
            const infoDiv = document.getElementById('promptInfo');
            const descDiv = document.getElementById('promptDescription');
            
            if (!promptId) {
                infoDiv.style.display = 'none';
                promptCache.selected_prompt_id = null;
                promptCache.selected_prompt_name = null;
                promptCache.selected_prompt_description = null;
                document.getElementById('platformActivePrompt').textContent = '-';
                return;
            }
            
            // Find prompt details
            const prompt = promptCache.prompts_list.find(p => p.id === promptId);
            if (prompt) {
                promptCache.selected_prompt_id = prompt.id;
                promptCache.selected_prompt_name = prompt.name;
                promptCache.selected_prompt_description = prompt.description;
                
                // Show info
                infoDiv.style.display = 'block';
                descDiv.textContent = prompt.description || 'No description available';
                
                // Update Platform Status
                document.getElementById('platformActivePrompt').textContent = prompt.name;
                
                console.log('✓ Selected prompt:', prompt.name);
            }
        }
        
        // Show data message (success or error)
        function showDataMessage(message, type) {
            const container = document.getElementById('dataLoadMessage');
            if (!container) return;
            
            const bgColor = type === 'success' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)';
            const borderColor = type === 'success' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)';
            const textColor = type === 'success' ? 'var(--success)' : 'var(--destructive)';
            const icon = type === 'success' ? '✓' : '✗';
            
            container.innerHTML = `
                <div style="background: ${bgColor}; border: 1px solid ${borderColor}; padding: 1rem; border-radius: 8px; color: ${textColor}; white-space: pre-line;">
                    <strong>${icon} ${message}</strong>
                </div>
            `;
        }
        
        // Confirm & Load Data function
        // Global variable to store uploaded files info
        let uploadedXmlFiles = {};
        
        // Handle data source change
        function handleDataSourceChange() {
            const source = document.querySelector('input[name="dataSource"]:checked').value;
            
            document.getElementById('dbParameters').style.display = source === 'db' ? 'block' : 'none';
            document.getElementById('xmlParameters').style.display = source === 'xml' ? 'block' : 'none';
            
            // Clear any previous messages
            showDataMessage('', 'info');
        }
        
        // Handle file selection
        async function handleFileSelect(event) {
            const files = event.target.files;
            if (!files.length) return;
            
            // Upload files
            const formData = new FormData();
            for (let file of files) {
                formData.append('files', file);
            }
            
            // Show uploading state
            const container = document.getElementById('selectedFiles');
            container.innerHTML = '<div style="text-align: center; padding: 1rem; color: var(--muted);"><div class="spinner" style="display: inline-block;"></div> Uploading files...</div>';
            
            try {
                const response = await fetch('/api/upload/xml', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    uploadedXmlFiles = data.files;
                    displaySelectedFiles(files, data.files);
                    showDataMessage(`✓ ${data.count} file(s) uploaded successfully`, 'success');
                } else {
                    showDataMessage('Upload failed: ' + data.error, 'error');
                    container.innerHTML = '';
                }
            } catch (error) {
                showDataMessage('Upload error: ' + error, 'error');
                container.innerHTML = '';
            }
        }
        
        // Display selected files
        function displaySelectedFiles(files, categorizedFiles) {
            const container = document.getElementById('selectedFiles');
            container.innerHTML = '';
            
            // Categorize for display
            const fileTypes = {
                'model': '📋',
                'contracts': '📄',
                'counterparties': '🏢',
                'creditrisk': '⚠️'
            };
            
            for (let file of files) {
                const fileDiv = document.createElement('div');
                fileDiv.className = 'file-item';
                
                // Determine type
                let typeLabel = 'Other';
                let typeIcon = '📁';
                for (let [key, icon] of Object.entries(fileTypes)) {
                    if (file.name.toLowerCase().includes(key)) {
                        typeLabel = key.charAt(0).toUpperCase() + key.slice(1);
                        typeIcon = icon;
                        break;
                    }
                }
                if (file.name.toLowerCase().includes('observation')) {
                    typeLabel = 'Observations';
                    typeIcon = '📊';
                }
                
                fileDiv.innerHTML = `
                    <span class="file-icon">${typeIcon}</span>
                    <span class="file-name">${file.name}</span>
                    <span class="file-type">${typeLabel}</span>
                    <span class="file-size">${(file.size / 1024 / 1024).toFixed(2)} MB</span>
                `;
                container.appendChild(fileDiv);
            }
        }
        
        // Drag and drop support
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                document.getElementById('xmlFileInput').files = files;
                handleFileSelect({target: {files: files}});
            });
        }
        
        async function confirmAndLoadData() {
            const source = document.querySelector('input[name="dataSource"]:checked').value;
            
            const btn = document.getElementById('confirmLoadBtn');
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner"></div> Loading Data...';
            
            try {
                let requestData = {
                    source: source
                };
                
                if (source === 'db') {
                    // Database parameters
                    const modelId = document.getElementById('modelIdInput').value.trim();
                    const applyLimit = document.getElementById('applyLimitCheck').checked;
                    const limitInput = document.getElementById('limitInput').value;
                    const limit = parseInt(limitInput);
                    
                    // Get dataset selection checkboxes
                    const loadContracts = document.getElementById('loadContractsCheck').checked;
                    const loadCounterparties = document.getElementById('loadCounterpartiesCheck').checked;
                    const loadRiskFactorsDB = document.getElementById('loadRiskFactorsDBCheck').checked;
                    
                    // Validate - at least one dataset must be selected
                    if (!loadContracts && !loadCounterparties && !loadRiskFactorsDB) {
                        showDataMessage('Please select at least one dataset to load', 'error');
                        btn.disabled = false;
                        btn.innerHTML = '📥 Confirm & Load Data';
                        return;
                    }
                    
                    // Validate limit
                    if (applyLimit && (!limit || limit <= 0)) {
                        showDataMessage('Please enter a valid limit (positive number)', 'error');
                        btn.disabled = false;
                        btn.innerHTML = '📥 Confirm & Load Data';
                        return;
                    }
                    
                    requestData = {
                        source: 'db',
                        model_id: modelId || null,
                        apply_limit: applyLimit,
                        limit: applyLimit ? limit : null,
                        load_contracts: loadContracts,
                        load_counterparties: loadCounterparties,
                        load_risk_factors_db: loadRiskFactorsDB
                    };
                    
                    console.log('📥 Loading from database:', requestData);
                    
                } else if (source === 'xml') {
                    // XML parameters
                    if (Object.keys(uploadedXmlFiles).length === 0) {
                        showDataMessage('Please upload XML files first', 'error');
                        btn.disabled = false;
                        btn.innerHTML = '📥 Confirm & Load Data';
                        return;
                    }
                    
                    const xmlLimit = document.getElementById('xmlLimit').value;
                    
                    requestData = {
                        source: 'xml',
                        xml_files: uploadedXmlFiles,
                        limit: xmlLimit ? parseInt(xmlLimit) : null
                    };
                    
                    console.log('📥 Loading from XML:', requestData);
                }
                
                const response = await fetch('/api/data/load', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(requestData)
                });
                
                const data = await response.json();
                console.log('Response:', data);
                
                if (data.success) {
                    // Update cache
                    dataCache.loaded = true;
                    dataCache.source = data.source;
                    dataCache.model_id = data.model_id;
                    dataCache.limit = data.limit;
                    dataCache.risk_factors_count = data.risk_factors_count;
                    dataCache.counterparties_count = data.counterparties_count;
                    dataCache.contracts_count = data.contracts_count;
                    dataCache.timestamp = data.timestamp;
                    dataCache.risk_factors_source = data.risk_factors_source || 'Unknown';
                    
                    // Show success message with source info
                    const sourceLabel = data.source === 'db' ? 'Database' : 'XML Files';
                    let message = `✓ Data Loaded Successfully from ${sourceLabel}
Source: ${sourceLabel}
Model ID: ${data.model_id || 'All'}
Limit: ${data.limit ? data.limit.toLocaleString() + ' records' : 'No limit'}`;
                    
                    // Add model parameters if present
                    if (data.model_params_count && data.model_params_count > 0) {
                        message += `
Model Parameters: ${data.model_params_count} sections`;
                    }
                    
                    message += `
Risk Factors: ${data.risk_factors_count} (${data.risk_factors_source || 'Sample'})
Contracts: ${data.contracts_count.toLocaleString()}
Counterparties: ${data.counterparties_count.toLocaleString()}`;
                    
                    showDataMessage(message, 'success');
                    updateDataStatusPanel();
                    updateGenerateDataStatus();
                    
                    console.log('✓ Data cached successfully:', dataCache);
                } else {
                    showDataMessage('Error loading data: ' + data.error, 'error');
                    console.error('Data loading error:', data);
                }
            } catch (error) {
                showDataMessage('Connection error: ' + error, 'error');
                console.error('Connection error:', error);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '📥 Confirm & Load Data';
            }
        }
        
        // Update Data Status Panel
        function updateDataStatusPanel() {
            if (dataCache.loaded) {
                document.getElementById('dataLoadedStatus').textContent = 'Yes';
                document.getElementById('dataLoadedStatus').style.color = 'var(--success)';
                
                // Show data source
                const sourceLabel = dataCache.source === 'db' ? 'Database' : dataCache.source === 'xml' ? 'XML Files' : '-';
                document.getElementById('dataSource').textContent = sourceLabel;
                
                document.getElementById('currentModelId').textContent = dataCache.model_id || 'All';
                document.getElementById('currentLimit').textContent = dataCache.limit ? dataCache.limit.toLocaleString() : 'No limit';
                document.getElementById('riskFactorsCount').textContent = dataCache.risk_factors_count;
                document.getElementById('contractsCount').textContent = dataCache.contracts_count.toLocaleString();
                document.getElementById('counterpartiesCount').textContent = dataCache.counterparties_count.toLocaleString();
                
                if (dataCache.timestamp) {
                    const date = new Date(dataCache.timestamp);
                    document.getElementById('loadTimestamp').textContent = date.toLocaleString();
                }
                
                // Fetch and display discovered attributes for XML source
                if (dataCache.source === 'xml') {
                    fetchDiscoveredAttributes();
                } else {
                    document.getElementById('attributesPanel').style.display = 'none';
                }
            } else {
                document.getElementById('dataLoadedStatus').textContent = 'No';
                document.getElementById('dataLoadedStatus').style.color = 'var(--muted)';
                document.getElementById('attributesPanel').style.display = 'none';
            }
        }
        
        // Fetch and display discovered attributes
        async function fetchDiscoveredAttributes() {
            try {
                const response = await fetch('/api/data/attributes');
                const data = await response.json();
                
                if (data.success && (data.model_parameters || data.counterparties || data.contracts || data.observations)) {
                    const panel = document.getElementById('attributesPanel');
                    const list = document.getElementById('attributesList');
                    
                    panel.style.display = 'block';
                    let html = '';
                    
                    // Display model parameter summary (summary-only, no attribute list)
                    if (data.model_parameters) {
                        html += `
                            <div style="margin-bottom: 1rem;">
                                <div style="color: var(--chart-3); font-weight: 600; margin-bottom: 0.5rem; font-size: 0.875rem;">
                                    ⚙️ Model Parameters (${data.model_parameters.total_attributes} attributes, ${data.model_parameters.total_sections} sections)
                                </div>
                            </div>
                        `;
                    }
                    
                    // Display counterparty attributes
                    if (data.counterparties) {
                        html += `
                            <div style="margin-bottom: 1rem;">
                                <div style="color: var(--primary); font-weight: 600; margin-bottom: 0.5rem; font-size: 0.875rem;">
                                    🏢 Counterparties (${data.counterparties.total_attributes} attributes)
                                </div>
                        `;
                        
                        const allCpAttrs = data.counterparties.attributes.filter(a => a.coverage >= 50);
                        const showInitial = Math.min(8, allCpAttrs.length);
                        
                        // Render initial 8 attributes
                        allCpAttrs.slice(0, showInitial).forEach(attr => {
                            html += `
                                <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: var(--secondary); border-radius: 6px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                                        <span style="color: var(--foreground); font-weight: 500; font-size: 0.75rem;">${attr.name}</span>
                                        <span style="color: ${attr.coverage >= 80 ? 'var(--success)' : 'var(--warning)'}; font-size: 0.75rem;">${attr.populated}/${attr.total}</span>
                                    </div>
                                    ${attr.samples.length > 0 ? `
                                        <div style="font-size: 0.7rem; color: var(--muted);">
                                            ${attr.samples.slice(0, 2).join(', ')}
                                        </div>
                                    ` : ''}
                                </div>
                            `;
                        });
                        
                        // Add expandable section for remaining attributes
                        if (allCpAttrs.length > 8) {
                            html += `<div id="cpAttrsExtra" style="display: none;">`;
                            
                            allCpAttrs.slice(8).forEach(attr => {
                                html += `
                                    <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: var(--secondary); border-radius: 6px;">
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                                            <span style="color: var(--foreground); font-weight: 500; font-size: 0.75rem;">${attr.name}</span>
                                            <span style="color: ${attr.coverage >= 80 ? 'var(--success)' : 'var(--warning)'}; font-size: 0.75rem;">${attr.populated}/${attr.total}</span>
                                        </div>
                                        ${attr.samples.length > 0 ? `
                                            <div style="font-size: 0.7rem; color: var(--muted);">
                                                ${attr.samples.slice(0, 2).join(', ')}
                                            </div>
                                        ` : ''}
                                    </div>
                                `;
                            });
                            
                            html += `</div>`;
                            
                            // Add toggle button
                            html += `
                                <button onclick="toggleAttributes('cpAttrs')" 
                                        style="width: 100%; padding: 0.5rem; margin-top: 0.5rem; 
                                               background: var(--secondary); border: 1px solid var(--border); 
                                               border-radius: 6px; color: var(--primary); cursor: pointer;
                                               font-size: 0.75rem; font-weight: 500; transition: all 0.2s;"
                                        onmouseover="this.style.background='var(--card-hover)'"
                                        onmouseout="this.style.background='var(--secondary)'">
                                    <span id="cpAttrsToggleText">▼ Show ${allCpAttrs.length - 8} more attributes</span>
                                </button>
                            `;
                        }
                        
                        html += `</div>`;
                    }
                    
                    // Display contract attributes
                    if (data.contracts) {
                        html += `
                            <div style="margin-bottom: 1rem;">
                                <div style="color: var(--chart-2); font-weight: 600; margin-bottom: 0.5rem; font-size: 0.875rem;">
                                    📄 Contracts (${data.contracts.total_attributes} attributes)
                                </div>
                        `;
                        
                        const allContractAttrs = data.contracts.attributes.filter(a => a.coverage >= 50);
                        const showInitial = Math.min(8, allContractAttrs.length);
                        
                        // Render initial 8 attributes
                        allContractAttrs.slice(0, showInitial).forEach(attr => {
                            html += `
                                <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: var(--secondary); border-radius: 6px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                                        <span style="color: var(--foreground); font-weight: 500; font-size: 0.75rem;">${attr.name}</span>
                                        <span style="color: ${attr.coverage >= 80 ? 'var(--success)' : 'var(--warning)'}; font-size: 0.75rem;">${attr.populated}/${attr.total}</span>
                                    </div>
                                    ${attr.samples.length > 0 ? `
                                        <div style="font-size: 0.7rem; color: var(--muted);">
                                            ${attr.samples.slice(0, 2).join(', ')}
                                        </div>
                                    ` : ''}
                                </div>
                            `;
                        });
                        
                        // Add expandable section for remaining attributes
                        if (allContractAttrs.length > 8) {
                            html += `<div id="contractAttrsExtra" style="display: none;">`;
                            
                            allContractAttrs.slice(8).forEach(attr => {
                                html += `
                                    <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: var(--secondary); border-radius: 6px;">
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                                            <span style="color: var(--foreground); font-weight: 500; font-size: 0.75rem;">${attr.name}</span>
                                            <span style="color: ${attr.coverage >= 80 ? 'var(--success)' : 'var(--warning)'}; font-size: 0.75rem;">${attr.populated}/${attr.total}</span>
                                        </div>
                                        ${attr.samples.length > 0 ? `
                                            <div style="font-size: 0.7rem; color: var(--muted);">
                                                ${attr.samples.slice(0, 2).join(', ')}
                                            </div>
                                        ` : ''}
                                    </div>
                                `;
                            });
                            
                            html += `</div>`;
                            
                            // Add toggle button
                            html += `
                                <button onclick="toggleAttributes('contractAttrs')" 
                                        style="width: 100%; padding: 0.5rem; margin-top: 0.5rem; 
                                               background: var(--secondary); border: 1px solid var(--border); 
                                               border-radius: 6px; color: var(--primary); cursor: pointer;
                                               font-size: 0.75rem; font-weight: 500; transition: all 0.2s;"
                                        onmouseover="this.style.background='var(--card-hover)'"
                                        onmouseout="this.style.background='var(--secondary)'">
                                    <span id="contractAttrsToggleText">▼ Show ${allContractAttrs.length - 8} more attributes</span>
                                </button>
                            `;
                        }
                        
                        html += `</div>`;
                    }
                    
                    // Display observations/risk factor attributes
                    if (data.observations) {
                        html += `
                            <div style="margin-bottom: 1rem;">
                                <div style="color: var(--chart-4); font-weight: 600; margin-bottom: 0.5rem; font-size: 0.875rem;">
                                    📊 Risk Factors/Observations (${data.observations.total_attributes} attributes, ${data.observations.total_records} records)
                                </div>
                        `;
                        
                        const allObsAttrs = data.observations.attributes.filter(a => a.coverage >= 50);
                        const showInitial = Math.min(8, allObsAttrs.length);
                        
                        // Render initial 8 attributes
                        allObsAttrs.slice(0, showInitial).forEach(attr => {
                            html += `
                                <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: var(--secondary); border-radius: 6px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                                        <span style="color: var(--foreground); font-weight: 500; font-size: 0.75rem;">${attr.name}</span>
                                        <span style="color: ${attr.coverage >= 80 ? 'var(--success)' : 'var(--warning)'}; font-size: 0.75rem;">${attr.populated}/${attr.total}</span>
                                    </div>
                                    ${attr.samples.length > 0 ? `
                                        <div style="font-size: 0.7rem; color: var(--muted);">
                                            ${attr.samples.slice(0, 2).join(', ')}
                                        </div>
                                    ` : ''}
                                </div>
                            `;
                        });
                        
                        // Add expandable section for remaining attributes
                        if (allObsAttrs.length > 8) {
                            html += `<div id="obsAttrsExtra" style="display: none;">`;
                            
                            allObsAttrs.slice(8).forEach(attr => {
                                html += `
                                    <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: var(--secondary); border-radius: 6px;">
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                                            <span style="color: var(--foreground); font-weight: 500; font-size: 0.75rem;">${attr.name}</span>
                                            <span style="color: ${attr.coverage >= 80 ? 'var(--success)' : 'var(--warning)'}; font-size: 0.75rem;">${attr.populated}/${attr.total}</span>
                                        </div>
                                        ${attr.samples.length > 0 ? `
                                            <div style="font-size: 0.7rem; color: var(--muted);">
                                                ${attr.samples.slice(0, 2).join(', ')}
                                            </div>
                                        ` : ''}
                                    </div>
                                `;
                            });
                            
                            html += `</div>`;
                            
                            // Add toggle button
                            html += `
                                <button onclick="toggleAttributes('obsAttrs')" 
                                        style="width: 100%; padding: 0.5rem; margin-top: 0.5rem; 
                                               background: var(--secondary); border: 1px solid var(--border); 
                                               border-radius: 6px; color: var(--primary); cursor: pointer;
                                               font-size: 0.75rem; font-weight: 500; transition: all 0.2s;"
                                        onmouseover="this.style.background='var(--card-hover)'"
                                        onmouseout="this.style.background='var(--secondary)'">
                                    <span id="obsAttrsToggleText">▼ Show ${allObsAttrs.length - 8} more attributes</span>
                                </button>
                            `;
                        }
                        
                        html += `</div>`;
                    }
                    
                    list.innerHTML = html;
                } else {
                    document.getElementById('attributesPanel').style.display = 'none';
                }
            } catch (error) {
                console.error('Error fetching attributes:', error);
                document.getElementById('attributesPanel').style.display = 'none';
            }
        }
        
        // Update Generate tab data status indicator
        function updateGenerateDataStatus() {
            const indicator = document.getElementById('generateDataStatus');
            if (!indicator) return;
            
            if (dataCache.loaded) {
                indicator.style.background = 'rgba(34, 197, 94, 0.1)';
                indicator.style.borderColor = 'rgba(34, 197, 94, 0.2)';
                indicator.innerHTML = `
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <strong style="color: var(--success);">✓ Data Loaded:</strong>
                            <span style="color: var(--foreground);">
                                Model ${dataCache.model_id || 'All'} | 
                                ${dataCache.contracts_count.toLocaleString()} contracts | 
                                ${dataCache.counterparties_count.toLocaleString()} counterparties |
                                ${dataCache.risk_factors_count} risk factors
                            </span>
                        </div>
                        <button type="button" class="btn btn-outline" onclick="switchTab('data')" style="padding: 6px 12px; font-size: 0.875rem;">
                            Reload Data
                        </button>
                    </div>
                `;
                
                // Update Platform Status panel counts
                const contractsEl = document.getElementById('generateContractsCount');
                const counterpartiesEl = document.getElementById('generateCounterpartiesCount');
                const riskFactorsEl = document.getElementById('generateRiskFactorsCount');
                
                if (contractsEl) contractsEl.textContent = dataCache.contracts_count.toLocaleString();
                if (counterpartiesEl) counterpartiesEl.textContent = dataCache.counterparties_count.toLocaleString();
                if (riskFactorsEl) riskFactorsEl.textContent = dataCache.risk_factors_count;
                
            } else {
                indicator.style.background = 'rgba(239, 68, 68, 0.1)';
                indicator.style.borderColor = 'rgba(239, 68, 68, 0.2)';
                indicator.innerHTML = `
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <strong style="color: var(--destructive);">⚠ No Data Loaded</strong>
                            <span style="color: var(--muted); font-size: 0.875rem;">Please load data before generating scenarios</span>
                        </div>
                        <button type="button" class="btn btn-primary" onclick="switchTab('data')" style="padding: 6px 12px; font-size: 0.875rem;">
                            Go to Data Loading
                        </button>
                    </div>
                `;
                
                // Show dashes when no data loaded
                const contractsEl = document.getElementById('generateContractsCount');
                const counterpartiesEl = document.getElementById('generateCounterpartiesCount');
                const riskFactorsEl = document.getElementById('generateRiskFactorsCount');
                
                if (contractsEl) contractsEl.textContent = '-';
                if (counterpartiesEl) counterpartiesEl.textContent = '-';
                if (riskFactorsEl) riskFactorsEl.textContent = '-';
            }
        }
        
        // Tab switching
        function switchTab(tabId) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
            document.getElementById(`${tabId}-content`).classList.add('active');
        }
        
        // Update slider value
        function updateSliderValue() {
            document.getElementById('sliderValue').textContent = document.getElementById('numScenarios').value;
        }
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            updateGenerateDataStatus();
            loadAvailablePrompts();
            console.log('ALM Scenario Generator initialized');
        });
        
        // Update type description
        document.getElementById('scenarioType').addEventListener('change', function() {
            const descriptions = {
                'stress': 'Deterministic scenarios based on specific events',
                'stochastic': 'Probabilistic scenarios from statistical models',
                'both': 'Mix of deterministic and probabilistic scenarios'
            };
            document.getElementById('typeDescription').textContent = descriptions[this.value];
        });
        
        // Set example
        function setExample(text) {
            document.getElementById('instruction').value = text;
        }
        
        // Toggle attributes visibility
        function toggleAttributes(prefix) {
            const extraSection = document.getElementById(`${prefix}Extra`);
            const toggleText = document.getElementById(`${prefix}ToggleText`);
            
            if (extraSection && toggleText) {
                if (extraSection.style.display === 'none') {
                    // Show extra attributes
                    extraSection.style.display = 'block';
                    toggleText.textContent = toggleText.textContent.replace('▼ Show', '▲ Hide');
                } else {
                    // Hide extra attributes
                    extraSection.style.display = 'none';
                    toggleText.textContent = toggleText.textContent.replace('▲ Hide', '▼ Show');
                }
            }
        }
        
        // Show process status
        function showProcessStatus(show = true) {
            const panel = document.getElementById('processStatus');
            const steps = document.getElementById('processSteps');
            if (show) {
                panel.classList.remove('hidden');
                steps.innerHTML = '';
            } else {
                panel.classList.add('hidden');
            }
        }
        
        // Add process step
        function addProcessStep(message, type = 'info') {
            const steps = document.getElementById('processSteps');
            const icons = {
                'info': '📋',
                'success': '✓',
                'prompt': '🧠',
                'llm': '🤖',
                'data': '📊',
                'processing': '⚙️'
            };
            const icon = icons[type] || '•';
            const color = type === 'success' ? 'var(--success)' : 'var(--foreground)';
            
            const step = document.createElement('div');
            step.style.color = color;
            step.innerHTML = `${icon} ${message}`;
            steps.appendChild(step);
            
            // Auto-scroll to bottom
            steps.scrollTop = steps.scrollHeight;
        }
        
        // Handle form submission
        function handleGenerate(event) {
            event.preventDefault();
            
            // Check if data is loaded
            if (!dataCache.loaded) {
                showError('⚠ No Data Loaded! Please go to Data Loading tab and click "Confirm & Load Data" first.');
                return;
            }
            
            // Check if prompt is selected
            const promptId = document.getElementById('promptSelect').value;
            if (!promptId) {
                showError('⚠ No Prompt Selected! Please select an LLM prompt from the dropdown above.');
                return;
            }
            
            const instruction = document.getElementById('instruction').value;
            const numScenarios = parseInt(document.getElementById('numScenarios').value);
            const scenarioType = document.getElementById('scenarioType').value;
            
            if (!instruction.trim()) {
                alert('Please enter scenario instructions');
                return;
            }
            
            const btn = document.getElementById('generateBtn');
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner"></div> Generating Scenarios...';
            
            // Show process status panel
            showProcessStatus(true);
            addProcessStep('Validating configuration...', 'info');
            
            // Get prompt details
            const selectedPrompt = promptCache.prompts_list.find(p => p.id === promptId);
            if (selectedPrompt) {
                addProcessStep(`Using LLM prompt: ${selectedPrompt.name}`, 'prompt');
                addProcessStep(`Description: ${selectedPrompt.description || 'No description'}`, 'info');
            }
            
            addProcessStep('Preparing to inject prompt into LLM context...', 'llm');
            
            // Get knowledge context if available (with safety check)
            let knowledgeContext = '';
            if (typeof getKnowledgeContext === 'function') {
                knowledgeContext = getKnowledgeContext();
                if (knowledgeContext && knowledgeFiles && knowledgeFiles.length > 0) {
                    addProcessStep(`Adding knowledge from ${knowledgeFiles.length} uploaded documents...`, 'info');
                }
            }
            
            addProcessStep(`Requesting ${numScenarios} ${scenarioType} scenarios...`, 'data');
            addProcessStep('Sending request to backend...', 'processing');
            
            fetch('/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    instruction: instruction,
                    num_scenarios: numScenarios,
                    scenario_type: scenarioType,
                    prompt_id: promptId,
                    knowledge_context: knowledgeContext  // Include knowledge context
                })
            })
            .then(r => r.json())
            .then(data => {
                btn.disabled = false;
                btn.innerHTML = '▶️ Generate Scenarios';
                
                if (data.success) {
                    addProcessStep('Scenarios generated successfully!', 'success');
                    addProcessStep(`Generated ${data.scenarios.length} scenarios with ${data.report.totalShocks} shocks`, 'success');
                    addProcessStep('Results available in Reporting tab', 'success');
                    
                    currentScenarios = data.scenarios;
                    currentReport = data.report;
                    displayResults(data.scenarios, data.report, data.csv_file);
                    
                    // Update badge
                    const badge = document.getElementById('resultsBadge');
                    badge.textContent = data.scenarios.length;
                    badge.classList.remove('hidden');
                    
                    // Hide process status after a delay and show success message
                    setTimeout(() => {
                        showProcessStatus(false);
                        // Could show a completion message here
                    }, 3000);
                } else {
                    addProcessStep(`Error: ${data.error}`, 'info');
                    showError(data.error);
                }
            })
            .catch(err => {
                btn.disabled = false;
                btn.innerHTML = '▶️ Generate Scenarios';
                showError('Connection error: ' + err);
            });
        }
        
        // Show error
        function showError(message) {
            addProcessStep(`Error: ${message}`, 'info');
            // Also show in an alert for visibility
            setTimeout(() => {
                alert(`Error: ${message}`);
            }, 100);
        }
        
        // Display results
        function displayResults(scenarios, report, csvFile) {
            const html = generateResultsHTML(scenarios, report, csvFile);
            
            // Results ONLY shown in Reporting tab (not inline in Generate)
            
            // Update Reporting tab with unique chart IDs
            const resultsContainer = document.getElementById('resultsContainer');
            if (resultsContainer) {
                resultsContainer.innerHTML = html;
                
                // Update canvas IDs in Reporting tab to be unique
                const resultsImpactCanvas = resultsContainer.querySelector('#impactChart');
                const resultsDistCanvas = resultsContainer.querySelector('#distributionChart');
                if (resultsImpactCanvas) resultsImpactCanvas.id = 'impactChartResults';
                if (resultsDistCanvas) resultsDistCanvas.id = 'distributionChartResults';
            }
            
            // Initialize charts in both locations after DOM update
            setTimeout(() => {
                // Charts for inline results (Generate tab)
                initCharts(scenarios, report, 'inline');
                
                // Charts for Reporting tab (with updated IDs)
                initCharts(scenarios, report, 'results');
            }, 150);
        }
        
        // Generate results HTML
        function generateResultsHTML(scenarios, report, csvFile) {
            let html = `
                <!-- Success Banner -->
                <div class="success-banner">
                    <div class="success-content">
                        <div class="success-icon">✓</div>
                        <div class="success-text">
                            <h4>Scenarios Generated Successfully</h4>
                            <p>${report.totalScenarios} scenarios with ${report.totalShocks} total shocks</p>
                        </div>
                    </div>
                    <div class="success-actions">
                        <button class="btn btn-outline" onclick="exportCSV()">
                            📥 Export CSV
                        </button>
                    </div>
                </div>
                
                <!-- Stats Grid -->
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-header">
                            <div>
                                <div class="stat-label">Total Scenarios</div>
                                <div class="stat-value">${report.totalScenarios}</div>
                                <div class="stat-subtitle">${report.stressScenarios} stress, ${report.stochasticScenarios} stochastic</div>
                            </div>
                            <div class="stat-icon">🎯</div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-header">
                            <div>
                                <div class="stat-label">Total Shocks</div>
                                <div class="stat-value">${report.totalShocks}</div>
                                <div class="stat-subtitle">Across all scenarios</div>
                            </div>
                            <div class="stat-icon">⚡</div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-header">
                            <div>
                                <div class="stat-label">Avg. NII Impact</div>
                                <div class="stat-value negative">${report.impactSummary.avgNiiImpact}%</div>
                                <div class="stat-subtitle">Net interest income</div>
                            </div>
                            <div class="stat-icon">📉</div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-header">
                            <div>
                                <div class="stat-label">Max VaR</div>
                                <div class="stat-value negative">${report.impactSummary.maxVaR}M</div>
                                <div class="stat-subtitle">Value at Risk</div>
                            </div>
                            <div class="stat-icon">📊</div>
                        </div>
                    </div>
                </div>
                
                <!-- Charts -->
                <div class="charts-grid">
                    <div class="chart-card">
                        <div class="chart-title">Scenario Impact Analysis</div>
                        <div class="chart-container">
                            <canvas id="impactChart"></canvas>
                        </div>
                    </div>
                    <div class="chart-card">
                        <div class="chart-title">Risk Factor Distribution</div>
                        <div class="chart-container">
                            <canvas id="distributionChart"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- Scenarios List -->
                <h3 style="margin-bottom: 1rem;">Generated Scenarios</h3>
                <div class="scenarios-list">
            `;
            
            scenarios.forEach((s, i) => {
                const impact = s.impact || {nii: 0, eve: 0, var: 0};
                html += `
                    <div class="scenario-card">
                        <div class="scenario-header">
                            <div class="scenario-top">
                                <div>
                                    <div class="scenario-meta">
                                        <span class="scenario-id">SCN_${String(i+1).padStart(3, '0')}</span>
                                        <span class="scenario-badge ${s.type === 'stress' ? 'badge-stress' : 'badge-stochastic'}">
                                            ${s.type === 'stress' ? '⚠️ Stress' : '⚡ Stochastic'}
                                        </span>
                                    </div>
                                    <div class="scenario-name">${s.name}</div>
                                </div>
                                <div class="scenario-impacts">
                                    <div class="impact-item">
                                        <div class="impact-label">NII Impact</div>
                                        <div class="impact-value ${impact.nii < 0 ? 'negative' : 'positive'}">${impact.nii > 0 ? '+' : ''}${impact.nii}%</div>
                                    </div>
                                    <div class="impact-item">
                                        <div class="impact-label">EVE Impact</div>
                                        <div class="impact-value ${impact.eve < 0 ? 'negative' : 'positive'}">${impact.eve > 0 ? '+' : ''}${impact.eve}%</div>
                                    </div>
                                </div>
                            </div>
                            <div class="scenario-desc">${s.description}</div>
                            <div class="scenario-footer">
                                <div class="shocks-count">
                                    📉 ${s.num_shocks} shocks applied
                                </div>
                                <button class="toggle-btn" onclick="toggleShocks(${i})">
                                    View Details ▼
                                </button>
                            </div>
                        </div>
                        <div class="shocks-detail" id="shocks-${i}">
                            <div class="shocks-title">Applied Shocks</div>
                            <div class="shocks-list">
                                ${s.shocks.slice(0, 10).map(shock => `
                                    <div class="shock-item">
                                        <div class="shock-info">
                                            <span class="shock-type-badge">${shock.factor_type.replace('_', ' ')}</span>
                                            <span class="shock-factor">${shock.factor_id}</span>
                                        </div>
                                        <div class="shock-value-info">
                                            <span class="shock-method">${shock.shock_type}</span>
                                            <span class="shock-value ${shock.value > 0 ? 'positive' : 'negative'}">${shock.value > 0 ? '+' : ''}${shock.value}</span>
                                        </div>
                                    </div>
                                `).join('')}
                                ${s.num_shocks > 10 ? `<div class="more-shocks">... and ${s.num_shocks - 10} more shocks</div>` : ''}
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                </div>
                
                <div class="success-banner" style="margin-top: 1.5rem;">
                    <div class="success-content">
                        <div class="success-icon">📊</div>
                        <div class="success-text">
                            <h4>Results Saved</h4>
                            <p>${csvFile}</p>
                        </div>
                    </div>
                </div>
            `;
            
            return html;
        }
        
        // Toggle shocks visibility
        function toggleShocks(index) {
            const detail = document.getElementById(`shocks-${index}`);
            detail.classList.toggle('expanded');
            
            // Also check for duplicate in results tab
            const allDetails = document.querySelectorAll(`#shocks-${index}`);
            allDetails.forEach(d => d.classList.toggle('expanded'));
        }
        
        // Initialize charts
        function initCharts(scenarios, report, location = 'inline') {
            // Create unique IDs based on location
            const impactId = location === 'results' ? 'impactChartResults' : 'impactChart';
            const distId = location === 'results' ? 'distributionChartResults' : 'distributionChart';
            
            console.log('Initializing charts for location:', location);
            console.log('Impact ID:', impactId, 'Dist ID:', distId);
            
            // Impact Chart
            const impactCtx = document.getElementById(impactId);
            if (impactCtx) {
                console.log('Found impact canvas:', impactId);
                
                // Destroy existing chart for this location if it exists
                try {
                    const existingChart = Chart.getChart(impactCtx);
                    if (existingChart) {
                        console.log('Destroying existing impact chart');
                        existingChart.destroy();
                    }
                } catch (e) {
                    console.log('No existing impact chart to destroy');
                }
                
                const newImpactChart = new Chart(impactCtx, {
                    type: 'bar',
                    data: {
                        labels: report.scenarioImpacts.map(s => s.name),
                        datasets: [
                            {
                                label: 'NII Impact %',
                                data: report.scenarioImpacts.map(s => s.nii),
                                backgroundColor: 'rgba(20, 184, 166, 0.8)',
                                borderRadius: 4
                            },
                            {
                                label: 'EVE Impact %',
                                data: report.scenarioImpacts.map(s => s.eve),
                                backgroundColor: 'rgba(56, 189, 248, 0.8)',
                                borderRadius: 4
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                labels: { color: 'hsl(215, 20%, 55%)' }
                            }
                        },
                        scales: {
                            x: {
                                ticks: { color: 'hsl(215, 20%, 55%)', font: { size: 10 } },
                                grid: { color: 'hsl(217, 33%, 17%)' }
                            },
                            y: {
                                ticks: { color: 'hsl(215, 20%, 55%)' },
                                grid: { color: 'hsl(217, 33%, 17%)' }
                            }
                        }
                    }
                });
            }
            
            // Distribution Chart
            const distCtx = document.getElementById(distId);
            if (distCtx) {
                if (distributionChart) distributionChart.destroy();
                
                const colors = [
                    'rgba(20, 184, 166, 0.8)',
                    'rgba(56, 189, 248, 0.8)',
                    'rgba(167, 139, 250, 0.8)',
                    'rgba(251, 191, 36, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(148, 163, 184, 0.8)'
                ];
                
                distributionChart = new Chart(distCtx, {
                    type: 'doughnut',
                    data: {
                        labels: report.riskFactorDistribution.map(r => r.name),
                        datasets: [{
                            data: report.riskFactorDistribution.map(r => r.count),
                            backgroundColor: colors.slice(0, report.riskFactorDistribution.length),
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '60%',
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: { 
                                    color: 'hsl(215, 20%, 55%)',
                                    font: { size: 11 },
                                    padding: 12
                                }
                            }
                        }
                    }
                });
            }
        }
        
        // Export CSV
        function exportCSV() {
            if (!currentScenarios.length) return;
            
            let csv = 'Scenario ID,Name,Type,Description,Shocks,NII Impact,EVE Impact,VaR\\n';
            currentScenarios.forEach((s, i) => {
                const impact = s.impact || {nii: 0, eve: 0, var: 0};
                csv += `SCN_${String(i+1).padStart(3, '0')},"${s.name}",${s.type},"${s.description}",${s.num_shocks},${impact.nii},${impact.eve},${impact.var}\\n`;
            });
            
            const blob = new Blob([csv], {type: 'text/csv'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `scenarios_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            URL.revokeObjectURL(url);
        }
        
        // ============================================================================
        // KNOWLEDGE FILE HANDLING
        // ============================================================================
        
        // knowledgeFiles array initialized at top of script
        
        // Handle file drop
        function handleKnowledgeDrop(e) {
            e.preventDefault();
            e.stopPropagation();
            const dropZone = document.getElementById('knowledgeDropZone');
            dropZone.style.borderColor = 'var(--border)';
            dropZone.style.background = 'var(--secondary)';
            
            const files = Array.from(e.dataTransfer.files);
            processKnowledgeFiles(files);
        }
        
        function handleKnowledgeDragOver(e) {
            e.preventDefault();
            e.stopPropagation();
            const dropZone = document.getElementById('knowledgeDropZone');
            dropZone.style.borderColor = 'var(--primary)';
            dropZone.style.background = 'var(--card-hover)';
        }
        
        function handleKnowledgeDragLeave(e) {
            e.preventDefault();
            e.stopPropagation();
            const dropZone = document.getElementById('knowledgeDropZone');
            dropZone.style.borderColor = 'var(--border)';
            dropZone.style.background = 'var(--secondary)';
        }
        
        // Handle file select
        function handleKnowledgeFileSelect(e) {
            const files = Array.from(e.target.files);
            processKnowledgeFiles(files);
            e.target.value = ''; // Reset input
        }
        
        // Process uploaded files
        async function processKnowledgeFiles(files) {
            for (const file of files) {
                // Validate file type
                const validTypes = ['.txt', '.doc', '.docx', '.pdf'];
                const fileExt = '.' + file.name.split('.').pop().toLowerCase();
                
                if (!validTypes.includes(fileExt)) {
                    alert(`Invalid file type: ${file.name}\nSupported: TXT, DOC, DOCX, PDF`);
                    continue;
                }
                
                // Add to pending list
                const fileId = Date.now() + '_' + file.name;
                addKnowledgeFileToUI(fileId, file.name, file.size, 'uploading');
                
                // Upload to backend
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/api/knowledge/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        // Update UI with success
                        updateKnowledgeFileStatus(fileId, 'processed', data);
                        
                        // Store file info
                        knowledgeFiles.push({
                            id: fileId,
                            name: file.name,
                            size: file.size,
                            text: data.text,
                            charCount: data.char_count,
                            wordCount: data.word_count
                        });
                        
                        // Update stats
                        updateKnowledgeStats();
                    } else {
                        updateKnowledgeFileStatus(fileId, 'error', { error: data.error });
                    }
                } catch (error) {
                    console.error('Upload error:', error);
                    updateKnowledgeFileStatus(fileId, 'error', { error: error.message });
                }
            }
        }
        
        // Add file to UI
        function addKnowledgeFileToUI(fileId, fileName, fileSize, status) {
            const list = document.getElementById('knowledgeFilesList');
            
            // Remove empty state if present
            if (list.querySelector('[style*="No knowledge files"]')) {
                list.innerHTML = '';
            }
            
            const fileCard = document.createElement('div');
            fileCard.id = `knowledge-file-${fileId}`;
            fileCard.style.cssText = 'padding: 1rem; border-bottom: 1px solid var(--border);';
            
            const icon = getFileIcon(fileName);
            const sizeStr = formatFileSize(fileSize);
            
            fileCard.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                            <span style="font-size: 1.5rem;">${icon}</span>
                            <div>
                                <div style="font-weight: 600; color: var(--foreground);">${fileName}</div>
                                <div style="font-size: 0.75rem; color: var(--muted);">${sizeStr}</div>
                            </div>
                        </div>
                        <div class="knowledge-file-status" id="status-${fileId}" style="font-size: 0.875rem;">
                            ${status === 'uploading' ? '⏳ Processing...' : ''}
                        </div>
                    </div>
                    <button onclick="removeKnowledgeFile('${fileId}')" 
                            style="background: none; border: none; color: var(--danger); cursor: pointer; font-size: 1.25rem;"
                            title="Remove file">
                        🗑️
                    </button>
                </div>
            `;
            
            list.appendChild(fileCard);
            updateKnowledgeBadge();
        }
        
        // Update file status
        function updateKnowledgeFileStatus(fileId, status, data) {
            const statusEl = document.getElementById(`status-${fileId}`);
            if (!statusEl) return;
            
            if (status === 'processed') {
                statusEl.innerHTML = `
                    <div style="color: var(--success);">✓ Processed & Added to LLM Context</div>
                    <div style="font-size: 0.75rem; color: var(--muted); margin-top: 0.25rem;">
                        ${data.char_count?.toLocaleString() || 0} characters · ${data.word_count?.toLocaleString() || 0} words
                    </div>
                `;
            } else if (status === 'error') {
                statusEl.innerHTML = `
                    <div style="color: var(--danger);">✗ Error: ${data.error}</div>
                `;
            }
        }
        
        // Remove file
        function removeKnowledgeFile(fileId) {
            if (!confirm('Remove this knowledge file?')) return;
            
            // Remove from array
            knowledgeFiles = knowledgeFiles.filter(f => f.id !== fileId);
            
            // Remove from UI
            const fileCard = document.getElementById(`knowledge-file-${fileId}`);
            if (fileCard) fileCard.remove();
            
            // Check if empty
            const list = document.getElementById('knowledgeFilesList');
            if (list.children.length === 0) {
                list.innerHTML = `
                    <div style="text-align: center; padding: 2rem; color: var(--muted);">
                        <div style="font-size: 2rem; margin-bottom: 1rem;">📂</div>
                        <p>No knowledge files uploaded yet</p>
                    </div>
                `;
            }
            
            updateKnowledgeStats();
            updateKnowledgeBadge();
        }
        
        // Clear all knowledge
        function clearAllKnowledge() {
            if (!confirm('Remove all knowledge files? This will clear the LLM context.')) return;
            
            knowledgeFiles = [];
            document.getElementById('knowledgeFilesList').innerHTML = `
                <div style="text-align: center; padding: 2rem; color: var(--muted);">
                    <div style="font-size: 2rem; margin-bottom: 1rem;">📂</div>
                    <p>No knowledge files uploaded yet</p>
                </div>
            `;
            updateKnowledgeStats();
            updateKnowledgeBadge();
        }
        
        // Update statistics
        function updateKnowledgeStats() {
            const totalChars = knowledgeFiles.reduce((sum, f) => sum + (f.charCount || 0), 0);
            const totalBytes = knowledgeFiles.reduce((sum, f) => sum + (f.size || 0), 0);
            
            document.getElementById('knowledgeFilesCount').textContent = knowledgeFiles.length;
            document.getElementById('knowledgeTotalChars').textContent = totalChars.toLocaleString();
            document.getElementById('knowledgeContextSize').textContent = formatFileSize(totalBytes);
        }
        
        // Update badge
        function updateKnowledgeBadge() {
            const badge = document.getElementById('knowledgeBadge');
            const count = knowledgeFiles.length;
            badge.textContent = count;
            if (count > 0) {
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
        
        // Utility functions (getFileIcon, formatFileSize, getKnowledgeContext) 
        // are defined at the top of the script
        
    </script>
</body>
</html>
"""


# ============================================================================
# PROMPT MANAGEMENT API ROUTES
# ============================================================================

@app.route('/api/prompts', methods=['GET'])
def get_prompts():
    try:
        prompts = load_prompts()
        return jsonify({'success': True, 'prompts': prompts})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/prompts', methods=['POST'])
def save_prompt_api():
    try:
        data = request.json
        if not data.get('name') or not data.get('prompt_text'):
            return jsonify({'success': False, 'error': 'Name and prompt text required'}), 400
        
        prompts = load_prompts()
        variables = extract_variables(data['prompt_text'])
        
        prompt_id = data.get('id')
        if prompt_id:
            idx = next((i for i, p in enumerate(prompts) if p['id'] == prompt_id), None)
            if idx is not None:
                prompts[idx].update({
                    'name': data['name'],
                    'description': data.get('description', ''),
                    'prompt_text': data['prompt_text'],
                    'variables': variables,
                    'tags': data.get('tags', []),
                    'updated_at': datetime.now().isoformat()
                })
        else:
            prompts.append({
                'id': generate_prompt_id(data['name']),
                'name': data['name'],
                'description': data.get('description', ''),
                'prompt_text': data['prompt_text'],
                'variables': variables,
                'tags': data.get('tags', []),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'is_default': False
            })
        
        if save_prompts(prompts):
            return jsonify({'success': True, 'prompts': prompts})
        return jsonify({'success': False, 'error': 'Save failed'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/prompts/<prompt_id>', methods=['DELETE'])
def delete_prompt_api(prompt_id):
    try:
        prompts = load_prompts()
        prompt = next((p for p in prompts if p['id'] == prompt_id), None)
        if not prompt:
            return jsonify({'success': False, 'error': 'Not found'}), 404
        if prompt.get('is_default'):
            return jsonify({'success': False, 'error': 'Cannot delete default'}), 400
        
        prompts = [p for p in prompts if p['id'] != prompt_id]
        if save_prompts(prompts):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Delete failed'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/prompts/export', methods=['GET'])
def export_prompts_api():
    try:
        import io
        prompts = load_prompts()
        output = io.BytesIO()
        output.write(json.dumps(prompts, indent=2).encode('utf-8'))
        output.seek(0)
        return send_file(output, mimetype='application/json', as_attachment=True,
                        download_name=f'prompts_{datetime.now().strftime("%Y%m%d")}.json')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/prompts/import', methods=['POST'])
def import_prompts_api():
    try:
        data = request.json
        new_prompts = data.get('prompts', [])
        if not isinstance(new_prompts, list):
            return jsonify({'success': False, 'error': 'Invalid format'}), 400
        
        current = load_prompts()
        existing_ids = {p['id'] for p in current}
        imported = 0
        
        for p in new_prompts:
            if not p.get('name') or not p.get('prompt_text'):
                continue
            if p['id'] in existing_ids:
                p['id'] = generate_prompt_id(p['name'])
            p['updated_at'] = datetime.now().isoformat()
            p['is_default'] = False
            p['variables'] = extract_variables(p['prompt_text'])
            current.append(p)
            imported += 1
        
        if save_prompts(current):
            return jsonify({'success': True, 'imported': imported})
        return jsonify({'success': False, 'error': 'Import failed'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload/xml', methods=['POST'])
def upload_xml():
    """Handle XML file uploads with schema-based type detection"""
    
    def detect_xml_type(filepath):
        """
        Detect XML type based on schema information in the file.
        
        Returns: 'model', 'contracts', 'counterparties', 'observations', or 'creditrisk'
        """
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Get schema location attribute
            schema_attr = root.attrib.get('{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation', '')
            
            # Detect based on schema name
            if 'schema-model' in schema_attr.lower():
                return 'model'
            elif 'schema-contract' in schema_attr.lower():
                return 'contracts'
            elif 'schema-counterpart' in schema_attr.lower():
                return 'counterparties'
            elif 'schema-observation' in schema_attr.lower():
                return 'observations'
            elif 'creditrisk' in schema_attr.lower():
                return 'creditrisk'
            
            # Fallback: analyze Model section contents
            model = root.find('Model')
            if model is not None:
                sections = [child.tag for child in model]
                
                # Check for characteristic sections
                if 'contractEditor' in sections:
                    return 'contracts'
                elif 'counterpartyEditor' in sections:
                    return 'counterparties'
                elif any('Obs' in s or 'observation' in s.lower() for s in sections):
                    return 'observations'
                elif 'yieldCurve' in sections or 'riskFactorConfiguration' in sections:
                    return 'model'
            
            return None
            
        except Exception as e:
            logger.warning(f"Error detecting XML type for {filepath}: {e}")
            return None
    
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files provided'}), 400
        
        uploaded_files = {}
        files = request.files.getlist('files')
        
        print(f"\n{'='*60}")
        print(f"XML File Upload - Received {len(files)} file(s)")
        print(f"{'='*60}")
        
        for file in files:
            if file and file.filename:
                # Secure the filename
                filename = secure_filename(file.filename)
                
                # Save file
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                print(f"  Saved: {filename} → {filepath}")
                
                # Detect XML type based on schema
                detected_type = detect_xml_type(filepath)
                
                if detected_type:
                    print(f"    Schema-detected type: {detected_type}")
                    
                    # Handle observations - can be multiple files
                    if detected_type == 'observations':
                        key = f"observations_{len([k for k in uploaded_files if 'observation' in k])}"
                        uploaded_files[key] = filepath
                    else:
                        uploaded_files[detected_type] = filepath
                else:
                    # Fallback to filename-based detection
                    print(f"    Schema detection failed, using filename...")
                    filename_lower = filename.lower()
                    
                    if 'creditrisk' in filename_lower or 'credit-risk' in filename_lower:
                        uploaded_files['creditrisk'] = filepath
                        print(f"    Categorized as: creditrisk (filename)")
                    elif 'counterpart' in filename_lower:
                        uploaded_files['counterparties'] = filepath
                        print(f"    Categorized as: counterparties (filename)")
                    elif 'contract' in filename_lower and 'counterpart' not in filename_lower:
                        uploaded_files['contracts'] = filepath
                        print(f"    Categorized as: contracts (filename)")
                    elif 'observation' in filename_lower:
                        key = f"observations_{len([k for k in uploaded_files if 'observation' in k])}"
                        uploaded_files[key] = filepath
                        print(f"    Categorized as: {key} (filename)")
                    elif 'model' in filename_lower:
                        uploaded_files['model'] = filepath
                        print(f"    Categorized as: model (filename)")
                    else:
                        uploaded_files[f'unknown_{len(uploaded_files)}'] = filepath
                        print(f"    Categorized as: unknown")
        
        print(f"\nFinal categorization:")
        for key, path in uploaded_files.items():
            print(f"  {key}: {Path(path).name}")
        print(f"{'='*60}\n")
        
        # Store in cache
        cache['uploaded_files'] = uploaded_files
        
        return jsonify({
            'success': True,
            'files': {k: Path(v).name for k, v in uploaded_files.items()},
            'count': len(uploaded_files)
        })
        
    except Exception as e:
        import traceback
        print(f"Error uploading files: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/data/attributes', methods=['GET'])
def get_discovered_attributes():
    """Get discovered attributes from loaded data - both counterparties AND contracts"""
    try:
        if not cache.get('loaded') or cache.get('source') != 'xml':
            return jsonify({'success': False, 'error': 'No XML data loaded'}), 400
        
        result = {
            'success': True,
            'counterparties': None,
            'contracts': None
        }
        
        # Process counterparty attributes
        cp_df = cache.get('counterparties_df')
        if cp_df is not None:
            cp_attributes = []
            for col in sorted(cp_df.columns):
                if col.startswith('_'):
                    continue  # Skip internal fields
                
                non_null = int(cp_df[col].notna().sum())
                total = len(cp_df)
                sample_vals = cp_df[col].dropna().unique()[:3].tolist()
                
                cp_attributes.append({
                    'name': col,
                    'populated': non_null,
                    'total': total,
                    'coverage': round(100 * non_null / total, 1) if total > 0 else 0,
                    'samples': [str(v)[:50] for v in sample_vals]
                })
            
            result['counterparties'] = {
                'total_attributes': len(cp_attributes),
                'total_records': len(cp_df),
                'attributes': cp_attributes
            }
        
        # Process contract attributes
        contracts_df = cache.get('contracts_df')
        if contracts_df is not None:
            contract_attributes = []
            for col in sorted(contracts_df.columns):
                if col.startswith('_'):
                    continue  # Skip internal fields
                
                non_null = int(contracts_df[col].notna().sum())
                total = len(contracts_df)
                sample_vals = contracts_df[col].dropna().unique()[:3].tolist()
                
                contract_attributes.append({
                    'name': col,
                    'populated': non_null,
                    'total': total,
                    'coverage': round(100 * non_null / total, 1) if total > 0 else 0,
                    'samples': [str(v)[:50] for v in sample_vals]
                })
            
            result['contracts'] = {
                'total_attributes': len(contract_attributes),
                'total_records': len(contracts_df),
                'attributes': contract_attributes
            }
        
        # Process observations/risk factor attributes
        obs_df = cache.get('observations_df')
        if obs_df is not None:
            obs_attributes = []
            for col in sorted(obs_df.columns):
                if col.startswith('_'):
                    continue  # Skip internal fields
                
                non_null = int(obs_df[col].notna().sum())
                total = len(obs_df)
                sample_vals = obs_df[col].dropna().unique()[:3].tolist()
                
                obs_attributes.append({
                    'name': col,
                    'populated': non_null,
                    'total': total,
                    'coverage': round(100 * non_null / total, 1) if total > 0 else 0,
                    'samples': [str(v)[:50] for v in sample_vals]
                })
            
            result['observations'] = {
                'total_attributes': len(obs_attributes),
                'total_records': len(obs_df),
                'attributes': obs_attributes
            }
        
        # Process model parameter attributes (NEW!)
        model_params_df = cache.get('model_params_df')
        if model_params_df is not None:
            model_param_attributes = []
            for col in sorted(model_params_df.columns):
                if col.startswith('_'):
                    continue  # Skip internal fields
                
                non_null = int(model_params_df[col].notna().sum())
                total = len(model_params_df)
                sample_vals = model_params_df[col].dropna().unique()[:3].tolist()
                
                model_param_attributes.append({
                    'name': col,
                    'populated': non_null,
                    'total': total,
                    'coverage': round(100 * non_null / total, 1) if total > 0 else 0,
                    'samples': [str(v)[:50] for v in sample_vals]
                })
            
            result['model_parameters'] = {
                'total_attributes': len(model_param_attributes),
                'total_sections': len(model_params_df),
                'attributes': model_param_attributes
            }
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        print(f"Error getting attributes: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/knowledge/upload', methods=['POST'])
def upload_knowledge():
    """
    Upload and process knowledge files (TXT, DOC, DOCX, PDF)
    Extracts text and makes it available for LLM context
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Empty filename'}), 400
        
        # Get file extension
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        # Validate file type
        allowed_extensions = {'txt', 'doc', 'docx', 'pdf'}
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False, 
                'error': f'Unsupported file type: {file_ext}. Allowed: {", ".join(allowed_extensions)}'
            }), 400
        
        # Read file content
        file_content = file.read()
        
        # Extract text based on file type
        extracted_text = ''
        
        if file_ext == 'txt':
            # Plain text - simple decode
            try:
                extracted_text = file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    extracted_text = file_content.decode('latin-1')
                except Exception as e:
                    return jsonify({'success': False, 'error': f'Text decoding error: {e}'}), 400
        
        elif file_ext == 'pdf':
            # PDF - use PyPDF2 or pdfplumber
            try:
                import io
                import PyPDF2
                
                pdf_file = io.BytesIO(file_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                text_parts = []
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())
                
                extracted_text = '\n\n'.join(text_parts)
                
            except ImportError:
                # Fallback: try pdfplumber
                try:
                    import pdfplumber
                    import io
                    
                    pdf_file = io.BytesIO(file_content)
                    with pdfplumber.open(pdf_file) as pdf:
                        text_parts = []
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                text_parts.append(text)
                        extracted_text = '\n\n'.join(text_parts)
                except ImportError:
                    return jsonify({
                        'success': False, 
                        'error': 'PDF extraction requires PyPDF2 or pdfplumber. Install with: pip install PyPDF2'
                    }), 400
            except Exception as e:
                return jsonify({'success': False, 'error': f'PDF extraction error: {e}'}), 400
        
        elif file_ext in ['doc', 'docx']:
            # Word documents - use python-docx
            try:
                import docx
                import io
                
                doc_file = io.BytesIO(file_content)
                doc = docx.Document(doc_file)
                
                text_parts = []
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        text_parts.append(paragraph.text)
                
                extracted_text = '\n\n'.join(text_parts)
                
            except ImportError:
                return jsonify({
                    'success': False, 
                    'error': 'Word document extraction requires python-docx. Install with: pip install python-docx'
                }), 400
            except Exception as e:
                return jsonify({'success': False, 'error': f'Word extraction error: {e}'}), 400
        
        # Calculate statistics
        char_count = len(extracted_text)
        word_count = len(extracted_text.split())
        
        # Basic validation
        if char_count == 0:
            return jsonify({
                'success': False, 
                'error': 'No text could be extracted from the file'
            }), 400
        
        logger.info(f"✓ Knowledge file processed: {filename}")
        logger.info(f"  Characters: {char_count:,}")
        logger.info(f"  Words: {word_count:,}")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'file_type': file_ext,
            'char_count': char_count,
            'word_count': word_count,
            'text': extracted_text,  # Send back to client for context building
            'message': f'Successfully processed {filename}'
        })
        
    except Exception as e:
        import traceback
        logger.error(f"Knowledge upload error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/data/load', methods=['POST'])
def load_data_api():
    """Enhanced data loading endpoint - supports both DB and XML sources"""
    try:
        data = request.json
        source = data.get('source', 'db')  # 'db' or 'xml'
        
        print(f"\n{'='*60}")
        print(f"Data Load Request - Source: {source.upper()}")
        print(f"{'='*60}")
        
        if source == 'db':
            # Database loading (existing logic)
            model_id = data.get('model_id')
            apply_limit = data.get('apply_limit', True)
            limit = data.get('limit', 1000) if apply_limit else None
            
            # Get dataset selection flags
            load_contracts = data.get('load_contracts', True)
            load_counterparties = data.get('load_counterparties', True)
            load_risk_factors_db = data.get('load_risk_factors_db', False)
            
            # Convert empty string to None
            if model_id == '':
                model_id = None
            
            print(f"  Model ID: {model_id or 'All models'}")
            print(f"  Limit: {limit or 'No limit'}")
            print(f"  Load Contracts: {load_contracts}")
            print(f"  Load Counterparties: {load_counterparties}")
            print(f"  Load Risk Factors from DB: {load_risk_factors_db}")
            print(f"{'='*60}\n")
            
            # Load data with configuration
            risk_factors, counterparties, contracts = load_data_with_config(
                model_id=model_id,
                limit=limit,
                load_contracts=load_contracts,
                load_counterparties=load_counterparties,
                load_risk_factors_from_db=load_risk_factors_db
            )
            
            # Determine risk factors source
            risk_factors_source = 'Regnology Risk Hub DB' if load_risk_factors_db else 'Sample Data'
            
            # Update cache
            cache['source'] = 'db'
            cache['model_id'] = model_id or 'All'
        
        elif source == 'xml':
            # XML loading (new functionality)
            xml_files = cache.get('uploaded_files', {})
            limit = data.get('limit')
            
            if not xml_files:
                return jsonify({'success': False, 'error': 'No XML files uploaded'}), 400
            
            print(f"  XML Files: {len(xml_files)}")
            for key, path in xml_files.items():
                print(f"    {key}: {Path(path).name}")
            if limit:
                print(f"  Limit: {limit}")
            print(f"{'='*60}\n")
            
            # Get file paths
            model_xml = xml_files.get('model')
            contracts_xml = xml_files.get('contracts')
            counterparties_xml = xml_files.get('counterparties')
            creditrisk_xml = xml_files.get('creditrisk')
            
            print(f"  File assignments:")
            print(f"    model_xml: {Path(model_xml).name if model_xml else 'None'}")
            print(f"    contracts_xml: {Path(contracts_xml).name if contracts_xml else 'None'}")
            print(f"    counterparties_xml: {Path(counterparties_xml).name if counterparties_xml else 'None'}")
            print(f"    creditrisk_xml: {Path(creditrisk_xml).name if creditrisk_xml else 'None'}")
            
            # Get observations files
            observations_xmls = []
            for key, filepath in xml_files.items():
                if 'observation' in key.lower():
                    observations_xmls.append(filepath)
            
            if observations_xmls:
                print(f"    observations: {len(observations_xmls)} file(s)")
            
            # Validate: at least one XML file of any type must be present
            if not any([model_xml, contracts_xml, counterparties_xml, observations_xmls]):
                return jsonify({'success': False, 'error': 'At least one XML file is required'}), 400
            
            print(f"\n  Loading flags:")
            print(f"    load_risk_factors: {bool(model_xml)}")
            print(f"    load_counterparties: {bool(counterparties_xml)}")
            print(f"    load_contracts: {bool(contracts_xml)}")
            print(f"    load_observations: {bool(observations_xmls)}")
            print(f"{'='*60}\n")
            
            # Load from XML with dynamic attribute extraction
            risk_factors, counterparties, contracts, enriched_data = load_from_xml(
                model_xml=model_xml,
                contracts_xml=contracts_xml,
                counterparties_xml=counterparties_xml,
                creditrisk_xml=creditrisk_xml,
                observations_xmls=observations_xmls,
                limit_contracts=limit,
                load_risk_factors=bool(model_xml),  # Only load if model XML present
                load_counterparties=bool(counterparties_xml),  # Only load if counterparties XML present
                load_contracts=bool(contracts_xml),  # Only load if contracts XML present
                return_enriched=True  # Enable dynamic attribute extraction
            )
            
            print(f"\n{'='*60}")
            print(f"XML LOADING COMPLETED")
            print(f"{'='*60}")
            print(f"  Risk factors loaded: {len(risk_factors)}")
            print(f"  Counterparties loaded: {len(counterparties)}")
            print(f"  Contracts loaded: {len(contracts)}")
            print(f"  Enriched data available: {enriched_data is not None}")
            if enriched_data and enriched_data.get('counterparties_df') is not None:
                print(f"  Counterparty attributes discovered: {len(enriched_data['counterparties_df'].columns)}")
            print(f"{'='*60}\n")
            
            # Set source label based on what was actually loaded
            if len(risk_factors) > 0:
                risk_factors_source = 'XML Files (Model)'
            elif enriched_data and enriched_data.get('observations_df') is not None and len(enriched_data.get('observations_df')) > 0:
                risk_factors_source = 'XML Files (Observations)'
            else:
                risk_factors_source = 'XML Files'
            
            # Update cache with enriched data
            cache['source'] = 'xml'
            cache['model_id'] = 'XML'
            cache['limit'] = limit
            
            # Store enriched data if available
            if enriched_data:
                cache['counterparties_df'] = enriched_data.get('counterparties_df')
                cache['discovered_schema'] = enriched_data.get('discovered_schema')
                cache['contracts_df'] = enriched_data.get('contracts_df')
                cache['contracts_schema'] = enriched_data.get('contracts_schema')
                cache['observations_df'] = enriched_data.get('observations_df')
                cache['observations_schema'] = enriched_data.get('observations_schema')
                cache['model_params'] = enriched_data.get('model_params')  # NEW!
                cache['model_params_df'] = enriched_data.get('model_params_df')  # NEW!
                cache['model_params_schema'] = enriched_data.get('model_params_schema')  # NEW!
                
                cp_attrs = len(enriched_data.get('counterparties_df', {}).columns) if enriched_data.get('counterparties_df') is not None else 0
                contract_attrs = len(enriched_data.get('contracts_df', {}).columns) if enriched_data.get('contracts_df') is not None else 0
                obs_attrs = len(enriched_data.get('observations_df', {}).columns) if enriched_data.get('observations_df') is not None else 0
                model_param_attrs = len(enriched_data.get('model_params_df', {}).columns) if enriched_data.get('model_params_df') is not None else 0  # NEW!
                print(f"  Stored enriched data:")
                if model_param_attrs > 0:  # NEW!
                    print(f"    Model parameter attributes: {model_param_attrs}")
                if cp_attrs > 0:
                    print(f"    Counterparty attributes: {cp_attrs}")
                if contract_attrs > 0:
                    print(f"    Contract attributes: {contract_attrs}")
                if obs_attrs > 0:
                    obs_count = len(enriched_data.get('observations_df')) if enriched_data.get('observations_df') is not None else 0
                    print(f"    Observations: {obs_count} records with {obs_attrs} attributes")
        
        else:
            return jsonify({'success': False, 'error': f'Invalid source: {source}'}), 400
        
        # Common cache updates
        cache['loaded'] = True
        cache['risk_factors'] = risk_factors
        cache['counterparties'] = counterparties
        cache['contracts'] = contracts
        cache['load_timestamp'] = datetime.now().isoformat()
        
        # Calculate risk factors count
        # If we have risk_factors objects, use that count
        # Otherwise, if we have observations data (from XML files), count unique risk factors there
        risk_factors_count = len(risk_factors) if risk_factors else 0
        
        # If risk_factors is empty but we have observations data, use that instead
        if risk_factors_count == 0 and enriched_data and enriched_data.get('observations_df') is not None:
            obs_df = enriched_data.get('observations_df')
            # Count unique combinations of currency + factor type as risk factors
            if 'currency_from_currency' in obs_df.columns:
                risk_factors_count = len(obs_df['currency_from_currency'].unique())
                print(f"  Counting risk factors from observations: {risk_factors_count} unique currencies")
            elif len(obs_df) > 0:
                # Just use the record count as an approximation
                risk_factors_count = len(obs_df)
                print(f"  Counting risk factors from observations: {risk_factors_count} observation records")
        
        # Calculate model parameters count
        model_params_count = 0
        if enriched_data and enriched_data.get('model_params_df') is not None:
            model_params_count = len(enriched_data.get('model_params_df'))
            print(f"  Model parameters: {model_params_count} configuration sections")
        
        # Return metadata
        result_data = {
            'success': True,
            'source': source,
            'model_id': cache['model_id'],
            'limit': cache.get('limit'),
            'risk_factors_count': risk_factors_count,
            'risk_factors_source': risk_factors_source,
            'contracts_count': len(contracts),
            'counterparties_count': len(counterparties),
            'model_params_count': model_params_count,  # NEW!
            'timestamp': cache['load_timestamp']
        }
        
        print(f"\n{'='*60}")
        print(f"RETURNING TO CLIENT:")
        print(f"{'='*60}")
        print(f"  risk_factors_count: {result_data['risk_factors_count']}")
        print(f"  model_params_count: {result_data['model_params_count']}")  # NEW!
        print(f"  contracts_count: {result_data['contracts_count']}")
        print(f"  counterparties_count: {result_data['counterparties_count']}")
        print(f"  risk_factors type: {type(risk_factors)}")
        print(f"  risk_factors length: {len(risk_factors) if risk_factors else 0}")
        print(f"{'='*60}\n")
        
        return jsonify(result_data)
        
    except Exception as e:
        import traceback
        print(f"✗ Error loading data: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

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
        prompt_id = data.get('prompt_id')
        
        print(f"\n{'='*60}")
        print(f"Web request:")
        print(f"  Instruction: {instruction[:100]}...")
        print(f"  Num scenarios: {num_scenarios}")
        print(f"  Type: {scenario_type}")
        print(f"  Prompt ID: {prompt_id}")
        print(f"{'='*60}\n")
        
        # Validate prompt is provided
        if not prompt_id:
            return jsonify({'success': False, 'error': 'No prompt selected. Please select an LLM prompt first.'}), 400
        
        # Load the selected prompt
        prompts = load_prompts()
        selected_prompt = next((p for p in prompts if p['id'] == prompt_id), None)
        
        if not selected_prompt:
            return jsonify({'success': False, 'error': f'Prompt {prompt_id} not found'}), 400
        
        print(f"🤖 Using LLM prompt: {selected_prompt['name']}")
        print(f"   Description: {selected_prompt.get('description', 'N/A')}")
        
        # Use cached data (must be loaded via /api/data/load first)
        try:
            risk_factors, counterparties, contracts = get_cached_data()
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        
        # Initialize LLM client
        llm_client = LlamaClient(base_url="http://localhost:11434", model_name="llama3")
        generator = ALMScenarioGenerator(llm_client)
        
        # Get knowledge context if available
        knowledge_context = data.get('knowledge_context', '')
        
        # Inject custom prompt by prepending to instruction
        prompt_text = selected_prompt.get('prompt_text', '')
        
        # Build full instruction with prompt, knowledge, and user request
        instruction_parts = []
        
        # Add system prompt
        if prompt_text:
            instruction_parts.append(f"System Context:\n{prompt_text}")
        
        # Add knowledge context
        if knowledge_context:
            instruction_parts.append(f"Additional Knowledge:\n{knowledge_context}")
            print(f"📚 Added knowledge context ({len(knowledge_context)} characters)")
        
        # Add user request
        instruction_parts.append(f"User Request:\n{instruction}")
        
        full_instruction = '\n\n'.join(instruction_parts)
        print(f"📝 Instruction built with {len(instruction_parts)} components")
        
        print("Generating scenarios...")
        scenarios, df = generator.generate_scenarios(
            risk_factors=risk_factors,
            counterparties=counterparties,
            contracts=contracts,
            user_instruction=full_instruction,
            num_scenarios=num_scenarios,
            scenario_type=scenario_type
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
                # Count factor types
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
        
        # Generate report data
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
            'csv_file': csv_file
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

if __name__ == '__main__':
    print("=" * 60)
    print("   ALM SCENARIO GENERATOR - PROFESSIONAL WEB INTERFACE")
    print("=" * 60)
    print()
    print("  🌐 Open in browser: http://localhost:8081")
    print("  🔗 Network access:  http://YOUR_IP:8081")
    print()
    print("  Features:")
    print("    • Professional dark fintech theme")
    print("    • Interactive charts and reports")
    print("    • Real-time scenario generation")
    print("    • CSV export functionality")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8081, debug=False)
