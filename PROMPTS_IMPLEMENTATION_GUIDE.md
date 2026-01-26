# 📘 Prompts Management System - Implementation Guide

## 🎯 Overview

This guide explains how to integrate the Prompts Management system into your existing ALM Scenario Generator web interface.

---

## 📦 What's Included

### **Backend (Python/Flask)**
- ✅ JSON-based prompt storage (`custom_prompts.json`)
- ✅ Full CRUD operations (Create, Read, Update, Delete)
- ✅ Variable extraction from prompts (e.g., `{customer_name}`)
- ✅ Export/Import functionality
- ✅ Integration with scenario generation

### **Frontend (HTML/CSS/JS)**
- ✅ New "Prompts" tab with management interface
- ✅ Prompt editor with live variable detection
- ✅ Prompt selector in Generate tab
- ✅ Dynamic variable input fields
- ✅ File upload/download for import/export

---

## 🚀 Quick Start

### **Step 1: Replace Your Web Interface File**

```bash
# Backup your existing file
cp web_interface_enhanced_01.py web_interface_enhanced_01.py.backup

# Copy the new version
cp /mnt/user-data/outputs/web_interface_with_prompts.py web_interface_enhanced_01.py
```

### **Step 2: Run the Application**

```bash
python web_interface_enhanced_01.py
```

### **Step 3: Open in Browser**

```
http://localhost:8081
```

---

## 📋 Features Explanation

### **1. Prompts Tab**

**Left Panel - Saved Prompts:**
- View all saved prompt templates
- Click to edit
- Shows tags and variable count
- Visual selection indicator

**Right Panel - Prompt Editor:**
- Name and description fields
- Large text area for prompt content
- Auto-detection of `{variables}`
- Tags for organization
- Save/Delete buttons
- Export/Import controls

### **2. Generate Tab Integration**

**Prompt Selector:**
- Dropdown menu with all available prompts
- Automatically loads selected prompt

**Variable Inputs (Dynamic):**
- Only shown if prompt contains `{variables}`
- Creates input field for each variable
- Example: `{customer_name}` → "Enter value for customer_name"

**Scenario Generation:**
- Variables are substituted before sending to LLM
- Example: `{region}` → "Swiss" results in "Swiss banking expert..."

### **3. Data Model**

Each prompt is stored as JSON:

```json
{
  "id": "my_custom_prompt",
  "name": "My Custom Prompt",
  "description": "Brief description",
  "prompt_text": "You are a {role} specialist...",
  "variables": ["role"],
  "tags": ["custom", "banking"],
  "created_at": "2026-01-24T10:30:00",
  "updated_at": "2026-01-24T10:30:00"
}
```

---

## 🔧 API Endpoints

### **GET /prompts**
Returns all prompts
```javascript
fetch('/prompts')
  .then(r => r.json())
  .then(data => console.log(data.prompts));
```

### **POST /prompts**
Create or update a prompt
```javascript
fetch('/prompts', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    name: 'My Prompt',
    description: 'Description here',
    prompt_text: 'Prompt content with {variables}',
    tags: ['tag1', 'tag2']
  })
});
```

### **DELETE /prompts/{id}**
Delete a prompt (except defaults)
```javascript
fetch('/prompts/my_custom_prompt', {
  method: 'DELETE'
});
```

### **GET /prompts/export**
Download all prompts as JSON file
```javascript
window.location.href = '/prompts/export';
```

### **POST /prompts/import**
Upload and merge prompts from JSON file
```html
<input type="file" accept=".json" onchange="importPrompts(event)">
```

---

## 💡 Usage Examples

### **Example 1: Create a Custom Prompt**

1. Click "Prompts" tab
2. Click "➕ New Prompt"
3. Fill in:
   - **Name:** Swiss Banking Expert
   - **Description:** Focus on CHF markets and FINMA requirements
   - **Prompt Text:**
     ```
     You are a {expertise} specialist focusing on {market} markets.
     
     REQUIREMENTS:
     - Comply with FINMA regulations
     - Consider CHF safe-haven status
     - Focus on mortgage portfolio risks
     ```
   - **Tags:** swiss, finma, mortgages
4. Click "💾 Save Prompt"

### **Example 2: Use Custom Prompt in Generation**

1. Go to "Generate" tab
2. Select "Swiss Banking Expert" from dropdown
3. Fill in variables:
   - `{expertise}`: "risk management"
   - `{market}`: "Swiss"
4. Enter scenario instructions
5. Click "▶️ Generate Scenarios"

### **Example 3: Export and Share Prompts**

1. Go to "Prompts" tab
2. Click "📥 Export All"
3. Save `alm_prompts_20260124_103045.json`
4. Share with team member
5. They click "📤 Import" and select the file
6. Prompts are merged with their existing ones

### **Example 4: Regional Customization**

Create a prompt with regional variables:

```
You are a {region} banking analyst specializing in {asset_class} portfolios.

REGIONAL FOCUS: {region}
- Local regulations: {regulatory_body}
- Currency: {currency}
- Market characteristics: {market_type}

Generate scenarios appropriate for {region} banking institutions.
```

