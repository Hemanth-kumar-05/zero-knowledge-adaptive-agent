# CO-PO Mapper Extension - Complete Setup Guide

## Overview
The CO-PO Mapper is a **script-based extension** that helps faculty members automatically map student queries, course content, or learning activities to:
- **Course Outcomes (CO)**: Specific learning objectives for a course
- **Program Outcomes (PO)**: Broader competencies aligned with degree program goals

This tool analyzes uploaded JSON files and provides detailed mapping analysis with relevance scores and statistics.

---

## Extension Details

### Basic Information
| Field | Value |
|-------|-------|
| **Extension Name** | CO-PO Mapper |
| **Extension Type** | Script-Based |
| **Category** | Academic |
| **Target Users** | Faculty, Course Coordinators |
| **Icon** | `fa-solid fa-diagram-project` (or `fa-solid fa-chart-network`) |

### Extension Configuration

#### 1. Name
```
CO-PO Mapper
```

#### 2. Description
```
AI-powered CO-PO mapping tool that analyzes course outcomes and maps them to Programme Outcomes (PO) and Programme Specific Outcomes (PSO). Upload a structured JSON file with course data to get comprehensive correlation analysis with justifications and attainment levels (0-3 scale).
```

#### 3. Category
```
Academic
```

#### 4. Welcome Message
```
Welcome to the AI-Powered CO-PO Mapper! 🎓

Upload a structured JSON file containing:
- Course information
- Course Outcomes (COs)
- Programme Outcomes (POs) with competencies
- Programme Specific Outcomes (PSOs)

I'll perform comprehensive AI-based mapping analysis with correlation levels (0-3) and detailed justifications for each CO-PO/PSO pairing.
```

#### 5. Input Placeholder
```
Upload course data JSON file for AI-powered CO-PO mapping analysis...
```

#### 6. Required Files (Optional)
```
.json
```

---

## Script Configuration

### Extension Type
Select: **Script-Based**

### Script Input Method
Choose **ONE** of the following:

#### Option A: Upload File
1. Select "Upload File"
2. Upload: `scripts/co_po_mapper_extension.py`

#### Option B: Paste Code
1. Select "Paste Code"
2. Copy and paste the complete script (see below)

### Handler Function Name
```
process
```

### Dependencies
```
(leave empty - only uses standard library)
```

---

## Complete Python Script

**File:** `scripts/co_po_mapper_extension.py`

This script prepares course data and delegates AI-based mapping to the assistant:

```python
"""
CO-PO Mapper Extension Script
Extension-compatible version that delegates AI processing to the assistant
"""

import json


def process(file_data: bytes, session_id: str, user_id: str) -> dict:
    """
    Handler function for CO-PO mapping extension.
    
    Args:
        file_data: Uploaded file content as bytes
        session_id: Current session ID
        user_id: ID of the user making the request
        
    Returns:
        Dictionary containing structured data for AI mapping
    """
    try:
        # Parse JSON data from uploaded file
        data = json.loads(file_data.decode('utf-8'))
        
        # Validate required fields
        required_fields = ['course_info', 'course_outcomes', 'programme_outcomes']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return {
                'result_type': 'error',
                'error': f'Missing required fields: {", ".join(missing_fields)}',
                'expected_format': {
                    'course_info': {'course_code': '...', 'course_name': '...'},
                    'course_outcomes': [{'co_id': 'CO1', 'description': '...'}],
                    'programme_outcomes': [{'po_id': 'PO1', 'title': '...', 'competencies': [...]}]
                }
            }
        
        # Build structured prompt for AI processing
        prompt_data = build_mapping_prompt(data)
        
        return {
            'result_type': 'co_po_mapping_request',
            'session_id': session_id,
            'course_data': data,
            'mapping_prompt': prompt_data['prompt'],
            'co_count': len(data.get('course_outcomes', [])),
            'po_count': len(data.get('programme_outcomes', [])),
            'instruction': 'Perform AI-based CO-PO mapping analysis with correlation levels (0-3) and justifications.',
            'metadata': {
                'course_code': data['course_info'].get('course_code', 'N/A'),
                'course_name': data['course_info'].get('course_name', 'N/A'),
                'department': data['course_info'].get('department', 'N/A')
            }
        }
        
    except json.JSONDecodeError as e:
        return {'result_type': 'error', 'error': f'Invalid JSON: {str(e)}'}
    except Exception as e:
        return {'result_type': 'error', 'error': f'Processing error: {str(e)}'}


def build_mapping_prompt(data: dict) -> dict:
    """Build structured prompt for AI-based CO-PO mapping."""
    course_info = data.get('course_info', {})
    course_outcomes = data.get('course_outcomes', [])
    programme_outcomes = data.get('programme_outcomes', [])
    
    prompt = f"""You are an engineering curriculum assessor evaluating Course Outcome attainment levels against Programme Outcomes.

COURSE INFORMATION:
Course: {course_info.get('course_name', 'N/A')}
Code: {course_info.get('course_code', 'N/A')}
Department: {course_info.get('department', 'N/A')}

COURSE OUTCOMES:
"""
    
    for co in course_outcomes:
        prompt += f"\n{co.get('co_id')}: {co.get('description')}"
    
    prompt += "\n\nPROGRAMME OUTCOMES:\n"
    for po in programme_outcomes:
        prompt += f"\n{po.get('po_id')} - {po.get('title')}:"
        prompt += f"\n  Description: {po.get('description')}"
        for comp in po.get('competencies', []):
            prompt += f"\n• {comp.get('competency_id')}: {comp.get('description')}"
    
    prompt += """

TASK: Assess attainment level between each CO and each PO.

ATTAINMENT SCALE:
0 - No correlation
1 - Low correlation
2 - Medium correlation  
3 - High correlation

Provide correlation level (0-3) and justification (5-10 words) for each CO-PO pair.
Present results as a structured mapping matrix with justifications and summary statistics.
"""
    
    return {'prompt': prompt, 'co_count': len(course_outcomes), 'po_count': len(programme_outcomes)}
```

