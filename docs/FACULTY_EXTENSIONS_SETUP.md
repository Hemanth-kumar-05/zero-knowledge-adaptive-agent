# Faculty Extensions - Quick Setup Guide

This guide helps you set up the **Grade Analyzer** and **Question Paper Generator** extensions for faculty use.

---

## Extension 1: Grade Analyzer (Script-based)

### What It Does
Analyzes student performance data from uploaded CSV/JSON files and provides statistical insights with AI-powered recommendations.

### Admin Setup Steps

1. **Navigate to Admin Panel** → Extensions → Create New Extension

2. **Fill Basic Information:**
   ```
   Name: Grade Analyzer
   Description: Analyze student performance data with AI-powered insights. Upload marks CSV/JSON to get statistical analysis, grade distribution, at-risk student identification, and personalized recommendations.
   Extension ID: grade-analyzer
   Icon: 📊
   Extension Type: script-based
   Status: Active
   ```

3. **Set Welcome Message:**
   ```
   Welcome to Grade Analyzer! Upload your student marks file (CSV or JSON) to get comprehensive performance analysis with statistical insights and recommendations.
   ```

4. **Set Input Placeholder:**
   ```
   Ask for analysis insights after uploading grades file
   ```

5. **Set Required File Types:**
   ```
   .csv, .json
   ```

6. **Upload Script File:**
   - File: `scripts/grade_analyzer_extension.py`
   - Handler Function: `process`

7. **Set System Prompt:**
   ```
   You are an expert faculty data analyst specializing in student performance evaluation. Your role is to: 1) Interpret statistical data from grade analysis, 2) Identify performance trends and patterns, 3) Provide actionable recommendations for student improvement, 4) Suggest teaching strategies based on data insights, 5) Highlight areas needing attention. Always provide clear, structured analysis with specific data points. Be constructive and focused on student success.
   ```

8. **Save Extension**

### Testing
1. Start a new session with Grade Analyzer
2. Upload `scripts/sample_grades.csv`
3. Ask: "Analyze the class performance"
4. Verify you get statistical breakdown, at-risk students, and recommendations

---

## Extension 2: Question Paper Generator (Prompt-based)

### What It Does
Generates exam questions aligned with Bloom's Taxonomy, complete with model answers and marking schemes.

### Admin Setup Steps

1. **Navigate to Admin Panel** → Extensions → Create New Extension

2. **Fill Basic Information:**
   ```
   Name: Question Paper Generator
   Description: Generate exam questions aligned with Bloom's Taxonomy. Create MCQs, short/long answer questions, numerical problems, and case studies with model answers and marking schemes.
   Extension ID: question-paper-generator
   Icon: 📝
   Extension Type: prompt-based
   Status: Active
   ```

3. **Set Welcome Message:**
   ```
   Welcome to Question Paper Generator! 🎓

   I can help you create:
   - Exam questions (MCQ, Short Answer, Long Answer, Numerical)
   - Questions mapped to Bloom's Taxonomy levels
   - Model answers with marking schemes
   - Course Outcome aligned questions

   Tell me about your course, topic, difficulty level, and question requirements!
   ```

4. **Set Input Placeholder:**
   ```
   Describe the subject, topic, difficulty level, and number of questions needed
   ```

5. **Set Required File Types:**
   ```
   (Leave empty - no files required)
   ```

6. **Set System Prompt:**
   ```
   You are an expert academic question paper creator with deep knowledge of pedagogy and assessment design. Your expertise includes:

   **CORE RESPONSIBILITIES:**
   1. Create exam questions aligned with Bloom's Taxonomy (Remember, Understand, Apply, Analyze, Evaluate, Create)
   2. Generate questions of varying difficulty levels (Easy, Medium, Hard)
   3. Provide comprehensive model answers with marking schemes
   4. Ensure questions test specific Course Outcomes (COs)
   5. Balance question types (MCQ, Short Answer, Long Answer, Numerical, Case Study)

   **BLOOM'S TAXONOMY MAPPING:**
   - **Remember (L1)**: Recall facts, terms, basic concepts (e.g., "Define...", "List...", "State...")
   - **Understand (L2)**: Explain ideas, concepts (e.g., "Explain...", "Describe...", "Summarize...")
   - **Apply (L3)**: Use information in new situations (e.g., "Calculate...", "Demonstrate...", "Solve...")
   - **Analyze (L4)**: Draw connections, distinguish between elements (e.g., "Compare...", "Analyze...", "Differentiate...")
   - **Evaluate (L5)**: Justify decisions, make judgments (e.g., "Evaluate...", "Critique...", "Assess...")
   - **Create (L6)**: Produce new work, design solutions (e.g., "Design...", "Construct...", "Develop...")

   **QUESTION FORMATS:**
   1. Multiple Choice Questions: 4 options, 1-2 marks
   2. Short Answer: 2-5 marks, 50-100 words
   3. Long Answer: 10-15 marks, detailed explanations
   4. Numerical: Step-by-step solutions
   5. Case Study: Real-world scenarios

   **OUTPUT STRUCTURE:**
   For each question:
   1. Question text with marks
   2. Bloom's level (L1-L6)
   3. CO mapping (if specified)
   4. Difficulty (Easy/Medium/Hard)
   5. Model answer with marking scheme

   **QUALITY GUIDELINES:**
   - Clear, unambiguous language
   - Balanced difficulty
   - Practical applications
   - Higher-order thinking (L4-L6)
   - Standard exam patterns

   Always generate questions that promote deep learning and critical thinking.
   ```

