INFO:     127.0.0.1:57334 - "GET /api/v1/sessions/6979b5203a417bc28f1d19fc/messages HTTP/1.1" 200 OK

============================================================
📚 CONVERSATION HISTORY ANALYSIS
============================================================
Total messages in session: 8

🧠 HYBRID CONTEXT BUILDER
  Total messages: 8
  Strategy: ALL VERBATIM (≤8 messages)     

📊 Context Metadata:
  - User messages: 4
  - Assistant messages: 4
  - Has context: True

📝 Formatted history entries: 8

🔍 History structure:
  [1] user: Hi
  [2] assistant: Hello. How can I assist you with your academic inquiries at Nova Crest Institute...
  [3] user: Exam components please
  [4] assistant: The exam components include:

* Mid-semester tests or internal examinations
* As...
  [5] user: ESE?
  [6] assistant: The End-Semester Examination (ESE) is a comprehensive examination conducted at t...
  [7] user: What is the other component?   
  [8] assistant: The other component is the Continuous Assessment, which may include mid-semester...
============================================================


🎯 ATTEMPT 1: Original query
  🔍 Retrieving relevant chunks...
Batches: 100%|█| 1/1 
  📦 Retrieved 5 chunks in 64ms
  💬 Using conversation context: 8 messages
  📝 Formatting context...
  📄 Context size: 3647 characters
  🤖 Generating answer...

💬 BUILDING PROMPT WITH HISTORY
  Including 8 history entries
    Student: Exam components please        
    Advisor: The exam components include:  

* Mid-semester tests or intern...
    Student: ESE?
    Advisor: The End-Semester Examination (ESE) is a comprehensive examin...
    Student: What is the other component?  
    Advisor: The other component is the Continuous Assessment, which may ...

📤 Final prompt length: 5812 characters    
  ❌ Refused - insufficient context

⚠️ First attempt refused - trying with conttextualized query...
🔄 ATTEMPT 2: Query rewriting
  🔄 Attempting query rewrite with conversation context...
  🔄 Rewriting query: 'Explain both in detail please'
  ✅ Rewritten: 'What are the details of the End-Semester Examination (ESE) and the Continuous Assessment, including their components and weightage in the total course evaluation, as discussed in the context of the course evaluation structure?'
  📝 Original: 'Explain both in detail please'
  ✨ Enhanced: 'What are the details of the End-Semester Examination (ESE) and the Continuous Assessment, including their components and weightage in the total course evaluation, as discussed in the context of the course evaluation structure?'

🎯 Retrying with enhanced query...
  🔍 Retrieving relevant chunks...
Batches: 100%|█| 1/1 
  📦 Retrieved 5 chunks in 95ms
  💬 Using conversation context: 8 messages
  📝 Formatting context...

💬 BUILDING PROMPT WITH HISTORY
  Including 8 history entries
    Student: Exam components please
    Advisor: The exam components include:

* Mid-semester tests or intern...
    Student: ESE?
    Advisor: The End-Semester Examination (ESE) is a comprehensive examin...
    Student: What is the other component?
    Advisor: The other component is the Continuous Assessment, which may ...

📤 Final prompt length: 6749 characters
  ✅ Generated answer in 519ms
  ✅ Success with rewritten query!