---

## Step-by-Step Creation Process

### Prerequisites
- Admin access to the system
- Backend and frontend running
- MongoDB connected

### Step 1: Access Admin Dashboard
1. Login with admin credentials
2. Navigate to Extensions section
3. Click "Create New Extension" button

### Step 2: Fill Basic Information
1. **Name**: `CO-PO Mapper`
2. **Description**: (copy from above)
3. **Category**: Select `Academic`
4. **Icon**: Choose network/diagram icon

### Step 3: Select Extension Type
- Select **"Script-Based"** radio button
- The form will show script-related fields

### Step 4: Configure Script
1. **Script Input Method**: Choose **"Upload File"** or **"Paste Code"**
   
   **If Upload File:**
   - Click "Choose File"
   - Select `scripts/co_po_mapper_extension.py`
   
   **If Paste Code:**
   - Click "Paste Code" radio
   - Copy entire script from above
   - Paste into code textarea

2. **Handler Function Name**: `process` (pre-filled)
3. **Dependencies**: Leave empty

### Step 5: Set UI Messages
1. **Welcome Message**: (copy from above)
2. **Input Placeholder**: (copy from above)
3. **Required Files**: `.json`

### Step 6: Create Extension
1. Click "Create Extension" button
2. Wait for validation and upload
3. Extension should appear in extensions list

---

## Test Data Format

Use the same structure as in `features/co_po_mapping/sample_data.json`:

### Complete Course Data Structure
```json
{
  "course_info": {
    "course_code": "CS0001",
    "course_name": "Engineering Practices Lab",
    "semester": 5,
    "credits": 4,
    "department": "Computer Science and Engineering"
  },
  
  "course_outcomes": [
    {
      "co_id": "CO1",
      "description": "Learn to assemble and disassemble the PC, monitor CPU performance and troubleshoot various problems related to it."
    },
    {
      "co_id": "CO2",
      "description": "Implement the electronic circuits using electronic components and Equipments."
    }
  ],
  
  "programme_outcomes": [
    {
      "po_id": "PO1",
      "title": "Engineering Knowledge",
      "description": "Apply the knowledge of mathematics, science, engineering fundamentals, and an engineering specialization for the solution of complex engineering problems",
      "competencies": [
        {
          "competency_id": "PO1.1",
          "description": "Apply fundamental concepts from mathematics, natural sciences or engineering sciences",
          "indicators": [
            {
              "indicator_id": "PO1.1.1",
              "description": "Apply mathematics, natural sciences or basic engineering science to concepts of another engineering discipline"
            }
          ]
        }
      ]
    },
    {
      "po_id": "PO2",
      "title": "Problem Analysis",
      "description": "Identify, formulate, research literature, and analyze complex engineering problems",
      "competencies": [
        {
          "competency_id": "PO2.1",
          "description": "Identify and formulate complex engineering problems",
          "indicators": [
            {
              "indicator_id": "PO2.1.1",
              "description": "Identify problem constraints"
            }
          ]
        }
      ]
    }
  ],
  
  "programme_specific_outcomes": [
    {
      "pso_id": "PSO1",
      "description": "Design, develop, and analyze software systems",
      "competencies": [
        {
          "competency_id": "PSO1.1",
          "description": "Apply software engineering principles",
          "indicators": [
            {
              "indicator_id": "PSO1.1.1",
              "description": "Design scalable software architecture"
            }
          ]
        }
      ]
    }
  ]
}
```

