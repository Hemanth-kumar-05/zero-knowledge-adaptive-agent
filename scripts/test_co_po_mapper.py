"""
CO-PO Mapping Extension Script
This script processes uploaded JSON files containing student queries and maps them to Course Outcomes (CO) and Program Outcomes (PO).
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
        Dictionary containing mapping results and visualizations
    """
    try:
        # Parse JSON data from uploaded file
        data = json.loads(file_data.decode('utf-8'))
        
        # Extract query from the uploaded data
        query = data.get('query', '')
        
        if not query:
            return {
                'error': 'No query found in uploaded file',
                'result_type': 'error'
            }
        
        # CO-PO Mapping logic
        # This is a simplified version - you can enhance this with ML models
        co_po_mapping = analyze_query_for_co_po(query)
        
        # Generate mapping matrix
        matrix = generate_mapping_matrix(co_po_mapping)
        
        # Calculate statistics
        stats = calculate_statistics(co_po_mapping)
        
        return {
            'result_type': 'co_po_mapping',
            'query': query,
            'mapping': co_po_mapping,
            'matrix': matrix,
            'statistics': stats,
            'session_id': session_id,
            'metadata': {
                'total_cos_mapped': len(co_po_mapping.get('course_outcomes', [])),
                'total_pos_mapped': len(co_po_mapping.get('program_outcomes', [])),
                'confidence_score': co_po_mapping.get('confidence', 0.85)
            }
        }
        
    except json.JSONDecodeError:
        return {
            'error': 'Invalid JSON format in uploaded file',
            'result_type': 'error'
        }
    except Exception as e:
        return {
            'error': f'Processing error: {str(e)}',
            'result_type': 'error'
        }


def analyze_query_for_co_po(query: str) -> dict:
    """
    Analyze the query and map to relevant COs and POs.
    
    This is a simplified keyword-based approach.
    In production, you might use NLP/ML models for better accuracy.
    """
    query_lower = query.lower()
    
    # Define CO mappings based on keywords
    co_keywords = {
        'CO1': ['understand', 'basic', 'fundamental', 'concept', 'definition'],
        'CO2': ['apply', 'implement', 'use', 'practice', 'develop'],
        'CO3': ['analyze', 'evaluate', 'compare', 'examine', 'assess'],
        'CO4': ['design', 'create', 'build', 'construct', 'formulate'],
        'CO5': ['integrate', 'combine', 'synthesize', 'advanced', 'complex']
    }
    
    # Define PO mappings based on keywords
    po_keywords = {
        'PO1': ['engineering', 'mathematical', 'scientific', 'principles'],
        'PO2': ['problem', 'identify', 'formulate', 'solve', 'solution'],
        'PO3': ['design', 'system', 'component', 'requirement'],
        'PO4': ['research', 'investigate', 'experiment', 'data'],
        'PO5': ['tool', 'technique', 'modern', 'technology'],
        'PO6': ['society', 'sustainability', 'impact', 'environment'],
        'PO7': ['communication', 'technical', 'document', 'presentation'],
        'PO8': ['team', 'collaborate', 'multidisciplinary', 'leadership'],
        'PO9': ['ethics', 'professional', 'responsibility', 'integrity'],
        'PO10': ['learning', 'continuous', 'adapt', 'self-directed']
    }
    
    # Find matching COs
    matched_cos = []
    for co, keywords in co_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            matched_cos.append({
                'code': co,
                'relevance': calculate_relevance(query_lower, keywords),
                'description': get_co_description(co)
            })
    
    # Find matching POs
    matched_pos = []
    for po, keywords in po_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            matched_pos.append({
                'code': po,
                'relevance': calculate_relevance(query_lower, keywords),
                'description': get_po_description(po)
            })
    
    # Sort by relevance
    matched_cos.sort(key=lambda x: x['relevance'], reverse=True)
    matched_pos.sort(key=lambda x: x['relevance'], reverse=True)
    
    return {
        'course_outcomes': matched_cos[:3],  # Top 3 COs
        'program_outcomes': matched_pos[:3],  # Top 3 POs
        'confidence': min(1.0, (len(matched_cos) + len(matched_pos)) / 8)
    }


def calculate_relevance(query: str, keywords: list) -> float:
    """Calculate relevance score based on keyword matches."""
    matches = sum(1 for keyword in keywords if keyword in query)
    return matches / len(keywords) if keywords else 0.0


def get_co_description(co_code: str) -> str:
    """Get description for a Course Outcome."""
    descriptions = {
        'CO1': 'Understand fundamental concepts and principles',
        'CO2': 'Apply knowledge to practical problems',
        'CO3': 'Analyze and evaluate complex scenarios',
        'CO4': 'Design and develop solutions',
        'CO5': 'Integrate and synthesize advanced concepts'
    }
    return descriptions.get(co_code, 'Course Outcome')


def get_po_description(po_code: str) -> str:
    """Get description for a Program Outcome."""
    descriptions = {
        'PO1': 'Engineering knowledge',
        'PO2': 'Problem analysis',
        'PO3': 'Design/development of solutions',
        'PO4': 'Conduct investigations',
        'PO5': 'Modern tool usage',
        'PO6': 'Engineer and society',
        'PO7': 'Communication',
        'PO8': 'Teamwork and leadership',
        'PO9': 'Ethics and professional responsibility',
        'PO10': 'Life-long learning'
    }
    return descriptions.get(po_code, 'Program Outcome')


def generate_mapping_matrix(co_po_mapping: dict) -> list:
    """Generate a matrix representation of CO-PO mappings."""
    cos = co_po_mapping.get('course_outcomes', [])
    pos = co_po_mapping.get('program_outcomes', [])
    
    matrix = []
    for co in cos:
        row = {
            'co': co['code'],
            'mappings': {}
        }
        for po in pos:
            # Calculate mapping strength based on relevance scores
            strength = (co['relevance'] + po['relevance']) / 2
            row['mappings'][po['code']] = round(strength, 2)
        matrix.append(row)
    
    return matrix


def calculate_statistics(co_po_mapping: dict) -> dict:
    """Calculate statistics from the mapping."""
    cos = co_po_mapping.get('course_outcomes', [])
    pos = co_po_mapping.get('program_outcomes', [])
    
    avg_co_relevance = sum(co['relevance'] for co in cos) / len(cos) if cos else 0
    avg_po_relevance = sum(po['relevance'] for po in pos) / len(pos) if pos else 0
    
    return {
        'total_cos': len(cos),
        'total_pos': len(pos),
        'avg_co_relevance': round(avg_co_relevance, 2),
        'avg_po_relevance': round(avg_po_relevance, 2),
        'overall_confidence': round(co_po_mapping.get('confidence', 0), 2)
    }
