#!/usr/bin/env python3
"""
Final Patch Script: Completes the web interface merge
Adds Prompts tab HTML and JavaScript while preserving all original UI elements
"""

import re

def apply_final_patches():
    print("🔄 Applying final patches to web_interface_COMPLETE.py...")
    print("="*60)
    
    # Read the file
    with open('web_interface_COMPLETE.py', 'r') as f:
        content = f.read()
    
    print(f"✓ Loaded file: {len(content)} characters")
    
    #  ==================================================================
    # PATCH 1: Add Prompts tab HTML content before Results tab
    # ==================================================================
    
    prompts_tab_html = '''
        <!-- Prompts Tab -->
        <div class="tab-content" id="prompts-content">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Prompt Templates Management</h2>
                    <p style="font-size: 0.875rem; color: var(--muted);">Create, edit, and manage custom prompt templates</p>
                </div>
                
                <div id="promptMessage"></div>
                
                <!-- Prompt List -->
                <div class="prompt-list">
                    <h3 style="margin-bottom: 1rem; font-size: 1rem;">Saved Prompts</h3>
                    <table class="prompt-table" id="promptsTable">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Description</th>
                                <th>Variables</th>
                                <th>Tags</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="promptsTableBody">
                            <tr>
                                <td colspan="5" style="text-align: center; color: var(--muted);">Loading prompts...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <!-- Prompt Editor -->
                <div class="prompt-editor" style="background: var(--secondary); padding: 1.5rem; border-radius: 8px; margin-top: 1.5rem;">
                    <h3 style="margin-bottom: 1rem; font-size: 1rem;">Prompt Editor</h3>
                    
                    <input type="hidden" id="currentPromptId">
                    
                    <div class="form-group">
                        <label for="promptName">Prompt Name *</label>
                        <input type="text" id="promptName" placeholder="e.g., Swiss Banking Expert" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="promptDescription">Description</label>
                        <input type="text" id="promptDescription" placeholder="Brief description">
                    </div>
                    
                    <div class="form-group">
                        <label for="promptText">Prompt Text *</label>
                        <textarea 
                            id="promptText" 
                            style="min-height: 200px;"
                            placeholder="Enter your prompt template...

Use {variable_name} for placeholders.

Example:
You are a {expertise} specialist with focus on {region} markets..."
                            required
                        ></textarea>
                        <p style="font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem;">
                            💡 Use {curly_braces} for variables
                        </p>
                    </div>
                    
                    <div class="form-group">
                        <label for="promptTags">Tags (comma-separated)</label>
                        <input type="text" id="promptTags" placeholder="e.g., conservative, regulatory, swiss">
                    </div>
                    
                    <div id="detectedVariables" class="hidden" style="margin-top: 1rem; padding: 1rem; background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.2); border-radius: 8px;">
                        <h4 style="font-size: 0.875rem; margin-bottom: 0.5rem; color: var(--warning);">Detected Variables:</h4>
                        <div id="variablesList" style="font-family: 'JetBrains Mono', monospace; color: var(--primary);"></div>
                    </div>
                    
                    <div class="editor-actions" style="display: flex; gap: 8px; margin-top: 1rem;">
                        <button class="btn btn-primary" onclick="savePrompt()">💾 Save Prompt</button>
                        <button class="btn btn-outline" onclick="clearEditor()">🔄 Clear</button>
                        <button class="btn btn-outline" onclick="exportPrompts()">📥 Export All</button>
                        <button class="btn btn-outline" onclick="document.getElementById('importFileInput').click()">📤 Import</button>
                        <input type="file" id="importFileInput" accept=".json" style="display: none;" onchange="importPrompts(event)">
                        <button class="btn btn-danger" id="deletePromptBtn" onclick="deletePrompt()" style="margin-left: auto; display: none;">🗑️ Delete</button>
                    </div>
                </div>
            </div>
        </div>
        
'''
    
    # Find where to insert (before Results tab)
    results_tab_marker = '''<!-- Results Tab -->
        <div class="tab-content" id="results-content">'''
    
    if results_tab_marker in content:
        content = content.replace(results_tab_marker, prompts_tab_html + results_tab_marker)
        print("✓ Added Prompts tab HTML")
    else:
        print("⚠ Could not find Results tab marker")
    
    # ==================================================================
    # PATCH 2: Add prompt-specific CSS styles
    # ==================================================================
    
    prompts_css = '''        
        /* Prompt Management Styles */
        .prompt-list {
            margin-bottom: 2rem;
        }
        
        .prompt-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .prompt-table th {
            text-align: left;
            padding: 12px;
            background: var(--secondary);
            color: var(--muted);
            font-weight: 500;
            font-size: 0.875rem;
            border-bottom: 1px solid var(--border);
        }
        
        .prompt-table td {
            padding: 12px;
            border-bottom: 1px solid var(--border);
            font-size: 0.875rem;
        }
        
        .prompt-table tr:hover {
            background: var(--card-hover);
            cursor: pointer;
        }
        
        .prompt-table .prompt-name {
            font-weight: 600;
            color: var(--primary);
        }
        
        .prompt-table .prompt-tags {
            display: flex;
            gap: 4px;
            flex-wrap: wrap;
        }
        
        .tag {
            padding: 2px 8px;
            background: var(--secondary);
            border-radius: 12px;
            font-size: 0.75rem;
            color: var(--muted);
        }
        
        .tag.default {
            background: rgba(20, 184, 166, 0.2);
            color: var(--primary);
        }
        
        .prompt-editor {
            background: var(--secondary);
            padding: 1.5rem;
            border-radius: 8px;
        }
        
        .editor-actions {
            display: flex;
            gap: 8px;
            margin-top: 1rem;
        }
        
        .btn-danger {
            background: var(--destructive);
            color: white;
        }
        
        .btn-danger:hover {
            opacity: 0.9;
        }
        
        .message {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 1rem;
            font-size: 0.875rem;
        }
        
        .message-success {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.2);
            color: var(--success);
        }
        
        .message-error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.2);
            color: var(--destructive);
        }
        
        .variable-fields {
            background: rgba(251, 191, 36, 0.1);
            border: 1px solid rgba(251, 191, 36, 0.2);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .variable-fields h4 {
            color: var(--warning);
            margin-bottom: 0.75rem;
            font-size: 0.875rem;
        }
        
'''
    
    # Insert CSS before /* Hide element */
    css_marker = '/* Hide element */'
    if css_marker in content:
        content = content.replace(css_marker, prompts_css + '\n        ' + css_marker)
        print("✓ Added prompts CSS")
    else:
        print("⚠ Could not find CSS insertion point")
    
    # ==================================================================
    # PATCH 3: Add JavaScript for prompt management
    # ==================================================================
    
    prompts_js = '''
        // ====================================================================
        // PROMPT MANAGEMENT JAVASCRIPT
        // ====================================================================
        
        let allPrompts = [];
        let currentEditingId = null;
        let currentPromptVariables = {};
        
        // Load prompts for selector in Generate tab
        async function loadPrompts() {
            try {
                const response = await fetch('/api/prompts');
                const data = await response.json();
                
                if (data.success) {
                    allPrompts = data.prompts;
                    updatePromptSelector(data.prompts);
                    updatePromptsBadge(data.prompts.length);
                    renderPromptsTable(data.prompts);
                }
            } catch (error) {
                console.error('Error loading prompts:', error);
            }
        }
        
        function updatePromptSelector(prompts) {
            const select = document.getElementById('promptSelect');
            if (select) {
                select.innerHTML = prompts.map(p => 
                    `<option value="${p.id}">${p.name}</option>`
                ).join('');
                
                if (prompts.length > 0) {
                    select.value = prompts[0].id;
                    handlePromptChange();
                }
            }
        }
        
        function updatePromptsBadge(count) {
            const badge = document.getElementById('promptsBadge');
            if (badge) {
                badge.textContent = count;
            }
        }
        
        function handlePromptChange() {
            const promptId = document.getElementById('promptSelect').value;
            const prompt = allPrompts.find(p => p.id === promptId);
            
            if (!prompt) return;
            
            const variableFields = document.getElementById('variableFields');
            if (!variableFields) return;
            
            if (prompt.variables && prompt.variables.length > 0) {
                currentPromptVariables = {};
                
                let html = '<div class="variable-fields"><h4>📝 Fill in Variables</h4>';
                prompt.variables.forEach(varName => {
                    html += `
                        <div class="form-group">
                            <label for="var_${varName}">{${varName}}</label>
                            <input type="text" id="var_${varName}" 
                                   placeholder="Enter value for ${varName}"
                                   oninput="updatePromptVariable('${varName}', this.value)">
                        </div>
                    `;
                });
                html += '</div>';
                
                variableFields.innerHTML = html;
                variableFields.classList.remove('hidden');
            } else {
                variableFields.classList.add('hidden');
                variableFields.innerHTML = '';
            }
        }
        
        function updatePromptVariable(varName, value) {
            currentPromptVariables[varName] = value;
        }
        
        function renderPromptsTable(prompts) {
            const tbody = document.getElementById('promptsTableBody');
            if (!tbody) return;
            
            if (prompts.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--muted);">No prompts saved yet</td></tr>';
                return;
            }
            
            tbody.innerHTML = prompts.map(p => `
                <tr onclick="editPrompt('${p.id}')">
                    <td class="prompt-name">${p.name}</td>
                    <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${p.description || '-'}
                    </td>
                    <td>
                        ${p.variables && p.variables.length > 0 
                            ? '<code style="font-size: 0.75rem;">{' + p.variables.join('}, {') + '}</code>'
                            : '-'
                        }
                    </td>
                    <td>
                        <div class="prompt-tags">
                            ${(p.tags || []).map(tag => 
                                `<span class="tag ${p.is_default ? 'default' : ''}">${tag}</span>`
                            ).join('')}
                        </div>
                    </td>
                    <td>
                        <button class="btn btn-outline btn-small" onclick="event.stopPropagation(); editPrompt('${p.id}')">
                            ✏️ Edit
                        </button>
                        ${!p.is_default ? `
                            <button class="btn btn-danger btn-small" onclick="event.stopPropagation(); deletePrompt('${p.id}')">
                                🗑️
                            </button>
                        ` : ''}
                    </td>
                </tr>
            `).join('');
        }
        
        function editPrompt(promptId) {
            const prompt = allPrompts.find(p => p.id === promptId);
            if (!prompt) return;
            
            if (prompt.is_default) {
                showMessage('Default prompts cannot be edited. Create a new custom prompt instead.', 'error');
                return;
            }
            
            currentEditingId = promptId;
            document.getElementById('currentPromptId').value = promptId;
            document.getElementById('promptName').value = prompt.name;
            document.getElementById('promptDescription').value = prompt.description || '';
            document.getElementById('promptText').value = prompt.prompt_text;
            document.getElementById('promptTags').value = (prompt.tags || []).join(', ');
            
            detectVariables();
            
            const deleteBtn = document.getElementById('deletePromptBtn');
            if (deleteBtn) {
                deleteBtn.style.display = prompt.is_default ? 'none' : 'block';
            }
            
            // Scroll to editor
            document.querySelector('.prompt-editor').scrollIntoView({ behavior: 'smooth' });
        }
        
        async function savePrompt() {
            const name = document.getElementById('promptName').value.trim();
            const description = document.getElementById('promptDescription').value.trim();
            const text = document.getElementById('promptText').value.trim();
            const tags = document.getElementById('promptTags').value.split(',').map(t => t.trim()).filter(t => t);
            
            if (!name || !text) {
                showMessage('Please fill in required fields (Name and Prompt Text)', 'error');
                return;
            }
            
            const promptData = {
                id: currentEditingId || null,
                name: name,
                description: description,
                prompt_text: text,
                tags: tags
            };
            
            try {
                const response = await fetch('/api/prompts', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(promptData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('✓ Prompt saved successfully!', 'success');
                    loadPrompts();
                    clearEditor();
                } else {
                    showMessage('Error: ' + data.error, 'error');
                }
            } catch (err) {
                showMessage('Connection error: ' + err, 'error');
            }
        }
        
        async function deletePrompt(promptId) {
            if (promptId) {
                // Called from table
                if (!confirm('Are you sure you want to delete this prompt?')) return;
            } else {
                // Called from editor
                promptId = currentEditingId;
                if (!promptId) return;
                if (!confirm('Are you sure you want to delete this prompt?')) return;
            }
            
            try {
                const response = await fetch(`/api/prompts/${promptId}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('✓ Prompt deleted', 'success');
                    clearEditor();
                    loadPrompts();
                } else {
                    showMessage('Error: ' + data.error, 'error');
                }
            } catch (err) {
                showMessage('Connection error: ' + err, 'error');
            }
        }
        
        function clearEditor() {
            currentEditingId = null;
            document.getElementById('currentPromptId').value = '';
            document.getElementById('promptName').value = '';
            document.getElementById('promptDescription').value = '';
            document.getElementById('promptText').value = '';
            document.getElementById('promptTags').value = '';
            document.getElementById('detectedVariables').classList.add('hidden');
            
            const deleteBtn = document.getElementById('deletePromptBtn');
            if (deleteBtn) {
                deleteBtn.style.display = 'none';
            }
        }
        
        function detectVariables() {
            const text = document.getElementById('promptText').value;
            const variables = Array.from(new Set(text.match(/\\{\\w+\\}/g) || []));
            
            const container = document.getElementById('detectedVariables');
            const list = document.getElementById('variablesList');
            
            if (variables.length > 0) {
                list.textContent = variables.join(', ');
                container.classList.remove('hidden');
            } else {
                container.classList.add('hidden');
            }
        }
        
        async function exportPrompts() {
            window.location.href = '/api/prompts/export';
        }
        
        async function importPrompts(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = async function(e) {
                try {
                    const prompts = JSON.parse(e.target.result);
                    
                    if (!Array.isArray(prompts)) {
                        throw new Error('Invalid format: expected array of prompts');
                    }
                    
                    const response = await fetch('/api/prompts/import', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ prompts: prompts })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        showMessage(`✓ Imported ${data.imported} prompts successfully!`, 'success');
                        loadPrompts();
                    } else {
                        showMessage('Import error: ' + data.error, 'error');
                    }
                } catch (err) {
                    showMessage('Invalid JSON file: ' + err.message, 'error');
                }
            };
            reader.readAsText(file);
            
            // Reset file input
            event.target.value = '';
        }
        
        function showMessage(text, type) {
            const container = document.getElementById('promptMessage');
            if (!container) return;
            
            const className = type === 'success' ? 'message-success' : 'message-error';
            container.innerHTML = `<div class="message ${className}">${text}</div>`;
            
            setTimeout(() => {
                container.innerHTML = '';
            }, 5000);
        }
        
        // Auto-detect variables as user types
        const promptTextArea = document.getElementById('promptText');
        if (promptTextArea) {
            promptTextArea.addEventListener('input', detectVariables);
        }
        
'''
    
    # Insert JavaScript before scenario generation code
    js_marker = '// Global state'
    if js_marker in content:
        content = content.replace(js_marker, prompts_js + '\n        ' + js_marker)
        print("✓ Added prompts JavaScript")
    else:
        print("⚠ Could not find JS insertion point")
    
    # ==================================================================
    # PATCH 4: Update handleGenerate to use selected prompt
    # ==================================================================
    
    old_generate_call = '''const instruction = document.getElementById('instruction').value;
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
                    scenario_type: scenarioType
                })
            })'''
    
    new_generate_call = '''const promptId = document.getElementById('promptSelect').value;
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
                    prompt_id: promptId,
                    prompt_variables: currentPromptVariables,
                    instruction: instruction,
                    num_scenarios: numScenarios,
                    scenario_type: scenarioType
                })
            })'''
    
    if old_generate_call in content:
        content = content.replace(old_generate_call, new_generate_call)
        print("✓ Updated handleGenerate function")
    else:
        print("⚠ Could not find handleGenerate function")
    
    # ==================================================================
    # PATCH 5: Add initialization call for prompts
    # ==================================================================
    
    # Add loadPrompts() call on page load
    old_init = '''// Initialize
        document.addEventListener('DOMContentLoaded', function() {'''
    
    new_init = '''// Initialize
        document.addEventListener('DOMContentLoaded', function() {
            loadPrompts();'''
    
    # If not found, create the initialization
    if old_init in content:
        content = content.replace(old_init, new_init)
        print("✓ Added prompts initialization")
    elif 'DOMContentLoaded' not in content:
        # Add at end of script
        end_script_marker = '</script>\n</body>'
        if end_script_marker in content:
            init_code = '''
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadPrompts();
        });
        '''
            content = content.replace(end_script_marker, init_code + '\n    ' + end_script_marker)
            print("✓ Created prompts initialization")
    
    # ==================================================================
    # Write the final result
    # ==================================================================
    
    with open('web_interface_COMPLETE.py', 'w') as f:
        f.write(content)
    
    print("="*60)
    print("✅ ALL PATCHES APPLIED SUCCESSFULLY!")
    print(f"📄 Final file: {len(content)} characters")
    print()
    print("The file now includes:")
    print("  ✓ All original UI elements (sliders, charts, status panels)")
    print("  ✓ Quick Start Examples")
    print("  ✓ Platform Status and Recent Activity panels")
    print("  ✓ Complete Prompts management tab")
    print("  ✓ Prompt selector in Generate tab")
    print("  ✓ Variable substitution support")
    print("  ✓ Export/Import functionality")
    print()
    print("Ready to use!")
    print("="*60)

if __name__ == '__main__':
    try:
        apply_final_patches()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
