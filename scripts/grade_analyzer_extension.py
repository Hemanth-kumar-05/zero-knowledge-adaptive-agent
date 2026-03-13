"""
Grade Analyzer Extension Script
Analyzes student performance data and generates comprehensive reports
"""

import json
import csv
from io import StringIO


def process(file_data: bytes, session_id: str, user_id: str) -> dict:
    """
    Handler function for Grade Analyzer extension.
    
    Args:
        file_data: Uploaded file content as bytes (CSV or JSON)
        session_id: Current session ID
        user_id: ID of the user making the request
        
    Returns:
        Dictionary containing analysis results and AI prompt for insights
    """
    try:
        # Detect file format and parse
        content = file_data.decode('utf-8')
        
        # Try JSON first
        try:
            data = json.loads(content)
            students = data.get('students', [])
            course_info = data.get('course_info', {})
        except json.JSONDecodeError:
            # Parse as CSV
            students, course_info = parse_csv(content)
        
        if not students:
            return {
                'result_type': 'error',
                'error': 'No student data found in file',
                'expected_format': {
                    'csv': 'roll_number,name,internal,external,total',
                    'json': {
                        'course_info': {'course_name': '...', 'max_marks': 100},
                        'students': [{'roll_number': '...', 'name': '...', 'marks': {...}}]
                    }
                }
            }
        
        # Perform statistical analysis
        analysis = analyze_grades(students, course_info)
        
        # Build prompt for AI insights
        prompt = build_analysis_prompt(students, analysis, course_info)
        
        return {
            'result_type': 'grade_analysis',
            'session_id': session_id,
            'course_info': course_info,
            'total_students': len(students),
            'analysis': analysis,
            'prompt': prompt
        }
        
    except Exception as e:
        return {
            'result_type': 'error',
            'error': f'Processing error: {str(e)}',
            'details': 'Ensure file is valid CSV or JSON format'
        }


def parse_csv(content: str) -> tuple:
    """Parse CSV content and extract student data"""
    reader = csv.DictReader(StringIO(content))
    students = []
    
    for row in reader:
        student = {
            'roll_number': row.get('roll_number', row.get('Roll Number', '')),
            'name': row.get('name', row.get('Name', '')),
            'marks': {}
        }
        
        # Extract marks columns
        for key, value in row.items():
            if key.lower() not in ['roll_number', 'roll number', 'name']:
                try:
                    student['marks'][key] = float(value) if value else 0
                except ValueError:
                    student['marks'][key] = 0
        
        students.append(student)
    
    # Infer course info from CSV headers
    course_info = {
        'course_name': 'Uploaded Course',
        'assessment_components': list(students[0]['marks'].keys()) if students else []
    }
    
    return students, course_info


