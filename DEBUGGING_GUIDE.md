# 🐛 Debugging Guide - Generate Button Not Working

## ✅ **Fixes Applied**

The `web_interface_COMPLETE.py` file has been updated with the following fixes:

### **1. Syntax Warning Fixed**
- ❌ **Before:** `HTML = """`  (caused invalid escape sequence warnings)
- ✅ **After:** `HTML = r"""`  (raw string prevents escape issues)

### **2. Missing Import Fixed**
- ❌ **Before:** `from flask import Flask, render_template_string, request, jsonify`
- ✅ **After:** `from flask import Flask, render_template_string, request, jsonify, send_file`

### **3. Enhanced Error Handling**
- Added console.log statements throughout handleGenerate()
- Added HTTP status checking in fetch
- Added null checks for DOM elements
- Better error messages

---

## 🔍 **Debugging Steps**

### **Step 1: Check Browser Console**

1. Open the web interface: `http://localhost:8081`
2. Press **F12** to open Developer Tools
3. Go to **Console** tab
4. Click "Generate Scenarios"
5. Look for these messages:

```
✓ Good signs:
📋 Page loaded, initializing...
✓ Prompts loaded
🚀 Generate button clicked
Prompt ID: default (or other prompt name)
Instruction: Generate severe stress...
📤 Sending request to /generate...
📥 Response status: 200

❌ Problems:
⚠ promptSelect element not found
❌ No prompt selected
❌ Error: [message]
HTTP error! status: 500
```

### **Step 2: Check Network Tab**

1. In Developer Tools, go to **Network** tab
2. Click "Generate Scenarios"
3. Look for `/generate` request
4. Check:
   - **Status:** Should be 200
   - **Response:** Should have `success: true`
   - **If 500 error:** Check terminal for Python errors

### **Step 3: Check Terminal Output**

Look for these in your terminal:

```bash
✓ Good:
Web request:
  Prompt ID: default
  Variables: {}
  Instruction: Generate severe stress...
  Num scenarios: 3
  Type: stress
Generating scenarios...
Using prompt: Default ALM Expert

❌ Problems:
Error: Selected prompt not found
KeyError: ...
AttributeError: ...
```

---

## 🔧 **Common Issues & Solutions**

### **Issue 1: Nothing Happens When Clicking**

**Symptoms:**
- Button click does nothing
- No console messages
- No network requests

**Solution:**
```javascript
// In browser console, test:
document.getElementById('generateBtn')
// Should return: <button id="generateBtn">...</button>

document.getElementById('scenarioForm')
// Should return: <form id="scenarioForm">...</form>
```

If either returns `null`, the HTML structure is broken.

### **Issue 2: "No prompt selected"**

**Symptoms:**
- Error: "No prompt template selected"
- Console shows: `Prompt ID: ` (empty)

**Solution:**
```javascript
// In browser console:
document.getElementById('promptSelect').value
// Should return: "default" or another prompt ID

allPrompts
// Should return: Array of prompt objects
```

**Fix:** Refresh the page to reload prompts, or check if `/api/prompts` endpoint works:
```bash
curl http://localhost:8081/api/prompts
```

### **Issue 3: HTTP 500 Error**

**Symptoms:**
- Console shows: `HTTP error! status: 500`
- Network tab shows red 500 response

**Solution:**
Check terminal for Python error. Common causes:

1. **Missing `custom_system_prompt` parameter:**
   ```python
   # Your ALMScenarioGenerator.generate_scenarios() might not accept this yet
   # Solution: Comment out or add parameter support
   ```

2. **Database connection error:**
   ```python
   # Check if load_data() works
   risk_factors, counterparties, contracts = load_from_riskpro(limit_contracts=1000)
   ```

3. **LLM connection error:**
   ```python
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   ```

### **Issue 4: Button Gets Stuck "Generating..."**

**Symptoms:**
- Button text changes to "Generating Scenarios..."
- Never changes back
- No results appear

**Possible causes:**

1. **Request is actually working but takes a long time:**
   - Wait 1-2 minutes
   - Check terminal for progress

2. **Request failed silently:**
   - Check Network tab for failed request
   - Check browser console for errors

3. **Response parsing failed:**
   - Check if response has `success: true`
   - Check if response has `scenarios` array

---

## 🧪 **Test Commands**

### **Test 1: API Endpoints**

```bash
# Test prompts endpoint
curl http://localhost:8081/api/prompts

# Expected output:
{"success":true,"prompts":[{"id":"default","name":"Default ALM Expert"...}]}
```

### **Test 2: Generate Endpoint (Manual)**

```bash
curl -X POST http://localhost:8081/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_id": "default",
    "prompt_variables": {},
    "instruction": "Generate 1 stress scenario",
    "num_scenarios": 1,
    "scenario_type": "stress"
  }'

# Should return JSON with scenarios
```

### **Test 3: Python Syntax**

```bash
python3 -m py_compile web_interface_COMPLETE.py
# Should complete without errors
```

---

## 📋 **Checklist**

Before asking for help, verify:

- [ ] File runs without SyntaxWarning: `python3 web_interface_COMPLETE.py`
- [ ] Browser console shows "Page loaded, initializing..."
- [ ] Browser console shows "✓ Prompts loaded"
- [ ] Prompt selector dropdown is populated
- [ ] Clicking button shows "🚀 Generate button clicked"
- [ ] Network tab shows `/generate` request sent
- [ ] Terminal shows "Web request:" with details
- [ ] Ollama is running: `curl http://localhost:11434/api/tags`
- [ ] Database loads: No errors about RiskPro connection

---

## 🚨 **Emergency Workaround**

If still not working, try this minimal test:

1. **Create test endpoint:**

```python
@app.route('/test-generate', methods=['GET'])
def test_generate():
    return jsonify({'success': True, 'message': 'Backend is working!'})
```

2. **Test in browser:**
```
http://localhost:8081/test-generate
```

3. **If that works:** Problem is in the `/generate` route
4. **If that fails:** Problem is Flask configuration or network

---

## 📞 **Getting Help**

When reporting issues, provide:

1. **Terminal output** (full error message)
2. **Browser console output** (all messages)
3. **Network tab screenshot** (showing `/generate` request)
4. **Python version:** `python3 --version`
5. **Flask version:** `pip show flask`

---

## ✅ **Success Indicators**

You'll know it's working when you see:

**Terminal:**
```
Web request:
  Prompt ID: default
  Variables: {}
  Instruction: Generate severe stress...
Generating scenarios...
✓ Saved to scenarios_20260124_235959.csv
```

**Browser Console:**
```
🚀 Generate button clicked
Prompt ID: default
📤 Sending request to /generate...
📥 Response status: 200
```

**Browser UI:**
- Results section appears
- Stats grid shows numbers
- Charts render
- Scenario cards appear

---

Good luck! 🎯