7. **Save Extension**

### Testing
1. Start a new session with Question Paper Generator
2. Ask: "Generate 5 questions on Binary Search Trees for undergraduate students"
3. Verify you get questions with Bloom's levels, model answers, and marking schemes

---

## File Structure

```
Project Root/
├── scripts/
│   ├── grade_analyzer_extension.py      # Script-based extension
│   ├── sample_grades.csv                # Sample data for testing
│   └── co_po_mapper_extension.py        # Existing extension
├── docs/
│   ├── GRADE_ANALYZER_SETUP.md          # Detailed setup guide
│   ├── QUESTION_PAPER_GENERATOR_SETUP.md # Detailed setup guide
│   ├── CO_PO_MAPPER_SETUP.md            # Existing extension guide
│   └── FACULTY_EXTENSIONS_SETUP.md      # This file
```

---

## Usage Scenarios

### Grade Analyzer Use Cases
1. **Post-Assessment Analysis**
   - Upload marks after CA/ESE
   - Identify at-risk students
   - Plan interventions

2. **Course Performance Tracking**
   - Compare across semesters
   - Track improvement trends
   - Evaluate teaching effectiveness

3. **Accreditation Reports**
   - Generate performance statistics
   - Document student outcomes
   - Support continuous improvement

### Question Paper Generator Use Cases
1. **Exam Preparation**
   - Create practice questions
   - Generate mock tests
   - Build question banks

2. **Assessment Design**
   - Ensure Bloom's level coverage
   - Balance difficulty levels
   - Align with course outcomes

3. **Quiz Creation**
   - Quick formative assessments
   - Topic-wise practice
   - Concept checks

---

## Comparison: Script-based vs Prompt-based

| Feature | Grade Analyzer (Script) | Question Paper Generator (Prompt) |
|---------|------------------------|-----------------------------------|
| **Type** | Script-based | Prompt-based |
| **File Upload** | Required (CSV/JSON) | Not required |
| **Processing** | Python script executes | Pure AI conversation |
| **Customization** | Modify Python code | Refine system prompt |
| **Deterministic** | Yes (same file = same stats) | No (AI generates variations) |
| **Output Format** | Structured data + AI analysis | Pure AI-generated text |
| **Use Case** | Data analysis | Content generation |
| **Complexity** | Higher (coding required) | Lower (prompt engineering) |

---

## Best Practices

### For Script-based Extensions
1. ✅ Test scripts locally before uploading
2. ✅ Handle errors gracefully
3. ✅ Validate input file format
4. ✅ Provide clear error messages
5. ✅ Document expected input format
6. ✅ Include sample data files
7. ✅ Use standard Python libraries only

### For Prompt-based Extensions
1. ✅ Write comprehensive system prompts
2. ✅ Include examples in prompt
3. ✅ Define output structure clearly
4. ✅ Set appropriate tone/style
5. ✅ Specify domain expertise
6. ✅ Test with various user inputs
7. ✅ Iterate and refine based on outputs

---

## Troubleshooting

### Grade Analyzer Issues
**Problem**: Script execution fails
- Check file format (CSV headers correct?)
- Verify encoding (UTF-8)
- Ensure numeric values for marks
- Review error message in response

**Problem**: No analysis generated
- Ensure at least 2 columns (roll_number, name)
- Check marks columns have numeric values
- Verify file isn't empty

### Question Paper Generator Issues
**Problem**: Questions not aligned to requirements
- Be more specific in request
- Mention Bloom's levels explicitly
- Specify marks distribution
- Provide topic details

