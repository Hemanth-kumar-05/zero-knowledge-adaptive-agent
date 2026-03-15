# Evaluation Metrics

## Purpose

This document defines the evaluation framework for the application for two goals:

1. Final review / panel presentation
2. Research paper preparation

The system is not only a chatbot. It is a personalized academic assistant platform with:

- retrieval-augmented generation over institutional knowledge
- user preference learning and application
- user fact memory with explicit controls
- session-aware conversation handling
- risk detection
- role-aware governance
- extension support
- policy contradiction detection and knowledge evolution workflows

Therefore, the evaluation must measure both product usefulness and research contribution.

## Evaluation Dimensions

The complete evaluation is organized into five dimensions:

1. Personalization Quality
2. Memory Quality and Safety
3. Retrieval and Response Quality
4. Knowledge Evolution and Contradiction Handling
5. System Reliability and Governance

## Primary Metrics

These are the headline metrics recommended for the final review and for inclusion in the main results section of a research paper.

### 1. Personalization Accuracy

Definition:
Measures how often the system adapts the answer correctly to known user preferences or stored user context when personalization should apply.

Examples:
- concise vs detailed response style
- bullet-point vs paragraph format
- beginner vs advanced technical level
- use of stored academic context when relevant

Measurement:
- Create benchmark queries for users with predefined preferences/facts.
- Judge whether the generated response follows the expected personalized behavior.

Formula:

`Personalization Accuracy = Correctly personalized responses / Total personalization test cases`

Why it matters:
This is a core contribution of the system and directly demonstrates user-adaptive behavior.

### 2. Zero-Knowledge Compliance

Definition:
Measures how often the system avoids applying personalization when no user preferences or memory have been learned.

Measurement:
- Use fresh users with empty preferences and empty facts.
- Ask prompts similar to personalization tests.
- Check whether the system avoids inventing user-specific adaptation.

Formula:

`Zero-Knowledge Compliance = Non-personalized responses with no prior user knowledge / Total zero-knowledge test cases`

Why it matters:
This measures trustworthiness and prevents false personalization.

### 3. User Memory Relevance Score

Definition:
Measures how relevant the injected user facts are to the current query.

Note:
In this system, user memory is stored in MongoDB facts and injected as user context. It is different from Chroma-based document retrieval.

Measurement:
- For each memory-enabled response, evaluate whether the used user memory is relevant to the question.
- Score on a 3-point scale:
  - `0 = irrelevant`
  - `1 = partially relevant`
  - `2 = clearly relevant and helpful`

Formula:

`User Memory Relevance Score = Sum of relevance scores / Total memory-enabled test cases`

Why it matters:
It validates whether remembered user information actually improves response usefulness.

### 4. Memory Isolation Integrity

Definition:
Measures whether one user’s preferences, facts, or memory ever leak into another user’s responses.

Measurement:
- Create multiple users with clearly different stored information.
- Query each user independently.
- Check for any cross-user leakage.

Formula:

`Memory Isolation Integrity = Leak-free cross-user tests / Total cross-user tests`

Why it matters:
This is a critical privacy and safety metric.

### 5. Preference Extraction Precision

Definition:
Measures how often automatically extracted user preferences are correct.

Measurement:
- Prepare conversation snippets with annotated ground-truth preferences.
- Compare extracted preferences with the gold labels.

Formula:

`Preference Extraction Precision = Correctly extracted preferences / Total extracted preferences`

Why it matters:
It validates the quality of the automatic personalization-learning subsystem.

### 6. Fact Extraction Precision

Definition:
Measures how often automatically extracted user facts are correct.

Measurement:
- Prepare conversation snippets with annotated ground-truth identity, academic, and concern facts.
- Compare extracted facts with ground truth.

Formula:

`Fact Extraction Precision = Correctly extracted facts / Total extracted facts`

Why it matters:
It validates the memory-learning pipeline.

### 7. Grounded Response Fidelity

Definition:
Measures how often the generated answer remains faithful to retrieved academic or policy sources.

Measurement:
- For each benchmark query, evaluate the answer against the returned sources.
- Annotate each response as:
  - `Grounded`
  - `Partially grounded`
  - `Unsupported`

Suggested reported metric:

`Grounded Fidelity = Fully grounded responses / Total evaluated responses`

Why it matters:
This is essential for any RAG-based system and strengthens the research value of the work.

### 8. Contradiction Resolution Rate

Definition:
Measures how often the system correctly detects and handles contradictions in:

- user claims vs retrieved policy knowledge
- conflicting stored preferences
- conflicting user facts

Measurement:
- Build contradiction-oriented scenarios.
- Check whether the system identifies, routes, or resolves them correctly.

Formula:

`Contradiction Resolution Rate = Correctly handled contradiction cases / Total contradiction cases`

Why it matters:
This captures one of the more advanced reasoning and governance capabilities of the system.

### 9. Knowledge Evolution Stability

