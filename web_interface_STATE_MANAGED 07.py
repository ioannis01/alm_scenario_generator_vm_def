"""
Professional Web Interface for ALM Scenario Generator
Enhanced with dark fintech theme, charts, and comprehensive reports
"""

from flask import Flask, render_template_string, request, jsonify, send_file
from alm_scenarios import ALMScenarioGenerator, LlamaClient
#from load_from_Risk HUB import load_from_Risk HUB
from load_alm_data import load_from_riskpro

import json
import random
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

app = Flask(__name__)

# Enhanced cache with metadata for state management
cache = {
    'loaded': False,
    'risk_factors': None,
    'counterparties': None,
    'contracts': None,
    'model_id': None,
    'limit': None,
    'load_timestamp': None
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

def load_data_with_config(model_id=None, limit=None):
    """Load data with specific configuration and cache it"""
    print(f"📊 Loading data with config: model_id={model_id}, limit={limit}")
    
    # Call load_from_Risk HUB with parameters
    risk_factors, counterparties, contracts = load_from_riskpro(
        model_id=model_id,
        limit_contracts=limit
    )
    
    # Store in cache with metadata
    cache['loaded'] = True
    cache['risk_factors'] = risk_factors
    cache['counterparties'] = counterparties
    cache['contracts'] = contracts
    cache['model_id'] = model_id
    cache['limit'] = limit
    cache['load_timestamp'] = datetime.now().isoformat()
    
    print(f"✓ Loaded {len(contracts)} contracts, {len(counterparties)} counterparties")
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
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary), var(--chart-2));
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
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
    </style>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="header-content">
            <div class="logo">
                <div class="logo-icon">📊</div>
                <div class="logo-text">
                    <h1>ALM Scenario Generator</h1>
                    <p>Asset Liability Management Platform</p>
                </div>
            </div>
            <div class="header-status">
                <div class="status-item">
                    <div class="status-dot"></div>
                    <span>Risk HUB Connected</span>
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
                            Configure data sources for scenario generation
                        </p>
                    </div>
                    
                    <div id="dataLoadMessage"></div>
                    
                    <!-- Risk HUB Data Section -->
                    <div style="background: rgba(20, 184, 166, 0.05); border: 1px solid rgba(20, 184, 166, 0.2); border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem;">
                        <div style="display: flex; align-items: center; gap: 8px; color: var(--primary); font-weight: 600; margin-bottom: 1rem; font-size: 1rem;">
                            🏦 Risk HUB Database
                        </div>
                        
                        <div class="form-group">
                            <label for="modelIdInput">Model ID (Optional)</label>
                            <input type="text" 
                                   id="modelIdInput" 
                                   placeholder="Enter Model ID (e.g., 10002) or leave empty for all models" 
                                   style="width: 100%; padding: 10px 14px; background: var(--secondary); border: 1px solid var(--border); border-radius: 8px; color: var(--foreground); font-size: 0.875rem;">
                            <p style="font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem;">
                                Data will load automatically when you click "Generate Scenarios"
                            </p>
                        </div>
                        
                        <div class="form-group">
                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; margin-bottom: 0.5rem;">
                                <input type="checkbox" id="applyLimitCheck" checked>
                                <span>Apply record limit</span>
                            </label>
                            <input type="number" id="limitInput" value="1000" min="1" max="100000" step="100" style="width: 100%;" placeholder="Maximum records to load">
                            <p style="font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem;">
                                Recommended: 1000-5000 for testing. Uncheck for production (loads all data).
                            </p>
                        </div>
                        
                        <div id="dataLoadMessage" style="margin-bottom: 1rem;"></div>
                        
                        <button class="btn btn-primary btn-full" onclick="confirmAndLoadData()" id="confirmLoadBtn">
                            📥 Confirm & Load Data
                        </button>
                        <p style="font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem; text-align: center;">
                            Click to load data into memory. Data will be cached for scenario generation.
                        </p>
                    </div>
                    
                    <!-- Future Data Sources Section (Placeholder) -->
                    <div style="background: rgba(148, 163, 184, 0.05); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 10px; padding: 1.5rem; opacity: 0.6;">
                        <div style="display: flex; align-items: center; gap: 8px; color: var(--muted); font-weight: 600; margin-bottom: 1rem; font-size: 1rem;">
                            📊 Additional Data Sources
                            <span style="background: var(--muted); color: var(--background); padding: 2px 8px; border-radius: 4px; font-size: 0.7rem;">Coming Soon</span>
                        </div>
                        <p style="font-size: 0.875rem; color: var(--muted);">
                            Future versions will support:
                        </p>
                        <ul style="color: var(--muted); font-size: 0.875rem; padding-left: 1.5rem; margin-top: 0.5rem;">
                            <li>Market data file uploads (CSV, Excel)</li>
                            <li>External system integrations</li>
                            <li>Custom data connectors</li>
                        </ul>
                    </div>
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
                            <p style="margin-bottom: 0.75rem;"><strong style="color: var(--foreground);">Step 1:</strong> Enter Model ID and configure limit</p>
                            <p style="margin-bottom: 0.75rem;"><strong style="color: var(--foreground);">Step 2:</strong> Click "Confirm & Load Data" to load into memory</p>
                            <p style="margin-bottom: 0.75rem;"><strong style="color: var(--foreground);">Step 3:</strong> Verify data in "Current Data Status" panel</p>
                            <p style="margin-bottom: 0;"><strong style="color: var(--foreground);">Step 4:</strong> Go to Generate tab to create scenarios</p>
                        </div>
                    </div>
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
            
            <!-- Results (shown inline after generation) -->
            <div id="inlineResults" class="results-section hidden"></div>
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
                        The ALM Scenario Generator creates stress and stochastic scenarios for your Risk HUB portfolio
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
        async function confirmAndLoadData() {
            const modelId = document.getElementById('modelIdInput').value.trim();
            const applyLimit = document.getElementById('applyLimitCheck').checked;
            const limitInput = document.getElementById('limitInput').value;
            const limit = parseInt(limitInput);
            
            // Validate
            if (applyLimit && (!limit || limit <= 0)) {
                showDataMessage('Please enter a valid limit (positive number)', 'error');
                return;
            }
            
            const btn = document.getElementById('confirmLoadBtn');
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner"></div> Loading Data...';
            
            console.log('📥 Confirming and loading data:', {modelId, applyLimit, limit});
            
            try {
                const response = await fetch('/api/data/load', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        model_id: modelId || null,
                        apply_limit: applyLimit,
                        limit: applyLimit ? limit : null
                    })
                });
                
                const data = await response.json();
                console.log('Response:', data);
                
                if (data.success) {
                    // Update cache
                    dataCache.loaded = true;
                    dataCache.model_id = data.model_id;
                    dataCache.limit = data.limit;
                    dataCache.risk_factors_count = data.risk_factors_count;
                    dataCache.counterparties_count = data.counterparties_count;
                    dataCache.contracts_count = data.contracts_count;
                    dataCache.timestamp = data.timestamp;
                    
                    // Show success message
                    const message = `✓ Data Loaded Successfully
Model ID: ${data.model_id || 'All'}
Limit: ${data.limit ? data.limit.toLocaleString() + ' records' : 'No limit'}
Risk Factors: ${data.risk_factors_count}
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
                
                document.getElementById('currentModelId').textContent = dataCache.model_id || 'All';
                document.getElementById('currentLimit').textContent = dataCache.limit ? dataCache.limit.toLocaleString() : 'No limit';
                document.getElementById('riskFactorsCount').textContent = dataCache.risk_factors_count;
                document.getElementById('contractsCount').textContent = dataCache.contracts_count.toLocaleString();
                document.getElementById('counterpartiesCount').textContent = dataCache.counterparties_count.toLocaleString();
                
                if (dataCache.timestamp) {
                    const date = new Date(dataCache.timestamp);
                    document.getElementById('loadTimestamp').textContent = date.toLocaleString();
                }
            } else {
                document.getElementById('dataLoadedStatus').textContent = 'No';
                document.getElementById('dataLoadedStatus').style.color = 'var(--muted)';
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
            
            fetch('/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    instruction: instruction,
                    num_scenarios: numScenarios,
                    scenario_type: scenarioType,
                    prompt_id: promptId
                })
            })
            .then(r => r.json())
            .then(data => {
                btn.disabled = false;
                btn.innerHTML = '▶️ Generate Scenarios';
                
                if (data.success) {
                    currentScenarios = data.scenarios;
                    currentReport = data.report;
                    displayResults(data.scenarios, data.report, data.csv_file);
                    
                    // Update badge
                    const badge = document.getElementById('resultsBadge');
                    badge.textContent = data.scenarios.length;
                    badge.classList.remove('hidden');
                } else {
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
            const container = document.getElementById('inlineResults');
            container.innerHTML = `<div class="error-banner">❌ Error: ${message}</div>`;
            container.classList.remove('hidden');
        }
        
        // Display results
        function displayResults(scenarios, report, csvFile) {
            const html = generateResultsHTML(scenarios, report, csvFile);
            
            // Show inline in Generate tab
            const inlineContainer = document.getElementById('inlineResults');
            inlineContainer.innerHTML = html;
            inlineContainer.classList.remove('hidden');
            
            // Update Reporting tab with unique chart IDs
            const resultsContainer = document.getElementById('resultsContainer');
            resultsContainer.innerHTML = html;
            
            // Update canvas IDs in Reporting tab to be unique
            const resultsImpactCanvas = resultsContainer.querySelector('#impactChart');
            const resultsDistCanvas = resultsContainer.querySelector('#distributionChart');
            if (resultsImpactCanvas) resultsImpactCanvas.id = 'impactChartResults';
            if (resultsDistCanvas) resultsDistCanvas.id = 'distributionChartResults';
            
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

@app.route('/api/data/load', methods=['POST'])
def load_data_api():
    """Explicit data loading endpoint"""
    try:
        data = request.json
        model_id = data.get('model_id')
        apply_limit = data.get('apply_limit', True)
        limit = data.get('limit', 1000) if apply_limit else None
        
        # Convert empty string to None
        if model_id == '':
            model_id = None
            
        print(f"\n{'='*60}")
        print(f"Data Load Request:")
        print(f"  Model ID: {model_id or 'All models'}")
        print(f"  Limit: {limit or 'No limit'}")
        print(f"{'='*60}\n")
        
        # Load data with configuration
        risk_factors, counterparties, contracts = load_data_with_config(
            model_id=model_id,
            limit=limit
        )
        
        # Return metadata
        return jsonify({
            'success': True,
            'model_id': model_id or 'All',
            'limit': limit,
            'risk_factors_count': len(risk_factors) if risk_factors else 0,
            'contracts_count': len(contracts),
            'counterparties_count': len(counterparties),
            'timestamp': cache['load_timestamp']
        })
        
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
        
        # Inject custom prompt by prepending to instruction
        prompt_text = selected_prompt.get('prompt_text', '')
        if prompt_text:
            # Prepend prompt context to user instruction
            full_instruction = f'''System Context:
{prompt_text}

User Request:
{instruction}'''
            print(f"📝 Injected prompt into instruction context")
        else:
            full_instruction = instruction
        
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