**Problem**: Model answers too brief
- Request detailed explanations
- Ask for step-by-step solutions
- Specify marking scheme format

---

## Future Enhancements

### Grade Analyzer
- [ ] Support Excel files (.xlsx)
- [ ] Multi-course comparison
- [ ] Historical trend analysis
- [ ] Graphical visualizations
- [ ] Export reports as PDF

### Question Paper Generator
- [ ] Save question banks
- [ ] Generate full papers in LaTeX
- [ ] Import syllabus for alignment
- [ ] Difficulty prediction
- [ ] Auto-generate distractors for MCQs

---

## Support

For detailed documentation, see:
- [Grade Analyzer Setup Guide](./GRADE_ANALYZER_SETUP.md)
- [Question Paper Generator Setup Guide](./QUESTION_PAPER_GENERATOR_SETUP.md)
- [CO-PO Mapper Setup Guide](./CO_PO_MAPPER_SETUP.md)

---

## MongoDB Quick Insert Commands

```javascript
// Grade Analyzer
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
    script_file_id: null,
    handler_function: "process"
  },
  created_by: null,
  is_active: true,
  created_at: new Date(),
  updated_at: new Date()
});

// Question Paper Generator
db.extensions.insertOne({
  name: "Question Paper Generator",
  description: "Generate exam questions aligned with Bloom's Taxonomy. Create MCQs, short/long answer questions, numerical problems, and case studies with model answers and marking schemes.",
  extension_id: "question-paper-generator",
  icon: "📝",
  extension_type: "prompt-based",
  welcome_message: "Welcome to Question Paper Generator! 🎓\n\nI can help you create:\n- Exam questions (MCQ, Short Answer, Long Answer, Numerical)\n- Questions mapped to Bloom's Taxonomy levels\n- Model answers with marking schemes\n- Course Outcome aligned questions\n\nTell me about your course, topic, difficulty level, and question requirements!",
  input_placeholder: "Describe the subject, topic, difficulty level, and number of questions needed",
  required_file_types: [],
  system_prompt: "You are an expert academic question paper creator with deep knowledge of pedagogy and assessment design. Your expertise includes:\n\n**CORE RESPONSIBILITIES:**\n1. Create exam questions aligned with Bloom's Taxonomy (Remember, Understand, Apply, Analyze, Evaluate, Create)\n2. Generate questions of varying difficulty levels (Easy, Medium, Hard)\n3. Provide comprehensive model answers with marking schemes\n4. Ensure questions test specific Course Outcomes (COs)\n5. Balance question types (MCQ, Short Answer, Long Answer, Numerical, Case Study)\n\n**BLOOM'S TAXONOMY MAPPING:**\n- **Remember (L1)**: Recall facts, terms, basic concepts (e.g., \"Define...\", \"List...\", \"State...\")\n- **Understand (L2)**: Explain ideas, concepts (e.g., \"Explain...\", \"Describe...\", \"Summarize...\")\n- **Apply (L3)**: Use information in new situations (e.g., \"Calculate...\", \"Demonstrate...\", \"Solve...\")\n- **Analyze (L4)**: Draw connections, distinguish between elements (e.g., \"Compare...\", \"Analyze...\", \"Differentiate...\")\n- **Evaluate (L5)**: Justify decisions, make judgments (e.g., \"Evaluate...\", \"Critique...\", \"Assess...\")\n- **Create (L6)**: Produce new work, design solutions (e.g., \"Design...\", \"Construct...\", \"Develop...\")\n\n**QUESTION FORMATS:**\n1. Multiple Choice Questions: 4 options, 1-2 marks\n2. Short Answer: 2-5 marks, 50-100 words\n3. Long Answer: 10-15 marks, detailed explanations\n4. Numerical: Step-by-step solutions\n5. Case Study: Real-world scenarios\n\n**OUTPUT STRUCTURE:**\nFor each question:\n1. Question text with marks\n2. Bloom's level (L1-L6)\n3. CO mapping (if specified)\n4. Difficulty (Easy/Medium/Hard)\n5. Model answer with marking scheme\n\n**QUALITY GUIDELINES:**\n- Clear, unambiguous language\n- Balanced difficulty\n- Practical applications\n- Higher-order thinking (L4-L6)\n- Standard exam patterns\n\nAlways generate questions that promote deep learning and critical thinking.",
  created_by: null,
  is_active: true,
  created_at: new Date(),
  updated_at: new Date()
});
```

---

**Ready to use!** Both extensions are now documented and ready for deployment. Faculty can start using them immediately after admin setup.
