# Script-Based Extension Testing Guide

## Overview
The system now supports two types of extensions:
1. **Prompt-Based**: Uses custom system prompts for AI responses (existing functionality)
2. **Script-Based**: Uses custom Python scripts for file processing (new functionality)

## What's Been Implemented

### Backend
✅ Extended extension schema with `extensionType` and `scriptConfig`  
✅ ScriptValidator service with security checks (AST-based validation)  
✅ ExtensionExecutor service with 30-second timeout and dynamic loading  
✅ GridFS storage for Python scripts  
✅ API endpoint supporting both file upload AND inline code  
✅ Dual input method: Upload .py file OR paste code directly  
✅ Security validation preventing dangerous operations (os, subprocess, eval, etc.)  

### Frontend
✅ Extension type selector (Prompt-Based / Script-Based)  
✅ Conditional UI showing appropriate fields based on type  
✅ File upload input for .py files  
✅ Code textarea for inline code pasting  
✅ Handler function name input  
✅ Dependencies input (optional)  
✅ FormData submission for script-based extensions  
✅ CSS styling for all new components  

## Testing Instructions

### 1. Start the Application

#### Start Backend
```bash
cd backend
uvicorn app.main:app --reload
```

#### Start Frontend
```bash
cd frontend
npm run dev
```

### 2. Create a Script-Based Extension

1. **Login as Admin** (user with `is_admin: true`)

2. **Navigate to Extensions Dashboard** (typically under admin section)

3. **Click "Create Extension"**

4. **Fill in Basic Information**:
   - Name: `CO-PO Mapper`
   - Description: `Maps student queries to Course Outcomes and Program Outcomes`
   - Category: `Academic`
   - Icon: Select any academic icon

5. **Select Extension Type**: Choose **"Script-Based"**

6. **Choose Script Input Method**: You have two options:

   **Option A: Upload File**
   - Select "Upload File"
   - Click "Choose File"
   - Upload: `scripts/test_co_po_mapper.py`
   
   **Option B: Paste Code**
   - Select "Paste Code"
   - Copy the entire content from `scripts/test_co_po_mapper.py`
   - Paste into the code textarea

7. **Set Handler Function**:
   - Handler Function Name: `process` (default, already filled)

8. **Add Dependencies** (Optional):
   - Leave empty (script only uses standard library: json)

9. **Set UI Messages**:
   - Welcome Message: `Upload a JSON file with your query to get CO-PO mapping analysis`
   - Input Placeholder: `Upload a JSON file containing the query field...`

10. **Required Files** (Optional):
    - You can specify: `.json` to indicate JSON files are expected

11. **Click "Create Extension"**

### 3. Test the Extension

1. **Start a New Session** with the CO-PO Mapper extension

2. **You Should See**:
   - Custom welcome message: "Upload a JSON file with your query..."
   - Custom input placeholder in the chat box

3. **Upload Test File**:
   - Click the attachment icon (📎) in the chat input
   - Select `scripts/test_co_po_query.json`
   - The file contains a sample query about database design

4. **Expected Backend Flow** (currently being implemented):
   ```
   User uploads file
   ↓
   Backend detects script-based extension
   ↓
   ExtensionExecutor retrieves script from GridFS
   ↓
   Script is loaded and executed with 30s timeout
   ↓
   Results returned to AI with system prompt
   ↓
   AI interprets and presents results to user
   ```

5. **Expected Output Structure**:
   ```json
   {
     "result_type": "co_po_mapping",
     "query": "How do I design...",
     "mapping": {
       "course_outcomes": [
         {"code": "CO4", "relevance": 0.8, "description": "Design and develop solutions"},
         {"code": "CO2", "relevance": 0.6, "description": "Apply knowledge to practical problems"},
         {"code": "CO3", "relevance": 0.4, "description": "Analyze and evaluate complex scenarios"}
       ],
       "program_outcomes": [
         {"code": "PO3", "relevance": 0.75, "description": "Design/development of solutions"},
         {"code": "PO2", "relevance": 0.67, "description": "Problem analysis"},
         {"code": "PO5", "relevance": 0.5, "description": "Modern tool usage"}
       ]
     },
     "matrix": [...],
     "statistics": {
       "total_cos": 3,
       "total_pos": 3,
       "avg_co_relevance": 0.6,
       "avg_po_relevance": 0.64,
       "overall_confidence": 0.75
     }
   }
   ```

## Script Requirements

### Handler Function Signature
```python
def process(file_data: bytes, session_id: str, user_id: str) -> dict:
    """
    Required parameters:
    - file_data: Uploaded file content as bytes
    - session_id: Current chat session ID
    - user_id: ID of the user making the request
    
    Returns:
    - Dictionary containing results (will be passed to AI)
    """
    pass
```

### Security Restrictions
Your script **CANNOT** use:
- `os` module
- `subprocess` module
- `eval()` or `exec()`
- `open()` function
- `sys` module
- Network operations (`socket`, `urllib`, `requests`)
- File system operations