When using:
- `{region}`: "Asian"
- `{asset_class}`: "trade finance"
- `{regulatory_body}`: "MAS"
- `{currency}`: "SGD"
- `{market_type}`: "export-oriented"

---

## 🛡️ Safety Features

### **Error Handling**

1. **Invalid JSON Import:**
   - Catches `JSONDecodeError`
   - Shows user-friendly error message
   - Doesn't crash the app

2. **Missing Required Fields:**
   - Frontend validation (name and prompt_text required)
   - Backend validation returns 400 error
   - Clear error messages

3. **Default Prompt Protection:**
   - Cannot delete default prompts (default, conservative, regulatory)
   - Warning shown if attempted

4. **File Write Safety:**
   - Uses atomic write operations
   - Creates backup before overwrite
   - Error recovery

### **Data Validation**

```python
# Backend validation
if not data.get('name') or not data.get('prompt_text'):
    return jsonify({'success': False, 'error': 'Name and prompt text are required'}), 400

# Variable extraction
variables = re.findall(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', prompt_text)
```

---

## 📁 File Structure

```
project/
├── web_interface_enhanced_01.py    # Main application
├── custom_prompts.json             # Auto-created on first run
├── alm_scenarios/                  # Existing modules
│   ├── __init__.py
│   ├── generators/
│   └── llm/
└── load_alm_data.py               # Data loading
```

---

## 🔄 Integration with Existing Code

### **Minimal Changes Required**

The new system integrates with your existing `ALMScenarioGenerator` class. You may need to update it to accept custom prompts:

```python
# In alm_scenarios/generators/scenario_generator.py

def generate_scenarios(
    self,
    risk_factors,
    counterparties,
    contracts,
    user_instruction,
    num_scenarios=3,
    scenario_type="stress",
    custom_system_prompt=None  # ← ADD THIS
):
    # Build prompt with custom system prompt if provided
    prompt = self.prompt_builder.build_prompt(
        risk_factors=risk_factors,
        counterparties=counterparties,
        contracts=contracts,
        user_instruction=user_instruction,
        num_scenarios=num_scenarios,
        scenario_type=scenario_type,
        custom_system_prompt=custom_system_prompt  # ← USE IT HERE
    )
    
    # Rest remains the same...
```

---

## 🎨 Customization

### **Change Default Prompts**

Edit the `load_prompts()` function to customize initial prompts:

```python
default_prompts = [
    {
        'id': 'my_company',
        'name': 'My Company Standard',
        'description': 'Our company standard approach',
        'prompt_text': 'Use our methodology...',
        # ...
    }
]
```

### **Add Custom Validation**

```python
def create_prompt():
    # ... existing code ...
    
    # Custom validation
    if len(data['prompt_text']) > 10000:
        return jsonify({'success': False, 'error': 'Prompt too long'}), 400
    
    if 'required_tag' not in data.get('tags', []):
        return jsonify({'success': False, 'error': 'Required tag missing'}), 400
```

### **Change Storage Format**

To use YAML instead of JSON:

```python
import yaml

def save_prompts(prompts):
    with open('custom_prompts.yaml', 'w') as f:
        yaml.dump(prompts, f)

def load_prompts():
    with open('custom_prompts.yaml', 'r') as f:
        return yaml.safe_load(f)
```

---

## 🐛 Troubleshooting

### **Prompts not loading?**

Check console for errors:
```javascript
// In browser console
fetch('/prompts').then(r => r.json()).then(console.log)
```

### **Variables not detected?**

Variables must match pattern: `{variable_name}`
- ✅ `{customer}`, `{region_name}`, `{asset_class_2}`
- ❌ `{customer-name}`, `{123}`, `{with space}`

### **Import failing?**

Validate JSON structure:
```bash
python -m json.tool custom_prompts.json
```

### **File permissions?**

Ensure write permissions:
```bash
chmod 644 custom_prompts.json
```

---

## 📊 Testing Checklist

- [ ] Create new prompt
- [ ] Edit existing prompt
- [ ] Delete custom prompt (not default)
- [ ] Export prompts
- [ ] Import prompts
- [ ] Use prompt with variables in generation
- [ ] Verify variable substitution works
- [ ] Test invalid JSON import (should show error)
- [ ] Test missing required fields (should show error)
- [ ] Try to delete default prompt (should prevent)

---

## 🎯 Next Steps

1. **Deploy the updated file**
2. **Test all features**
3. **Create your first custom prompt**
4. **Export and backup your prompts**
5. **Share with team members**

---

## 💼 Production Considerations

### **Backups**

```bash
# Automated backup script
#!/bin/bash
cp custom_prompts.json "backups/prompts_$(date +%Y%m%d_%H%M%S).json"
```

### **Multi-User Support**

For multi-user environments, consider:
- User-specific prompt storage
- Shared vs. private prompts
- Version control for prompts
- Approval workflow for changes

### **Security**

- Sanitize user input
- Limit file size uploads
- Rate limit API calls
- Add authentication

---

## 📞 Support

For issues or questions:
1. Check this guide
2. Review error messages in browser console
3. Check Flask application logs
4. Verify JSON file structure

---

**Ready to manage your AI prompts like a pro!** 🚀
