# Question Paper Generator Extension Setup Guide

## Overview
The **Question Paper Generator** is a prompt-based extension that helps faculty create exam questions aligned with Bloom's Taxonomy. It generates diverse question types with model answers, marking schemes, and cognitive level mapping.

---

## Extension Configuration

### Basic Information
- **Extension Name**: Question Paper Generator
- **Extension ID**: `question-paper-generator`
- **Extension Type**: `prompt-based`
- **Script File**: None (prompt-based)
- **Handler Function**: N/A

### Welcome Message
```
Welcome to Question Paper Generator! 🎓

I can help you create:
- Exam questions (MCQ, Short Answer, Long Answer, Numerical)
- Questions mapped to Bloom's Taxonomy levels
- Model answers with marking schemes
- Course Outcome aligned questions

Tell me about your course, topic, difficulty level, and question requirements!
```

### Input Placeholder
```
Describe the subject, topic, difficulty level, and number of questions needed
```

### Required File Types
```json
[]
```
(No files required - purely conversational)

### System Prompt
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
1. **Multiple Choice Questions (MCQ)**
   - 4 options (A, B, C, D)
   - One correct answer
   - Plausible distractors
   - Mark: 1-2 marks each

2. **Short Answer Questions (2-5 marks)**
   - Concise answers (50-100 words)
   - Test specific concepts
   - Clear marking points

3. **Long Answer Questions (10-15 marks)**
   - Detailed explanations
   - Multiple sub-parts
   - Comprehensive coverage

4. **Numerical Problems**
   - Step-by-step solutions
   - Formula-based
   - Mark distribution per step

5. **Case Study/Scenario-based**
   - Real-world application
   - Critical thinking required
   - Multiple sub-questions

**OUTPUT STRUCTURE:**
For each question provide:
1. Question number and text
2. Marks allocated
3. Bloom's level (L1-L6)
4. Course Outcome mapping (if specified)
5. Difficulty level (Easy/Medium/Hard)
6. Model answer with marking scheme
7. Common mistakes students make (optional)

**QUALITY GUIDELINES:**
- Use clear, unambiguous language
- Avoid trick questions
- Ensure questions are course-aligned
- Provide balanced difficulty distribution
- Include practical/application-based questions
- Test higher-order thinking skills (L4-L6)
- Follow standard university examination patterns

**FORMAT EXAMPLE:**