### Expected AI Response

The AI assistant will analyze the course data and generate:

1. **CO-PO Mapping Matrix**:
   - For each CO, list all PO/PSO mappings
   - Correlation level (0-3) for each pairing
   - Justification explaining the correlation

2. **Summary Statistics**:
   - Average correlation levels
   - Strong mappings (level 3)
   - Weak or missing mappings (level 0-1)
   - Course coverage analysis

3. **Recommendations**:
   - Suggestions for improving CO-PO alignment
   - Identification of gaps in outcome coverage

**Example Output Format**:

```
CO-PO Mapping Analysis for Engineering Practices Lab

=== CO1: Learn to assemble and disassemble the PC ===

PO1 (Engineering Knowledge): Level 2 - Medium Correlation
Justification: Applies basic computer hardware concepts

PO2 (Problem Analysis): Level 1 - Low Correlation
Justification: Limited problem analysis, mainly procedural

PO3 (Design/Development): Level 0 - No Correlation
Justification: Does not involve design activities

...

=== CO2: Implement electronic circuits ===

PO1 (Engineering Knowledge): Level 3 - High Correlation
Justification: Directly applies engineering science fundamentals

PO2 (Problem Analysis): Level 2 - Medium Correlation
Justification: Requires circuit analysis and troubleshooting

...

=== SUMMARY STATISTICS ===
- Total Mappings: 24
- High Correlations (3): 6
- Medium Correlations (2): 10
- Low Correlations (1): 5
- No Correlations (0): 3
- Coverage: 87.5%

=== RECOMMENDATIONS ===
- Strengthen design components to improve PO3 mapping
- Add problem-solving scenarios for better PO2 alignment
```

---

## How Faculty Members Will Use It

### Step 1: Start Session
1. Navigate to Extensions
2. Select "CO-PO Mapper"
3. Click "Start Chat"

### Step 2: Prepare Query File
Create a JSON file with the query:
```json
{
  "query": "Your course activity or learning objective description here"
}
```

### Step 3: Upload File
1. Click attachment icon (📎) in chat
2. Select JSON file
3. Upload

### Step 4: Review Results
The AI will respond with:
- List of mapped Course Outcomes with relevance scores
- List of mapped Program Outcomes with relevance scores
- CO-PO mapping matrix
- Statistical summary
- Confidence score

### Step 5: Export/Use Results
- Copy the mapping for OBE documentation
- Use confidence scores for assessment planning
- Reference PO codes for accreditation reports

---

## Expected Output Structure

```json
{
  "result_type": "co_po_mapping",
  "query": "Original query text",
  "mapping": {
    "course_outcomes": [
      {
        "code": "CO4",
        "relevance": 0.80,
        "description": "Design and develop solutions"
      },
      {
        "code": "CO2",
        "relevance": 0.60,
        "description": "Apply knowledge to practical problems"
      },
      {
        "code": "CO3",
        "relevance": 0.40,
        "description": "Analyze and evaluate complex scenarios"
      }
    ],
    "program_outcomes": [
      {
        "code": "PO3",
        "relevance": 0.75,
        "description": "Design/development of solutions"
      },
      {
        "code": "PO2",
        "relevance": 0.67,
        "description": "Problem analysis"
      },
      {
        "code": "PO5",
        "relevance": 0.50,
        "description": "Modern tool usage"
      }
    ],
    "confidence": 0.75
  },
  "matrix": [
    {
      "co": "CO4",
      "mappings": {
        "PO3": 0.78,
        "PO2": 0.74,
        "PO5": 0.65
      }
    }
  ],
  "statistics": {
    "total_cos": 3,
    "total_pos": 3,
    "avg_co_relevance": 0.60,
    "avg_po_relevance": 0.64,
    "overall_confidence": 0.75
  },
  "metadata": {
    "total_cos_mapped": 3,
    "total_pos_mapped": 3,
    "confidence_score": 0.75
  }
}
```

