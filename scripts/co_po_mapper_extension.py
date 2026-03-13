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
                    'course_info': {'course_code': '...', 'course_name': '...', 'department': '...'},
                    'course_outcomes': [{'co_id': 'CO1', 'description': '...'}],
                    'programme_outcomes': [{'po_id': 'PO1', 'title': '...', 'description': '...', 'competencies': [...]}],
                    'programme_specific_outcomes': [{'pso_id': 'PSO1', 'description': '...', 'competencies': [...]}]
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
            'pso_count': len(data.get('programme_specific_outcomes', [])),
            'instruction': (
                'TASK: Perform CO-PO mapping analysis using AI.\n\n'
                'You are an engineering curriculum assessor. Analyze the provided course data and map each '
                'Course Outcome (CO) to relevant Programme Outcomes (POs) and Programme Specific Outcomes (PSOs).\n\n'
                'Use the attainment scale:\n'
                '0 - No correlation\n'
                '1 - Low correlation\n'
                '2 - Medium correlation\n'
                '3 - High correlation\n\n'
                'For each CO-PO/PSO pairing, provide:\n'
                '1. Correlation level (0-3)\n'
                '2. Justification (5-10 words)\n\n'
                'Present results as a structured mapping matrix with justifications.'
            ),
            'metadata': {
                'course_code': data['course_info'].get('course_code', 'N/A'),
                'course_name': data['course_info'].get('course_name', 'N/A'),
                'department': data['course_info'].get('department', 'N/A'),
                'semester': data['course_info'].get('semester', 'N/A'),
                'credits': data['course_info'].get('credits', 'N/A')
            }
        }
        
    except json.JSONDecodeError as e:
        return {
            'result_type': 'error',
            'error': f'Invalid JSON format: {str(e)}',
            'help': 'Please ensure the uploaded file is valid JSON'
        }
    except Exception as e:
        return {
            'result_type': 'error',
            'error': f'Processing error: {str(e)}'
        }


def build_mapping_prompt(data: dict) -> dict:
    """
    Build a structured prompt for AI-based CO-PO mapping.
    
    Args:
        data: Course data dictionary
        
    Returns:
        Dictionary with prompt and metadata
    """
    course_info = data.get('course_info', {})
    course_outcomes = data.get('course_outcomes', [])
    programme_outcomes = data.get('programme_outcomes', [])
    programme_specific_outcomes = data.get('programme_specific_outcomes', [])
    
    # Build the mapping prompt
    prompt = f"""You are an engineering curriculum assessor evaluating Course Outcome attainment levels against Programme Outcomes.

COURSE INFORMATION:
Course: {course_info.get('course_name', 'N/A')}
Code: {course_info.get('course_code', 'N/A')}
Department: {course_info.get('department', 'N/A')}
Semester: {course_info.get('semester', 'N/A')}
Credits: {course_info.get('credits', 'N/A')}

COURSE OUTCOMES:
"""
    
    for co in course_outcomes:
        prompt += f"\n{co.get('co_id', 'N/A')}: {co.get('description', 'N/A')}"
    
    prompt += "\n\nPROGRAMME OUTCOMES:\n"
    for po in programme_outcomes:
        prompt += f"\n{po.get('po_id', 'N/A')} - {po.get('title', 'N/A')}:"
        prompt += f"\n  Description: {po.get('description', 'N/A')}"
        
        competencies = po.get('competencies', [])
        if competencies:
            prompt += "\n  Competencies:"
            for comp in competencies:
                prompt += f"\n    • {comp.get('competency_id', 'N/A')}: {comp.get('description', 'N/A')}"
                indicators = comp.get('indicators', [])
                if indicators:
                    for ind in indicators:
                        prompt += f"\n      - {ind.get('indicator_id', 'N/A')}: {ind.get('description', 'N/A')}"
    
    if programme_specific_outcomes:
        prompt += "\n\nPROGRAMME SPECIFIC OUTCOMES:\n"
        for pso in programme_specific_outcomes:
            prompt += f"\n{pso.get('pso_id', 'N/A')} - {pso.get('description', 'N/A')}"
            
            competencies = pso.get('competencies', [])
            if competencies:
                prompt += "\n  Competencies:"
                for comp in competencies:
                    prompt += f"\n    • {comp.get('competency_id', 'N/A')}: {comp.get('description', 'N/A')}"
                    indicators = comp.get('indicators', [])
                    if indicators:
                        for ind in indicators:
                            prompt += f"\n      - {ind.get('indicator_id', 'N/A')}: {ind.get('description', 'N/A')}"
    
    prompt += """

TASK: Assess the attainment level between each CO and each PO/PSO.

ATTAINMENT SCALE:
0 - No correlation (CO does not address this outcome)
1 - Low correlation (CO slightly addresses this outcome)
2 - Medium correlation (CO moderately addresses this outcome)
3 - High correlation (CO strongly addresses this outcome)

INSTRUCTIONS:
1. For each Course Outcome, evaluate its correlation with EVERY Programme Outcome and Programme Specific Outcome
2. Assign a correlation level (0-3) based on how well the CO addresses the PO/PSO
3. Provide a brief justification (5-10 words) explaining the correlation level
4. Consider the competencies and indicators when making your assessment

FORMAT YOUR RESPONSE AS:
For each CO, create a mapping table showing:
- CO ID and Description
- For each PO/PSO:
  * Correlation Level (0-3)
  * Justification

After all mappings, provide:
- Summary statistics (average correlations, strong mappings, weak areas)
- Recommendations for curriculum improvement

Begin the mapping analysis now.
"""
    
    return {
        'prompt': prompt,
        'co_count': len(course_outcomes),
        'po_count': len(programme_outcomes),
        'pso_count': len(programme_specific_outcomes)
    }


def calculate_statistics(mappings: dict) -> dict:
    """
    Calculate statistics from mapping results.
    This function can be called after AI generates the mappings.
    
    Args:
        mappings: Dictionary of CO-PO mappings
        
    Returns:
        Dictionary with statistics
    """
    stats = {
        'total_mappings': 0,
        'high_correlations': 0,
        'medium_correlations': 0,
        'low_correlations': 0,
        'no_correlations': 0
    }
    
    for co_id, outcomes in mappings.items():
        for outcome_id, data in outcomes.items():
            level = data.get('level', 0)
            stats['total_mappings'] += 1
            
            if level == 3:
                stats['high_correlations'] += 1
            elif level == 2:
                stats['medium_correlations'] += 1
            elif level == 1:
                stats['low_correlations'] += 1
            else:
                stats['no_correlations'] += 1
    
    if stats['total_mappings'] > 0:
        stats['coverage_percentage'] = round(
            ((stats['total_mappings'] - stats['no_correlations']) / stats['total_mappings']) * 100,
            2
        )
    else:
        stats['coverage_percentage'] = 0
    
    return stats