**Question 1 (5 marks) [Bloom's L2: Understand] [CO2] [Medium]**
Explain the difference between supervised and unsupervised learning with suitable examples.

**Model Answer:**
Supervised learning uses labeled training data where input-output pairs are known... (2 marks)
Examples: Classification, Regression... (1 mark)
Unsupervised learning works with unlabeled data... (1 mark)
Examples: Clustering, Dimensionality reduction... (1 mark)

**Marking Scheme:**
- Definition of supervised learning: 2 marks
- Examples of supervised learning: 1 mark
- Definition of unsupervised learning: 1 mark
- Examples of unsupervised learning: 1 mark

---

Always ask clarifying questions if requirements are unclear. Generate questions that promote deep learning and critical thinking.
```

---

## Usage Examples

### Example 1: Basic Request
**User Input:**
```
Generate 5 questions on Database Normalization for undergraduate students
```

**Extension Response:**
- 2-3 questions at L2 (Understand)
- 1-2 questions at L3 (Apply)
- 1 question at L4 (Analyze)
- Mix of MCQ, short answer, and numerical
- Total marks: ~25

### Example 2: Detailed Request
**User Input:**
```
Create a 60-mark question paper for Data Structures course covering:
- Topic: Trees (Binary Trees, BST, AVL)
- Difficulty: Medium to Hard
- Question types: 5 MCQs, 3 short answers (5 marks each), 2 long answers (15 marks each)
- Bloom's levels: Mix of L2, L3, L4, L5
- Map to CO3 and CO4
```

**Extension Response:**
- Structured question paper as per specification
- Each question with complete details
- Model answers with marking schemes
- Bloom's taxonomy and CO mapping clearly marked

### Example 3: Specific Bloom's Level
**User Input:**
```
Give me 3 Evaluate-level (L5) questions on Software Testing methodologies
```

**Extension Response:**
- Questions requiring critical evaluation
- Comparison of different approaches
- Judgment-based questions
- Comprehensive model answers

### Example 4: Real-world Scenario
**User Input:**
```
Create a case study question on Cloud Computing for final semester students (15 marks)
```

**Extension Response:**
- Realistic business scenario
- Multiple sub-questions testing different aspects
- Application of theoretical concepts
- Structured marking scheme

---

## Best Practices for Faculty

### 1. **Provide Clear Context**
Good: "Generate 10 questions on Neural Networks for BE Computer Science, covering backpropagation, activation functions, and CNNs"
Bad: "Give me some questions on AI"

### 2. **Specify Distribution**
- Mention marks allocation
- Bloom's level preference
- Question type mix
- Difficulty spread

### 3. **Align with Course Outcomes**
"Questions should test CO2: Ability to design and analyze algorithms"

### 4. **Review and Customize**
- AI-generated questions are a starting point
- Review for context-specific accuracy
- Adjust difficulty based on class performance
- Modify language to match your teaching style

### 5. **Iterate and Refine**
- Request modifications: "Make Q3 more challenging"
- Ask for alternatives: "Give another question at L4"
- Request explanations: "Explain why this tests L5"

---

## Sample Conversations

### Conversation 1: Creating Practice Questions
```
Faculty: I need 5 practice questions on Linked Lists for beginners

AI: I'll create 5 questions covering basic linked list concepts:

**Question 1 (2 marks) [L1: Remember] [Easy]**
Define a singly linked list and state its key characteristic.

**Model Answer:**
A singly linked list is a linear data structure where each node contains data and 
a pointer to the next node. Key characteristic: Sequential access only. (2 marks)

[... 4 more questions with increasing difficulty ...]

Faculty: Can you make Q4 more challenging?

AI: [Provides enhanced version at L4 analyzing time complexity...]
```

### Conversation 2: Full Question Paper
```
Faculty: Create a 100-mark question paper for Operating Systems covering:
- Process Management (30 marks)
- Memory Management (30 marks)  
- File Systems (20 marks)
- Deadlocks (20 marks)
Mix of all question types

AI: [Generates complete paper with sections, questions, model answers]

Faculty: For Q8, provide an alternative that tests L5 instead of L3

AI: [Replaces Apply-level question with Evaluate-level alternative]
```

---

## Features

✅ **Bloom's Taxonomy Aligned** - Questions mapped to cognitive levels
✅ **Multiple Question Types** - MCQ, Short, Long, Numerical, Case Study
✅ **Model Answers** - Complete solutions with marking schemes
✅ **CO Mapping** - Align questions with course outcomes
✅ **Difficulty Grading** - Easy, Medium, Hard classification
✅ **Iterative Refinement** - Request modifications and alternatives
✅ **Real-world Scenarios** - Application-based questions
✅ **Comprehensive Coverage** - Full question paper generation

---

## MongoDB Setup (Admin)

```javascript
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

## Prompt Templates for Faculty

### Template 1: Quick Questions
```
Generate [NUMBER] [QUESTION_TYPE] questions on [TOPIC] for [LEVEL] students
```

### Template 2: Detailed Request
```
Create a [MARKS]-mark question paper for [COURSE] covering:
- Topics: [LIST]
- Difficulty: [LEVEL]
- Question types: [DISTRIBUTION]
- Bloom's levels: [L1, L2, etc.]
- Map to [COs]
```

### Template 3: Specific Bloom's Level
```
Give me [NUMBER] [BLOOM_LEVEL]-level questions on [TOPIC]
```

### Template 4: Case Study
```
Create a case study question on [TOPIC] for [LEVEL] students ([MARKS] marks)
```

---

## Tips for Effective Use

1. **Start Broad, Then Refine**
   - Begin with general requirements
   - Request modifications based on output
   - Iterate until satisfied

2. **Be Specific About Level**
   - Mention student year (BE 2nd year, ME 1st sem)
   - Specify course code if available
   - Indicate if it's for internal/external exam

3. **Request Variations**
   - Ask for multiple versions of same question
   - Get alternative questions at different Bloom's levels
   - Request different difficulty levels

4. **Verify Content Accuracy**
   - Cross-check technical details
   - Ensure alignment with syllabus
   - Validate marking schemes

5. **Build Question Banks**
   - Save generated questions
   - Create topic-wise collections
   - Maintain difficulty-wise categorization

---

## Related Extensions

- **Grade Analyzer**: Analyze student performance after exams
- **CO-PO Mapper**: Map course outcomes to programme outcomes
- **Feedback Composer**: Generate constructive feedback for students
- **Rubric Creator**: Design grading rubrics for assessments