def analyze_grades(students: list, course_info: dict) -> dict:
    """Perform comprehensive statistical analysis"""
    
    # Calculate totals for each student
    for student in students:
        student['total'] = sum(student['marks'].values())
    
    # Extract all totals
    totals = [s['total'] for s in students]
    
    if not totals:
        return {}
    
    # Statistical measures
    mean = sum(totals) / len(totals)
    sorted_totals = sorted(totals)
    median = sorted_totals[len(sorted_totals) // 2]
    
    # Standard deviation
    variance = sum((x - mean) ** 2 for x in totals) / len(totals)
    std_dev = variance ** 0.5
    
    # Pass/Fail analysis (assuming 40% is passing)
    passing_marks = course_info.get('passing_marks', 40)
    max_marks = course_info.get('max_marks', 100)
    
    passed = [s for s in students if s['total'] >= passing_marks]
    failed = [s for s in students if s['total'] < passing_marks]
    
    # Grade distribution (assuming standard grading)
    grade_distribution = {
        'A+ (90-100)': len([s for s in students if s['total'] >= 90]),
        'A (80-89)': len([s for s in students if 80 <= s['total'] < 90]),
        'B+ (70-79)': len([s for s in students if 70 <= s['total'] < 80]),
        'B (60-69)': len([s for s in students if 60 <= s['total'] < 70]),
        'C (50-59)': len([s for s in students if 50 <= s['total'] < 60]),
        'D (40-49)': len([s for s in students if 40 <= s['total'] < 50]),
        'F (<40)': len([s for s in students if s['total'] < 40])
    }
    
    # At-risk students (below 50%)
    at_risk = [
        {
            'roll_number': s['roll_number'],
            'name': s['name'],
            'total': s['total'],
            'marks': s['marks']
        }
        for s in students if s['total'] < 50
    ]
    
    # Top performers
    top_performers = sorted(students, key=lambda x: x['total'], reverse=True)[:5]
    
    # Component-wise analysis
    component_analysis = {}
    for component in course_info.get('assessment_components', []):
        component_scores = [s['marks'].get(component, 0) for s in students]
        if component_scores:
            component_analysis[component] = {
                'mean': sum(component_scores) / len(component_scores),
                'max': max(component_scores),
                'min': min(component_scores),
                'below_average': len([s for s in component_scores if s < sum(component_scores) / len(component_scores)])
            }
    
    return {
        'total_students': len(students),
        'mean_score': round(mean, 2),
        'median_score': round(median, 2),
        'std_deviation': round(std_dev, 2),
        'highest_score': max(totals),
        'lowest_score': min(totals),
        'pass_count': len(passed),
        'fail_count': len(failed),
        'pass_percentage': round((len(passed) / len(students)) * 100, 2),
        'grade_distribution': grade_distribution,
        'at_risk_students': at_risk,
        'top_performers': [
            {'roll_number': s['roll_number'], 'name': s['name'], 'total': s['total']}
            for s in top_performers
        ],
        'component_analysis': component_analysis
    }


def build_analysis_prompt(students: list, analysis: dict, course_info: dict) -> str:
    """Build comprehensive prompt for AI insights"""
    
    prompt = f"""You are a faculty data analyst providing insights on student performance.

COURSE INFORMATION:
Course: {course_info.get('course_name', 'N/A')}
Total Students: {analysis['total_students']}
Assessment Components: {', '.join(course_info.get('assessment_components', []))}

STATISTICAL SUMMARY:
- Mean Score: {analysis['mean_score']}
- Median Score: {analysis['median_score']}
- Standard Deviation: {analysis['std_deviation']}
- Highest Score: {analysis['highest_score']}
- Lowest Score: {analysis['lowest_score']}

PASS/FAIL ANALYSIS:
- Passed: {analysis['pass_count']} students ({analysis['pass_percentage']}%)
- Failed: {analysis['fail_count']} students

GRADE DISTRIBUTION:
"""
    
    for grade, count in analysis['grade_distribution'].items():
        prompt += f"- {grade}: {count} students\n"
    
    if analysis['at_risk_students']:
        prompt += f"\nAT-RISK STUDENTS ({len(analysis['at_risk_students'])} students below 50%):\n"
        for student in analysis['at_risk_students'][:10]:  # Limit to 10
            prompt += f"- {student['name']} ({student['roll_number']}): {student['total']} marks\n"
    
    if analysis['top_performers']:
        prompt += f"\nTOP PERFORMERS:\n"
        for i, student in enumerate(analysis['top_performers'], 1):
            prompt += f"{i}. {student['name']} ({student['roll_number']}): {student['total']} marks\n"
    
    if analysis['component_analysis']:
        prompt += f"\nCOMPONENT-WISE ANALYSIS:\n"
        for component, stats in analysis['component_analysis'].items():
            prompt += f"- {component}: Mean={stats['mean']:.2f}, Max={stats['max']}, Min={stats['min']}\n"
    
    prompt += """

TASK: Provide a comprehensive analysis including:
1. Overall class performance assessment
2. Strengths and weaknesses in different components
3. Actionable recommendations for at-risk students
4. Suggestions for improving overall performance
5. Comparison with typical distribution patterns

Present your analysis in a clear, structured format with specific, data-driven insights.
"""
    
    return prompt
