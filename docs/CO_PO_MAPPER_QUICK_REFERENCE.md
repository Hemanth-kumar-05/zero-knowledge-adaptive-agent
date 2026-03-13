# CO-PO Mapper - Quick Reference Card

## What is CO-PO Mapper? 📊
Automatically maps your course activities, assignments, or learning objectives to Course Outcomes (CO) and Program Outcomes (PO) with relevance scores.

## Quick Start (Faculty)

### 1. Create Your Query File
Save as `query.json`:
```json
{
  "query": "Describe your activity here"
}
```

### 2. Access the Tool
1. Login to system
2. Go to Extensions → CO-PO Mapper
3. Click "Start Chat"

### 3. Upload & Analyze
1. Click 📎 attachment icon
2. Select your JSON file
3. Get instant CO-PO mapping!

## Sample Queries

### Example 1: Lab Assignment
```json
{
  "query": "Students will design and implement a web application using modern frameworks to solve real-world problems while working in teams"
}
```
**Maps to:** CO2, CO4, PO3, PO5, PO8

### Example 2: Theory Question
```json
{
  "query": "Understand and explain the fundamental principles of data structures and algorithms"
}
```
**Maps to:** CO1, PO1, PO10

### Example 3: Project Work
```json
{
  "query": "Research and investigate sustainable IoT solutions for smart cities, considering societal impact and ethical implications"
}
```
**Maps to:** CO3, CO4, PO4, PO6, PO9

## Understanding Results

### Relevance Score
- **0.8 - 1.0**: Strong alignment ✅
- **0.5 - 0.8**: Moderate alignment ⚠️
- **< 0.5**: Weak alignment ❌

### Confidence Score
- Overall mapping quality
- Higher = better keyword matches

## What Gets Mapped?

### Course Outcomes (CO)
- **CO1**: Understand fundamentals
- **CO2**: Apply knowledge
- **CO3**: Analyze & evaluate
- **CO4**: Design & develop
- **CO5**: Integrate & synthesize

### Program Outcomes (PO)
- **PO1**: Engineering knowledge
- **PO2**: Problem analysis
- **PO3**: Design solutions
- **PO4**: Conduct research
- **PO5**: Modern tools
- **PO6**: Society & sustainability
- **PO7**: Communication
- **PO8**: Teamwork
- **PO9**: Ethics
- **PO10**: Life-long learning

## Tips for Better Results

✅ Use action verbs (design, analyze, implement, evaluate)
✅ Include technical context (system, tool, method)
✅ Mention team/individual aspects
✅ Specify application domain
❌ Avoid vague descriptions
❌ Don't use single words

## Use Cases

- 📝 Syllabus creation
- 📋 Assignment design
- 🧪 Lab activity planning
- 📊 Assessment mapping
- 🎓 Project evaluation
- 📈 Accreditation documentation

## File Location
Script: `scripts/test_co_po_mapper.py`
Sample: `scripts/test_co_po_query.json`
Full Guide: `docs/CO_PO_MAPPER_SETUP.md`

---

**Need Help?** Contact your system administrator or refer to the full setup guide.