### Allowed Libraries
- `json`
- `csv`
- `datetime`
- `math`
- `statistics`
- `collections`
- `numpy` (if specified in dependencies)
- `pandas` (if specified in dependencies)
- `matplotlib` (if specified in dependencies)

### Return Format
Your script should return a dictionary with:
- `result_type`: Type of result (e.g., "co_po_mapping", "analysis", "report")
- `error`: Error message (if processing failed)
- Any other fields relevant to your processing

## Validation Process

When you create a script-based extension, the system:

1. **Checks file size** (max 1MB)
2. **Validates Python syntax** (AST parsing)
3. **Scans for forbidden imports/calls**
4. **Verifies handler function exists**
5. **Checks handler function signature**
6. **Stores script in GridFS** with metadata
7. **Returns validation errors** if any issues found

## Error Handling

If script execution fails:
- 30-second timeout protection
- Graceful fallback to prompt-based mode
- Error details logged (not exposed to user)
- User sees friendly error message

## Next Steps (Not Yet Implemented)

The following features are planned but not yet implemented:

### Query Flow Integration
- Detect file upload in script-based extension session
- Trigger script execution automatically
- Pass results to AI with enhanced system prompt
- Display script results in chat UI

### Script Result Display
- Visualizations for matrix data
- Download options for generated files
- Formatted tables for statistics
- Interactive charts (if matplotlib used)

## Testing Different Scenarios

### Test Case 1: Valid Script Upload
- Upload `test_co_po_mapper.py`
- Should: ✅ Validate successfully, store in GridFS

### Test Case 2: Invalid Script (Security Violation)
Create a test script with:
```python
import os

def process(file_data, session_id, user_id):
    os.system("echo hello")
    return {}
```
- Should: ❌ Reject with "Forbidden import: os"

### Test Case 3: Missing Handler Function
Create a script without `process()` function
- Should: ❌ Reject with "Handler function 'process' not found"

### Test Case 4: Wrong Handler Signature
```python
def process(file_data):  # Missing session_id and user_id
    return {}
```
- Should: ❌ Reject with "Handler function must accept 3 parameters"

### Test Case 5: Inline Code Paste
- Paste valid Python code directly
- Should: ✅ Validate and store same as file upload

## Troubleshooting

### Extension Creation Fails
- Check browser console for errors
- Verify Python script syntax
- Ensure handler function exists with correct signature
- Check file size (must be < 1MB)

### Script Not Executing
- Verify extension was created successfully
- Check that extensionType is "script-based"
- Look for script_config in extension document
- Check MongoDB GridFS for stored script

### Backend Errors
- Check FastAPI logs for validation errors
- Verify MongoDB connection
- Ensure GridFS is accessible
- Check script_validator.py logs

## Architecture Details

### Extension Document Structure (MongoDB)
```json
{
  "_id": "...",
  "name": "CO-PO Mapper",
  "extension_type": "script-based",
  "script_config": {
    "script_file_id": "ObjectId(...)",
    "script_filename": "test_co_po_mapper.py",
    "handler_function": "process",
    "version": "1.0",
    "dependencies": []
  },
  "welcome_message": "Upload a JSON file...",
  "input_placeholder": "Upload a JSON file...",
  "created_at": "...",
  "updated_at": "..."
}
```

### GridFS Document Structure
```json
{
  "filename": "test_co_po_mapper.py",
  "metadata": {
    "extension_id": "...",
    "uploaded_by": "user_id",
    "uploaded_at": "...",
    "handler_function": "process",
    "extension_type": "script-based"
  }
}
```

## Security Details

### AST Validation
The ScriptValidator uses Python's `ast` module to:
- Parse source code into Abstract Syntax Tree
- Walk all nodes looking for forbidden patterns
- Check import statements against blacklist
- Check function calls against blacklist
- Verify no dynamic code execution (eval, exec, compile)

### Execution Isolation
- Scripts run in same process (Python's import system)
- 30-second timeout via `asyncio.wait_for()`
- Temporary file cleanup in `finally` block
- No access to file system or network
- Results passed through AI before reaching user

### What CAN'T Be Done
❌ Read/write files  
❌ Execute shell commands  
❌ Make network requests  
❌ Access environment variables  
❌ Import system modules  
❌ Modify Python runtime  

### What CAN Be Done
✅ Process uploaded file data  
✅ Perform calculations  
✅ Use allowed libraries (JSON, math, etc.)  
✅ Return structured results  
✅ Access session and user IDs  

## Summary

You now have a complete script-based extension system that:
- Allows admins to upload custom processing logic
- Validates scripts for security
- Stores scripts in MongoDB GridFS
- Supports both file upload and inline code
- Has a clean UI with conditional fields
- Provides comprehensive error handling

The only remaining work is integrating script execution into the query flow when users upload files in chat sessions.
