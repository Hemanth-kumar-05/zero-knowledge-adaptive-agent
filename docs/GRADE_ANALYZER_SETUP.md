# Grade Analyzer Extension Setup Guide

## Overview
The **Grade Analyzer** is a script-based extension that helps faculty analyze student performance data. Upload a CSV or JSON file with student marks, and get comprehensive statistical analysis with AI-powered insights.

---

## Extension Configuration

### Basic Information
- **Extension Name**: Grade Analyzer
- **Extension ID**: `grade-analyzer`
- **Extension Type**: `script-based`
- **Script File**: `scripts/grade_analyzer_extension.py`
- **Handler Function**: `process`

### Welcome Message
```
Welcome to Grade Analyzer! Upload your student marks file (CSV or JSON) to get comprehensive performance analysis with statistical insights and recommendations.
```

### Input Placeholder
```
Ask for analysis insights after uploading grades file
```

### Required File Types
```json
[".csv", ".json"]
```

### System Prompt
```
You are an expert faculty data analyst specializing in student performance evaluation. Your role is to:

1. Interpret statistical data from grade analysis
2. Identify performance trends and patterns
3. Provide actionable recommendations for student improvement
4. Suggest teaching strategies based on data insights
5. Highlight areas needing attention

Always provide clear, structured analysis with specific data points. Be constructive and focused on student success.
```

---

## Input Format

### CSV Format (Recommended)
```csv
roll_number,name,CA1,CA2,ESE,Assignment,Lab,Total
CS001,Arjun Kumar,18,17,45,9,19,108
CS002,Priya Sharma,16,15,38,8,17,94
CS003,Rahul Verma,19,18,48,10,20,115
```

**Required Columns:**
- `roll_number` or `Roll Number` - Student identifier
- `name` or `Name` - Student name
- Additional columns - Assessment components (CA1, CA2, ESE, Assignment, Lab, etc.)

**Notes:**
- First row must be headers
- Numeric values for marks (empty cells treated as 0)
- Column names become assessment component names
- Total can be auto-calculated or provided

### JSON Format (Alternative)
```json
{
  "course_info": {
    "course_name": "Database Management Systems",
    "course_code": "CS301",
    "max_marks": 120,
    "passing_marks": 48,
    "assessment_components": ["CA1", "CA2", "ESE", "Assignment", "Lab"]
  },
  "students": [
    {
      "roll_number": "CS001",
      "name": "Arjun Kumar",
      "marks": {
        "CA1": 18,
        "CA2": 17,
        "ESE": 45,
        "Assignment": 9,
        "Lab": 19
      }
    },
    {
      "roll_number": "CS002",
      "name": "Priya Sharma",
      "marks": {
        "CA1": 16,
        "CA2": 15,
        "ESE": 38,
        "Assignment": 8,
        "Lab": 17
      }
    }
  ]
}
```

---

## Analysis Output

The analyzer provides:

### 1. Statistical Summary
- Mean, median, standard deviation
- Highest and lowest scores
- Score distribution histogram

### 2. Pass/Fail Analysis
- Pass percentage
- Failed student count
- At-risk students (below 50%)

### 3. Grade Distribution
Standard grade bands:
- A+ (90-100)
- A (80-89)
- B+ (70-79)
- B (60-69)
- C (50-59)
- D (40-49)
- F (<40)

### 4. Component-wise Analysis
For each assessment:
- Average score
- Maximum/minimum scores
- Students below average

### 5. Student Identification
- Top 5 performers
- At-risk students list
- Individual weak areas

### 6. AI Insights
- Performance trends
- Recommendations for improvement
- Teaching strategy suggestions
- Comparison with typical distributions

---

## Usage Example

1. **Upload File**: Click attachment button and select CSV/JSON file
2. **Request Analysis**: Type something like:
   - "Analyze the class performance"
   - "Who are the at-risk students?"
   - "What are the weak areas in this course?"
   - "Provide recommendations for improvement"

3. **Get Insights**: AI generates comprehensive analysis with:
   - Statistical breakdown
   - Visual-friendly summaries
   - Actionable recommendations

---

## Sample Data File

A sample CSV file is available at: `scripts/sample_grades.csv`

Use it to test the extension. It contains:
- 25 students
- 5 assessment components (CA1, CA2, ESE, Assignment, Lab)
- Realistic score distribution

---

## MongoDB Setup (Admin)

```javascript
db.extensions.insertOne({
  name: "Grade Analyzer",
  description: "Analyze student performance data with AI-powered insights. Upload marks CSV/JSON to get statistical analysis, grade distribution, at-risk student identification, and personalized recommendations.",
  extension_id: "grade-analyzer",
  icon: "📊",
  extension_type: "script-based",
  welcome_message: "Welcome to Grade Analyzer! Upload your student marks file (CSV or JSON) to get comprehensive performance analysis with statistical insights and recommendations.",
  input_placeholder: "Ask for analysis insights after uploading grades file",
  required_file_types: [".csv", ".json"],
  system_prompt: "You are an expert faculty data analyst specializing in student performance evaluation. Your role is to: 1) Interpret statistical data from grade analysis, 2) Identify performance trends and patterns, 3) Provide actionable recommendations for student improvement, 4) Suggest teaching strategies based on data insights, 5) Highlight areas needing attention. Always provide clear, structured analysis with specific data points. Be constructive and focused on student success.",
  script_config: {
    script_file_id: null,  // Upload script via admin panel
    handler_function: "process"
  },
  created_by: null,
  is_active: true,
  created_at: new Date(),
  updated_at: new Date()
});
```

---

## Features

✅ **CSV & JSON Support** - Flexible input formats
✅ **Comprehensive Statistics** - Mean, median, std dev, distribution
✅ **Grade Bands** - Standard A+ to F grading
✅ **At-risk Detection** - Identify struggling students early
✅ **Component Analysis** - Pinpoint weak assessment areas
✅ **AI Insights** - Smart recommendations based on data
✅ **Top Performers** - Recognize high-achieving students
✅ **Pass/Fail Analytics** - Track success rates

---

## Extension Behavior

1. **File Upload**: Extension script executes automatically
2. **Data Parsing**: Reads CSV/JSON and extracts student records
3. **Statistical Analysis**: Calculates all metrics
4. **Prompt Building**: Creates comprehensive data summary
5. **AI Generation**: LLM analyzes data and provides insights
6. **Response Display**: User sees formatted analysis with tables

---

## Tips for Faculty

1. **Consistent Format**: Use same column names across different courses
2. **Regular Analysis**: Upload after each assessment cycle
3. **Compare Trends**: Track performance across semesters
4. **Early Intervention**: Act on at-risk student alerts
5. **Component Focus**: Use component analysis to improve teaching
6. **Documentation**: Keep analysis reports for accreditation

---

## Troubleshooting

**Error: "No student data found"**
- Check CSV has header row
- Ensure at least 2 columns (roll_number, name) exist
- Verify file encoding is UTF-8

**Error: "Processing error"**
- Check marks are numeric values
- Remove special characters from names
- Ensure CSV is properly formatted

**Low accuracy in insights**
- Provide meaningful column names
- Add course info in JSON format
- Include more assessment components
- Use consistent grading scales

---

## Related Extensions

- **CO-PO Mapper**: Map course outcomes to programme outcomes
- **Question Paper Generator**: Create exam questions with AI
- **Lab Report Analyzer**: Grade and provide feedback on lab submissions
