"""
Extension Script Template
=======================

This template shows how to create a script-based extension handler.
Your script must contain a function with the following signature.

Required Function Signature:
---------------------------
def process(file_data: bytes, session_id: str, user_id: str) -> dict

OR (async version):
async def process(file_data: bytes, session_id: str, user_id: str) -> dict

Parameters:
-----------
- file_data: The uploaded file content as bytes
- session_id: Current chat session ID
- user_id: ID of the user who uploaded the file

Return Value:
------------
Must return a dictionary with these keys:
{
    "success": bool,              # Required: True if processing succeeded
    "result": any,                # Your processed data (dict, list, etc.)
    "ai_context": str,            # Summary text for AI to use in response
    "visualization": str,         # Optional: base64 encoded image
    "download_url": str,          # Optional: URL for downloadable output
    "metadata": dict              # Optional: Additional metadata
}

Allowed Imports:
---------------
- json, csv, datetime, math, statistics
- collections, itertools, functools, re
- typing, dataclasses, enum
- numpy, pandas (if needed for data processing)

Forbidden (Security):
--------------------
- os, subprocess, sys, socket
- open(), eval(), exec(), compile()
- File system operations

Example Usage:
=============
"""

import json
from datetime import datetime
from typing import Dict


def process(file_data: bytes, session_id: str, user_id: str) -> Dict:
    """
    Main handler function for the extension
    
    This example processes a JSON file and extracts statistics
    """
    try:
        # Step 1: Parse the uploaded file
        data = json.loads(file_data.decode('utf-8'))
        
        # Step 2: Process the data (your custom logic here)
        # Example: Count items and extract summary
        item_count = len(data) if isinstance(data, list) else 1
        
        summary = {
            "total_items": item_count,
            "processed_at": datetime.now().isoformat(),
            "session_id": session_id,
        }
        
        #Step 3: Generate AI context (what the AI should know)
        ai_context = f"Successfully processed {item_count} items from the uploaded file. "
        ai_context += "The data has been analyzed and is ready for discussion."
        
        # Step 4: Return structured result
        return {
            "success": True,
            "result": summary,
            "ai_context": ai_context,
            "metadata": {
                "file_size_bytes": len(file_data),
                "processing_timestamp": datetime.now().isoformat()
            }
        }
    
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid JSON file format",
            "ai_context": "The uploaded file is not valid JSON. Please upload a properly formatted JSON file."
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ai_context": f"An error occurred while processing the file: {str(e)}"
        }


# Advanced Example: CO-PO Mapping (if you want data analytics)
def process_co_po_mapping(file_data: bytes, session_id: str, user_id: str) -> Dict:
    """
    Example: Process CO-PO mapping data
    """
    try:
        # Parse course data
        course_data = json.loads(file_data.decode('utf-8'))
        
        cos = course_data.get('course_outcomes', [])
        pos = course_data.get('programme_outcomes', [])
        
        # Generate mapping matrix (simplified example)
        mappings = []
        for co in cos:
            for po in pos:
                # Your mapping logic here
                correlation = calculate_correlation(co, po)
                if correlation > 0:
                    mappings.append({
                        "co_id": co['co_id'],
                        "po_id": po['po_id'],
                        "strength": correlation
                    })
        
        # Generate summary for AI
        ai_context = f"CO-PO mapping completed: {len(cos)} Course Outcomes mapped to {len(pos)} Program Outcomes. "
        ai_context += f"Total mappings generated: {len(mappings)}. "
        
        return {
            "success": True,
            "result": {
                "mappings": mappings,
                "summary": {
                    "total_cos": len(cos),
                    "total_pos": len(pos),
                    "total_mappings": len(mappings),
                    "coverage_percentage": (len(mappings) / (len(cos) * len(pos))) * 100 if cos and pos else 0
                }
            },
            "ai_context": ai_context
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ai_context": f"CO-PO mapping failed: {str(e)}"
        }


def calculate_correlation(co: Dict, po: Dict) -> int:
    """Helper function: Calculate CO-PO correlation (example)"""
    # Simplified correlation logic (customize as needed)
    # Return 1 (low), 2 (medium), or 3 (high)
    
    co_desc = co.get('description', '').lower()
    po_desc = po.get('description', '').lower()
    
    # Simple keyword matching
    common_keywords = set(co_desc.split()) & set(po_desc.split())
    
    if len(common_keywords) > 5:
        return 3  # High correlation
    elif len(common_keywords) > 2:
        return 2  # Medium correlation
    elif len(common_keywords) > 0:
        return 1  # Low correlation
    else:
        return 0  # No correlation


"""
Testing Your Script:
===================

Before uploading, test your script locally:

```python
# test_script.py
import json

# Simulate file upload
test_data = {"test": "data"}
file_bytes = json.dumps(test_data).encode('utf-8')

# Call your handler
result = process(file_bytes, "test_session_123", "test_user_456")

print("Result:", json.dumps(result, indent=2))
```

Deployment:
==========

1. Save your script as a .py file (e.g., my_extension.py)
2. Go to Admin Dashboard -> Extensions -> Create Extension
3. Select "Script-Based" extension type
4. Upload your .py file
5. Specify the handler function name (e.g., "process")
6. Test with sample data

Support:
========
For issues or questions, contact your system administrator.
"""
