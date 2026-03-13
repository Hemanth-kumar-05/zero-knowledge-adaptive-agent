import React, { useState } from 'react';
import FontAwesomeIconPicker from './FontAwesomeIconPicker';
import './ExtensionCreateModal.css';

const CATEGORIES = ['Academic', 'Planning', 'Research', 'Career', 'Learning'];

function ExtensionCreateModal({ isOpen, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'Academic',
    systemPrompt: '',
    welcomeMessage: '',
    inputPlaceholder: '',
    requiredFiles: '',
    icon: '',
    isActive: true,
    
    // Script-based extension fields
    extensionType: 'prompt-based',
    scriptInputMode: 'upload', // 'upload' or 'inline'
    scriptFile: null,
    scriptCode: '',
    handlerFunction: 'process',
    dependencies: ''
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.name.endsWith('.py')) {
        setErrors(prev => ({ ...prev, scriptFile: 'Only .py files are allowed' }));
        return;
      }
      setFormData(prev => ({ ...prev, scriptFile: file }));
      if (errors.scriptFile) {
        setErrors(prev => ({ ...prev, scriptFile: '' }));
      }
    }
  };

  const handleIconSelect = (iconClass) => {
    setFormData(prev => ({ ...prev, icon: iconClass }));
    // Clear error for icon
    if (errors.icon) {
      setErrors(prev => ({ ...prev, icon: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name || formData.name.trim().length < 3) {
      newErrors.name = 'Name must be at least 3 characters';
    }

    if (!formData.description || formData.description.trim().length < 10) {
      newErrors.description = 'Description must be at least 10 characters';
    }

    if (!formData.icon) {
      newErrors.icon = 'Icon is required';
    }

    if (formData.extensionType === 'prompt-based') {
      if (!formData.systemPrompt || formData.systemPrompt.trim().length < 20) {
        newErrors.systemPrompt = 'System prompt must be at least 20 characters';
      }

      if (!formData.welcomeMessage || formData.welcomeMessage.trim().length < 10) {
        newErrors.welcomeMessage = 'Welcome message must be at least 10 characters';
      }

      if (!formData.inputPlaceholder || formData.inputPlaceholder.trim().length < 10) {
        newErrors.inputPlaceholder = 'Input placeholder must be at least 10 characters';
      }
    } else if (formData.extensionType === 'script-based') {
      // Script-based validation
      if (formData.scriptInputMode === 'upload') {
        if (!formData.scriptFile) {
          newErrors.scriptFile = 'Script file is required';
        }
      } else {
        if (!formData.scriptCode || formData.scriptCode.trim().length < 20) {
          newErrors.scriptCode = 'Script code must be at least 20 characters';
        }
      }

      if (!formData.handlerFunction || formData.handlerFunction.trim().length < 1) {
        newErrors.handlerFunction = 'Handler function name is required';
      }

      if (!formData.welcomeMessage || formData.welcomeMessage.trim().length < 10) {
        newErrors.welcomeMessage = 'Welcome message must be at least 10 characters';
      }

      if (!formData.inputPlaceholder || formData.inputPlaceholder.trim().length < 10) {
        newErrors.inputPlaceholder = 'Input placeholder must be at least 10 characters';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Always use FormData (backend expects Form, not JSON)
      if (formData.extensionType === 'prompt-based') {
        // Parse required files (comma-separated)
        const requiredFilesArray = formData.requiredFiles
          .split(',')
          .map(f => f.trim())
          .filter(f => f.length > 0);

        const formDataToSend = new FormData();
        formDataToSend.append('name', formData.name.trim());
        formDataToSend.append('description', formData.description.trim());
        formDataToSend.append('category', formData.category);
        formDataToSend.append('systemPrompt', formData.systemPrompt.trim());
        formDataToSend.append('welcomeMessage', formData.welcomeMessage.trim());
        formDataToSend.append('inputPlaceholder', formData.inputPlaceholder.trim());
        formDataToSend.append('icon', formData.icon);
        formDataToSend.append('isActive', formData.isActive);
        formDataToSend.append('extensionType', 'prompt-based');
        
        if (requiredFilesArray.length > 0) {
          formDataToSend.append('requiredFiles', requiredFilesArray.join(','));
        }

        await onSubmit(formDataToSend);
      } else {
        // Script-based extension - use FormData
        const formDataToSend = new FormData();
        
        formDataToSend.append('name', formData.name.trim());
        formDataToSend.append('description', formData.description.trim());
        formDataToSend.append('category', formData.category);
        formDataToSend.append('welcomeMessage', formData.welcomeMessage.trim());
        formDataToSend.append('inputPlaceholder', formData.inputPlaceholder.trim());
        formDataToSend.append('icon', formData.icon);
        formDataToSend.append('isActive', formData.isActive);
        formDataToSend.append('extensionType', 'script-based');
        formDataToSend.append('handlerFunction', formData.handlerFunction.trim());
        
        if (formData.dependencies && formData.dependencies.trim()) {
          formDataToSend.append('dependencies', formData.dependencies.trim());
        }

        // Parse required files
        const requiredFilesArray = formData.requiredFiles
          .split(',')
          .map(f => f.trim())
          .filter(f => f.length > 0);
        if (requiredFilesArray.length > 0) {
          formDataToSend.append('requiredFiles', requiredFilesArray.join(','));
        }

        // Add script file or code
        if (formData.scriptInputMode === 'upload' && formData.scriptFile) {
          formDataToSend.append('scriptFile', formData.scriptFile);
        } else if (formData.scriptInputMode === 'inline' && formData.scriptCode) {
          formDataToSend.append('scriptCode', formData.scriptCode.trim());
        }

        await onSubmit(formDataToSend);
      }

      // Reset form
      setFormData({
        name: '',
        description: '',
        category: 'Academic',
        systemPrompt: '',
        welcomeMessage: '',
        inputPlaceholder: '',
        requiredFiles: '',
        icon: '',
        isActive: true,
        extensionType: 'prompt-based',
        scriptInputMode: 'upload',
        scriptFile: null,
        scriptCode: '',
        handlerFunction: 'process',
        dependencies: ''
      });
      setIconFile(null);
      setIconPreview('');
      onClose();
    } catch (error) {
      setErrors({ submit: error.message || 'Failed to create extension' });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="extension-modal-overlay" onClick={onClose}>
      <div className="extension-modal" onClick={(e) => e.stopPropagation()}>
        <div className="extension-modal-header">
          <h2>Create New Extension</h2>
          <button className="modal-close-btn" onClick={onClose}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="extension-form">
          {errors.submit && (
            <div className="form-error">{errors.submit}</div>
          )}

          <div className="form-group">
            <label htmlFor="name">Extension Name *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="e.g., Policy Advisor"
              maxLength={100}
              required
            />
            {errors.name && <span className="field-error">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="description">Description *</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Brief description of what this extension does..."
              rows={3}
              maxLength={500}
              required
            />
            {errors.description && <span className="field-error">{errors.description}</span>}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="category">Category *</label>
              <select
                id="category"
                name="category"
                value={formData.category}
                onChange={handleChange}
                required
              >
                {CATEGORIES.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Extension Icon *</label>
              <FontAwesomeIconPicker
                selectedIcon={formData.icon}
                onSelectIcon={handleIconSelect}
                category={formData.category}
              />
              {errors.icon && <span className="field-error">{errors.icon}</span>}
            </div>
          </div>

          <div className="form-group">
            <label>Extension Type *</label>
            <div className="extension-type-selector">
              <label className="radio-option">
                <input
                  type="radio"
                  name="extensionType"
                  value="prompt-based"
                  checked={formData.extensionType === 'prompt-based'}
                  onChange={handleChange}
                />
                <span>
                  <strong>Prompt-Based</strong>
                  <small>AI responds using custom system prompts</small>
                </span>
              </label>
              <label className="radio-option">
                <input
                  type="radio"
                  name="extensionType"
                  value="script-based"
                  checked={formData.extensionType === 'script-based'}
                  onChange={handleChange}
                />
                <span>
                  <strong>Script-Based</strong>
                  <small>Custom Python processing for uploaded files</small>
                </span>
              </label>
            </div>
          </div>

          {formData.extensionType === 'prompt-based' && (
            <div className="form-group">
              <label htmlFor="systemPrompt">System Prompt *</label>
              <textarea
                id="systemPrompt"
                name="systemPrompt"
                value={formData.systemPrompt}
                onChange={handleChange}
                placeholder="System prompt that defines the extension's behavior and personality..."
                rows={5}
                required
              />
              <div className="field-hint">
                This prompt will be used to customize the AI's responses for this extension
              </div>
              {errors.systemPrompt && <span className="field-error">{errors.systemPrompt}</span>}
            </div>
          )}

          {formData.extensionType === 'script-based' && (
            <>
              <div className="form-group">
                <label>Script Input Method *</label>
                <div className="script-input-method-selector">
                  <label className="radio-option">
                    <input
                      type="radio"
                      name="scriptInputMode"
                      value="upload"
                      checked={formData.scriptInputMode === 'upload'}
                      onChange={handleChange}
                    />
                    <span>Upload File</span>
                  </label>
                  <label className="radio-option">
                    <input
                      type="radio"
                      name="scriptInputMode"
                      value="inline"
                      checked={formData.scriptInputMode === 'inline'}
                      onChange={handleChange}
                    />
                    <span>Paste Code</span>
                  </label>
                </div>
              </div>

              {formData.scriptInputMode === 'upload' && (
                <div className="form-group">
                  <label htmlFor="scriptFile">Python Script File *</label>
                  <input
                    type="file"
                    id="scriptFile"
                    name="scriptFile"
                    accept=".py"
                    onChange={handleFileChange}
                    required={formData.extensionType === 'script-based' && formData.scriptInputMode === 'upload'}
                  />
                  <div className="field-hint">
                    Upload a Python (.py) file with your custom processing logic
                  </div>
                  {formData.scriptFile && (
                    <div className="file-info">Selected: {formData.scriptFile.name}</div>
                  )}
                  {errors.scriptFile && <span className="field-error">{errors.scriptFile}</span>}
                </div>
              )}

              {formData.scriptInputMode === 'inline' && (
                <div className="form-group">
                  <label htmlFor="scriptCode">Python Code *</label>
                  <textarea
                    id="scriptCode"
                    name="scriptCode"
                    value={formData.scriptCode}
                    onChange={handleChange}
                    placeholder="Paste your Python code here...&#10;&#10;def process(file_data: bytes, session_id: str, user_id: str) -> dict:&#10;    # Your processing logic&#10;    return {'result': 'value'}"
                    rows={15}
                    className="code-textarea"
                    required={formData.extensionType === 'script-based' && formData.scriptInputMode === 'inline'}
                  />
                  <div className="field-hint">
                    Paste Python code with a handler function (default: process)
                  </div>
                  {errors.scriptCode && <span className="field-error">{errors.scriptCode}</span>}
                </div>
              )}

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="handlerFunction">Handler Function Name *</label>
                  <input
                    type="text"
                    id="handlerFunction"
                    name="handlerFunction"
                    value={formData.handlerFunction}
                    onChange={handleChange}
                    placeholder="process"
                    required={formData.extensionType === 'script-based'}
                  />
                  <div className="field-hint">
                    The function name to call in your script
                  </div>
                  {errors.handlerFunction && <span className="field-error">{errors.handlerFunction}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="dependencies">Dependencies (Optional)</label>
                  <input
                    type="text"
                    id="dependencies"
                    name="dependencies"
                    value={formData.dependencies}
                    onChange={handleChange}
                    placeholder="numpy, pandas, matplotlib"
                  />
                  <div className="field-hint">
                    Comma-separated list of required packages
                  </div>
                </div>
              </div>
            </>
          )}

          <div className="form-group">
            <label htmlFor="welcomeMessage">Welcome Message *</label>
            <input
              type="text"
              id="welcomeMessage"
              name="welcomeMessage"
              value={formData.welcomeMessage}
              onChange={handleChange}
              placeholder="e.g., Let me help you plan your courses and navigate registration..."
              required
            />
            <div className="field-hint">
              The message shown to users when they start a new chat with this extension
            </div>
            {errors.welcomeMessage && <span className="field-error">{errors.welcomeMessage}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="inputPlaceholder">Input Placeholder *</label>
            <input
              type="text"
              id="inputPlaceholder"
              name="inputPlaceholder"
              value={formData.inputPlaceholder}
              onChange={handleChange}
              placeholder="e.g., Ask about course registration, add/drop deadlines, prerequisites..."
              required
            />
            <div className="field-hint">
              Placeholder text shown in the message input box for this extension
            </div>
            {errors.inputPlaceholder && <span className="field-error">{errors.inputPlaceholder}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="requiredFiles">Required Files (Optional)</label>
            <input
              type="text"
              id="requiredFiles"
              name="requiredFiles"
              value={formData.requiredFiles}
              onChange={handleChange}
              placeholder="e.g., policy_document, transcript, id_proof (comma-separated)"
            />
            <div className="field-hint">
              List of file types or documents users should provide (comma-separated)
            </div>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                name="isActive"
                checked={formData.isActive}
                onChange={handleChange}
              />
              <span>Make this extension active immediately</span>
            </label>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : 'Create Extension'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ExtensionCreateModal;