---

## Customization Options

### Enhanced Keyword Mappings
Faculty can customize the script to include domain-specific keywords:

```python
co_keywords = {
    'CO1': ['understand', 'basic', 'fundamental', 'recall', 'identify', 'list'],
    'CO2': ['apply', 'implement', 'execute', 'demonstrate', 'solve'],
    # Add more specific to your course
}
```

### Custom CO/PO Descriptions
Update descriptions to match your institution's framework:

```python
def get_co_description(co_code: str) -> str:
    descriptions = {
        'CO1': 'Your institution-specific CO1 description',
        'CO2': 'Your institution-specific CO2 description',
        # etc.
    }
    return descriptions.get(co_code, 'Course Outcome')
```

### Add More Outcomes
Extend to include PSOs (Program Specific Outcomes):

```python
pso_keywords = {
    'PSO1': ['software', 'application', 'programming'],
    'PSO2': ['hardware', 'embedded', 'IoT'],
    # etc.
}
```

---

## Benefits for Faculty

1. **Time Saving**: Automated CO-PO mapping instead of manual analysis
2. **Consistency**: Standardized mapping criteria across courses
3. **Data-Driven**: Objective relevance scores for assessment
4. **Accreditation Ready**: Quick generation of OBE documentation
5. **Continuous Improvement**: Track mapping patterns over time
6. **Transparency**: Clear reasoning with keyword-based analysis

---

## Common Use Cases

### Use Case 1: Course Design
Map course learning objectives to COs and POs during syllabus creation

### Use Case 2: Assessment Planning
Verify that exam questions align with desired outcomes

### Use Case 3: Assignment Creation
Ensure assignments target specific CO-PO combinations

### Use Case 4: Lab Activity Mapping
Map lab experiments to practical application outcomes

### Use Case 5: Project Evaluation
Analyze final year project objectives for comprehensive CO-PO coverage

### Use Case 6: Accreditation Reports
Generate CO-PO attainment data for NBA/NAAC submissions

---

## Troubleshooting

### Issue: "No query found in uploaded file"
**Solution**: Ensure JSON file has `"query"` key

### Issue: "Invalid JSON format"
**Solution**: Validate JSON syntax (use jsonlint.com)

### Issue: No mappings returned
**Solution**: Use descriptive text with action verbs (design, analyze, implement, etc.)

### Issue: Low confidence scores
**Solution**: Include more specific technical terms and outcome-related keywords

---

## Future Enhancements

1. **ML-Based Mapping**: Replace keyword matching with NLP models
2. **Batch Processing**: Upload multiple queries at once
3. **Visualization**: Generate CO-PO matrix heatmaps
4. **Bloom's Taxonomy**: Map to cognitive levels
5. **Historical Analysis**: Track mapping trends across semesters
6. **Export Formats**: Generate PDF/Excel reports
7. **Course-Specific Training**: Fine-tune for specific domains

---

## Security & Privacy

- Scripts run in sandboxed environment
- No access to file system or network
- 30-second execution timeout
- Input data not stored permanently
- Results visible only to session user

---

## Support & Updates

For issues or enhancement requests:
1. Check validation errors in browser console
2. Review backend logs for script execution errors
3. Test with sample data first
4. Contact admin for script updates

---

## Summary Checklist

- [ ] Backend and frontend running
- [ ] Admin access obtained
- [ ] Extension created with script-based type
- [ ] Script uploaded or pasted
- [ ] Welcome message and placeholder set
- [ ] Test JSON file prepared
- [ ] Extension tested with sample data
- [ ] Results verified
- [ ] Faculty members informed about usage
- [ ] Documentation shared

---

**Your CO-PO Mapper is now ready to help faculty streamline outcome-based education mapping!** 🎓📊