Definition:
Measures how safely and correctly the system updates policy knowledge when changes are detected and reviewed.

Measurement:
- Run end-to-end policy update workflows.
- Check:
  - affected chunks identified
  - old chunks deprecated correctly
  - new chunks created correctly
  - updated policy reflected in retrieval
  - audit trail preserved

Suggested sub-metrics:
- `Affected Chunk Recall`
- `Successful Policy Update Execution Rate`
- `Post-Update Retrieval Correctness`

Why it matters:
This is the main metric for the policy-unlearning and knowledge-evolution contribution.

### 10. End-to-End Task Success Rate

Definition:
Measures whether realistic user tasks are completed successfully from start to finish.

Example tasks:
- answer a policy question correctly
- remember and reuse a user fact
- obey a user formatting preference
- detect a policy-change claim and request proof
- complete a reviewed policy update workflow

Formula:

`Task Success Rate = Successfully completed scenarios / Total scenarios`

Why it matters:
This is highly effective for panel presentation because it maps directly to practical usefulness.

## Secondary Metrics

These metrics support the primary metrics and can be reported as secondary experimental results.

### 1. Personalization Consistency

Definition:
Measures whether the same user preferences are applied consistently across repeated interactions.

### 2. False Personalization Rate

Definition:
Measures how often the system personalizes incorrectly or unnecessarily.

### 3. Memory Update Correctness

Definition:
Measures whether updated or conflicting facts correctly replace older facts when appropriate.

### 4. User Control Compliance

Definition:
Measures whether explicit user controls are respected, including:

- forget
- reset
- confirm
- lock
- retention change

### 5. Risk Alert Precision

Definition:
Measures how often generated risk alerts correspond to genuine patterns of academic concern.

### 6. Session Context Continuity

Definition:
Measures whether the system uses session history correctly within a conversation.

### 7. Extension Execution Success Rate

Definition:
Measures how reliably prompt-based and script-based extensions work for valid inputs.

### 8. Policy Claim Detection Precision

Definition:
Measures how accurately the system detects genuine policy update claims while avoiding false alarms.

### 9. Audit Completeness

Definition:
Measures whether policy changes produce complete and traceable audit records.

### 10. Response Latency

Definition:
Measures average and percentile response times for important flows.

Suggested reporting:
- average latency
- p95 latency
- latency with and without personalization

## Recommended Final Metric Set

For a strong final review and research-paper evaluation, the following set is recommended as the main result table:

1. Personalization Accuracy
2. Zero-Knowledge Compliance
3. User Memory Relevance Score
4. Memory Isolation Integrity
5. Preference Extraction Precision
6. Fact Extraction Precision
7. Grounded Response Fidelity
8. Contradiction Resolution Rate
9. Knowledge Evolution Stability
10. End-to-End Task Success Rate

## Metric-to-System Mapping

### Personalization subsystem
- Personalization Accuracy
- Zero-Knowledge Compliance
- Preference Extraction Precision
- Personalization Consistency
- False Personalization Rate

### Memory subsystem
- User Memory Relevance Score
- Memory Isolation Integrity
- Fact Extraction Precision
- Memory Update Correctness
- User Control Compliance

### RAG subsystem
- Grounded Response Fidelity
- Session Context Continuity
- Response Latency

### Policy evolution subsystem
- Contradiction Resolution Rate
- Knowledge Evolution Stability
- Policy Claim Detection Precision
- Audit Completeness

### Platform / advanced features
- End-to-End Task Success Rate
- Extension Execution Success Rate
- Risk Alert Precision

## Presentation Strategy

### For final review / judges

Emphasize:
- end-to-end task success
- personalization quality
- memory safety
- grounded answers
- policy update workflow stability

Recommended demo narrative:
- show a user with no prior memory
- show learning of preference or fact
- show later personalized behavior
- show memory control
- show policy contradiction detection and review flow

### For research paper

Emphasize:
- measurable personalization
- controlled memory usage
- zero-knowledge compliance
- cross-user safety
- contradiction-aware knowledge evolution

Recommended paper structure:
- system architecture
- benchmark design
- metric definitions
- experimental setup
- quantitative results
- ablation or subsystem-wise analysis

## Notes for Implementation

- Evaluation should be performed primarily through backend APIs rather than manual frontend clicking.
- The frontend can be used for demonstration, but the backend APIs are the better target for repeatable experiments.
- Human annotation will likely be needed for:
  - personalization correctness
  - memory relevance
  - grounded response fidelity
  - contradiction handling quality
- Automated scoring can be used for:
  - isolation
  - extraction precision against labels
  - task completion
  - latency
  - audit existence

## Final Summary

The application should not be evaluated as a simple chatbot. It should be evaluated as a personalized academic assistant platform with:

- adaptive response generation
- explicit user memory
- memory safety and control
- grounded knowledge retrieval
- contradiction-aware policy evolution
- extension-driven specialization
- governance and auditability

This metric framework is designed to support both a convincing product demonstration and a publishable research evaluation.
