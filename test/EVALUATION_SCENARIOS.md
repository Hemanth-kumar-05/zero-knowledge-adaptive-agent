# Evaluation Scenarios

## Purpose

This document defines benchmark scenarios for the metrics described in [EVALUATION_METRICS.md](/c:/Users/hemanthk/Project%20Work%20II/test/EVALUATION_METRICS.md).

These scenarios are designed for:

1. final review demonstration support
2. structured manual evaluation
3. future automated evaluation harness implementation

Each scenario includes:
- scenario ID
- target metric
- setup
- user action
- expected behavior
- scoring notes

## Scenario Design Principles

- Each scenario should isolate one main behavior.
- Some scenarios may contribute to multiple metrics.
- Preference and memory scenarios should use synthetic users to avoid contamination.
- Cross-user scenarios must use clearly distinct user identities and preferences.
- Policy-update scenarios should be run only when Phase 3 is enabled.

## A. Personalization Quality Scenarios

### SCN-PERS-01: Concise Response Preference

Target metrics:
- Personalization Accuracy
- Personalization Consistency

Setup:
- Create a user with locked preference: `communication_style = concise`
- No special memory facts required

User action:
- Ask: "Explain the exam registration process."

Expected behavior:
- Response should be short and direct
- No unnecessary elaboration
- Response should still remain correct and grounded

Scoring notes:
- Pass if response clearly reflects concise style
- Fail if response becomes long, verbose, or overly detailed

### SCN-PERS-02: Detailed Response Preference

Target metrics:
- Personalization Accuracy

Setup:
- Create a user with locked preference: `communication_style = detailed`

User action:
- Ask: "Explain the exam registration process."

Expected behavior:
- Response should include expanded explanation and steps
- Should provide more context than in SCN-PERS-01

Scoring notes:
- Compare against concise scenario output for contrast

### SCN-PERS-03: Bullet Format Preference

Target metrics:
- Personalization Accuracy

Setup:
- Create a user with locked preference: `response_format = lists`

User action:
- Ask: "What are the rules for course withdrawal?"

Expected behavior:
- Response should be formatted as bullets or a clearly structured list

Scoring notes:
- Fail if response is a plain block paragraph without list structure

### SCN-PERS-04: Technical Level Preference

Target metrics:
- Personalization Accuracy

Setup:
- Create a user with locked preference: `technical_level = beginner`

User action:
- Ask: "How does the policy update workflow operate?"

Expected behavior:
- Response should use simpler language
- Response should explain technical terms instead of assuming expertise

Scoring notes:
- Compare with advanced-user version of the same query

### SCN-PERS-05: Freeform Manual Preference

Target metrics:
- Personalization Accuracy

Setup:
- Add a manual custom preference such as:
  - "Always answer me in short bullet points with one example."

User action:
- Ask: "What is the CA and ESE evaluation pattern?"

Expected behavior:
- Response should reflect the exact freeform preference

Scoring notes:
- Useful for validating custom preference handling

### SCN-PERS-06: Multi-turn Preference Consistency

Target metrics:
- Personalization Consistency

Setup:
- Same user as SCN-PERS-03 or SCN-PERS-05

User action:
- Ask 3 consecutive academic questions in the same session

Expected behavior:
- Response format should remain consistent across turns

Scoring notes:
- Fail if the style is obeyed only on the first turn

## B. Zero-Knowledge Compliance Scenarios

### SCN-ZKC-01: Fresh User Without Preferences

Target metrics:
- Zero-Knowledge Compliance
- False Personalization Rate

Setup:
- Create a fresh user with:
  - no preferences
  - no facts
  - no prior session history

User action:
- Ask: "Explain the exam registration process."

Expected behavior:
- Response should be neutral
- No invented personalization
- No mention of user-specific context

Scoring notes:
- Fail if the system behaves as if it knows the user already

### SCN-ZKC-02: Fresh User Without Memory Facts

Target metrics:
- Zero-Knowledge Compliance

Setup:
- Fresh user with no facts

User action:
- Ask: "Given my current courses, what should I prioritize?"

Expected behavior:
- System should not invent current courses
- Should either answer generally or ask for clarification

Scoring notes:
- Strong test for hallucinated personalization

## C. Memory Relevance and Fact Usage Scenarios

### SCN-MEM-01: Relevant Academic Fact Usage

Target metrics:
- User Memory Relevance Score
- End-to-End Task Success Rate

Setup:
- Store fact:
  - `current_courses = ["Machine Learning", "Database Systems"]`

User action:
- Ask: "What should I focus on this week for my studies?"

Expected behavior:
- Response may refer to the stored courses
- Memory usage should be relevant and useful

Scoring notes:
- Score higher if memory is used naturally and correctly

### SCN-MEM-02: Irrelevant Memory Should Not Be Injected

Target metrics:
- User Memory Relevance Score

Setup:
- Store fact:
  - `advisor = "Dr. Kumar"`

User action:
- Ask: "What is the procedure for exam registration?"

Expected behavior:
- Response should not force irrelevant advisor information into the answer

Scoring notes:
- Fail if irrelevant memory appears

### SCN-MEM-03: Identity Fact Usage

Target metrics:
- User Memory Relevance Score

Setup:
- Store fact:
  - `year = "3rd year"`
  - `major = "Computer Science"`

User action:
- Ask: "What academic advice would you give me based on my profile?"

Expected behavior:
- Response may use year and major appropriately

Scoring notes:
- Good test for helpful personalization vs overreach

### SCN-MEM-04: Concern Fact Usage

Target metrics:
- User Memory Relevance Score

Setup:
- Store fact:
  - `attendance_concern = "worried about attendance shortage"`

User action:
- Ask: "What should I do next?"

Expected behavior:
- Response should acknowledge relevant concern context

Scoring notes:
- Good for testing temporary concern memory usefulness

## D. Memory Isolation and Safety Scenarios

### SCN-ISO-01: Cross-User Fact Isolation

Target metrics:
- Memory Isolation Integrity

Setup:
- User A facts:
  - `major = "Mechanical Engineering"`
- User B facts:
  - `major = "Computer Science"`

User action:
- Ask as User B: "What do you know about my academic profile?"

Expected behavior:
- Response must only reflect User B data

Scoring notes:
- Any appearance of User A data is an immediate fail

### SCN-ISO-02: Cross-User Preference Isolation

Target metrics:
- Memory Isolation Integrity

Setup:
- User A preference:
  - concise
- User B preference:
  - detailed

User action:
- Ask same question from both users

Expected behavior:
- Each response should follow only that user’s preferences

Scoring notes:
- Useful for testing preference leakage

### SCN-ISO-03: Session Ownership Isolation

Target metrics:
- Memory Isolation Integrity
- User Control Compliance

Setup:
- Create session for User A
- Attempt to access messages as User B

User action:
- Retrieve session messages with the wrong user context

Expected behavior:
- Access denied or protected behavior

Scoring notes:
- Backend API security scenario

## E. Preference Extraction Scenarios

### SCN-PREFX-01: Explicit Preference Statement

Target metrics:
- Preference Extraction Precision

Setup:
- Fresh user

User action:
- In a conversation, user says:
  - "I prefer concise answers from now on."

Expected behavior:
- System should extract a concise preference correctly

Scoring notes:
- Check extracted category, value, and confidence

### SCN-PREFX-02: One-Time Request Should Not Become Preference

Target metrics:
- Preference Extraction Precision
- False Personalization Rate

Setup:
- Fresh user

User action:
- User says:
  - "Can you explain this briefly just this time?"

Expected behavior:
- System should not persist this as a general preference

Scoring notes:
- Important negative case

### SCN-PREFX-03: Ambiguous Statement

Target metrics:
- Preference Extraction Precision

Setup:
- Fresh user

User action:
- User says:
  - "That was helpful."

Expected behavior:
- No preference should be extracted

Scoring notes:
- Strong false-positive check

## F. Fact Extraction Scenarios

### SCN-FACT-01: Explicit Identity Fact

Target metrics:
- Fact Extraction Precision

Setup:
- Fresh user

User action:
- User says:
  - "I am Hemanth, and I am in 3rd year Computer Science."

Expected behavior:
- Extract:
  - name
  - year
  - major

Scoring notes:
- Precision-oriented case

### SCN-FACT-02: Academic Context Fact

Target metrics:
- Fact Extraction Precision

Setup:
- Fresh user

User action:
- User says:
  - "I am taking Machine Learning and Database Systems this semester."

Expected behavior:
- Extract `current_courses`

### SCN-FACT-03: Temporary Concern

Target metrics:
- Fact Extraction Precision

Setup:
- Fresh user

User action:
- User says:
  - "I am really worried about my attendance shortage."

Expected behavior:
- Extract concern-type fact with temporary retention

### SCN-FACT-04: Non-Factual Message

Target metrics:
- Fact Extraction Precision

Setup:
- Fresh user

User action:
- User says:
  - "Thanks, that makes sense."

Expected behavior:
- No fact should be extracted

## G. Groundedness Scenarios

### SCN-GRD-01: Known Policy Question

Target metrics:
- Grounded Response Fidelity
- End-to-End Task Success Rate

Setup:
- Chroma contains the relevant policy chunk(s)

User action:
- Ask a policy question clearly covered by the knowledge base

Expected behavior:
- Answer should align with retrieved sources

Scoring notes:
- Good baseline groundedness case

### SCN-GRD-02: Out-of-Scope Question

Target metrics:
- Grounded Response Fidelity

Setup:
- Ask a question outside the known academic/policy scope

User action:
- Example:
  - "What is the weather in Paris tomorrow?"

Expected behavior:
- System should not fabricate unsupported institutional answers

Scoring notes:
- Fail if hallucination appears as grounded fact

### SCN-GRD-03: Multi-Source Answer

Target metrics:
- Grounded Response Fidelity

Setup:
- Ask a question whose answer likely combines multiple retrieved chunks

Expected behavior:
- Answer should integrate sources coherently without unsupported additions

## H. Contradiction Handling Scenarios

### SCN-CON-01: Preference Conflict Detection

Target metrics:
- Contradiction Resolution Rate

Setup:
- User has two conflicting preferences in the same category

User action:
- Run conflict-check workflow

Expected behavior:
- Conflict should be detected and surfaced

### SCN-CON-02: User Claim Contradicts Retrieved Policy

Target metrics:
- Contradiction Resolution Rate
- Policy Claim Detection Precision

Setup:
- User states a policy claim that conflicts with current Chroma knowledge

User action:
- Example:
  - "The new circular says CA is now 50%."

Expected behavior:
- Claim should be flagged for contradiction/policy review workflow

### SCN-CON-03: Non-Contradictory Clarification

Target metrics:
- Contradiction Resolution Rate

Setup:
- User asks a clarification question but does not contradict policy

Expected behavior:
- System should not incorrectly trigger contradiction workflow

## I. Knowledge Evolution / Policy Update Scenarios

### SCN-KE-01: Policy Claim Detection and Proof Request

Target metrics:
- Knowledge Evolution Stability
- Policy Claim Detection Precision
- End-to-End Task Success Rate

Setup:
- Phase 3 enabled
- authenticated user

User action:
- Submit a policy-change claim

Expected behavior:
- System should detect the claim
- ask for proof upload
- create pending claim state

### SCN-KE-02: Proof Upload and Ticket Creation

Target metrics:
- Knowledge Evolution Stability

Setup:
- pending claim exists in session metadata

User action:
- upload proof
- create ticket with proofs

Expected behavior:
- ticket should be created successfully
- session pending claim should be cleared

### SCN-KE-03: Find Affected Chunks

Target metrics:
- Knowledge Evolution Stability

Setup:
- approved or valid ticket exists

User action:
- run affected chunk search

Expected behavior:
- relevant chunks returned
- chunk list meaningful for reviewer

### SCN-KE-04: Apply Deprecation and Create New Chunks

Target metrics:
- Knowledge Evolution Stability

Setup:
- approved ticket
- selected chunks
- replacement text

User action:
- apply deprecation workflow

Expected behavior:
- old chunks deprecated
- new chunks created
- ticket updated to implemented
- audit trail created

### SCN-KE-05: Post-Update Retrieval Correctness

Target metrics:
- Knowledge Evolution Stability
- Grounded Response Fidelity

Setup:
- after SCN-KE-04

User action:
- ask the same policy question again

Expected behavior:
- answer should reflect updated policy knowledge

## J. End-to-End Task Scenarios

### SCN-TASK-01: Personalized Academic QA

Target metrics:
- End-to-End Task Success Rate

Setup:
- user with preference and memory facts

User action:
- ask a relevant academic question

Expected behavior:
- correct
- grounded
- personalized

### SCN-TASK-02: Memory Learn and Reuse

Target metrics:
- End-to-End Task Success Rate

Setup:
- user states a fact in an earlier turn

User action:
- later asks a question where that fact should help

Expected behavior:
- memory extracted and reused correctly

### SCN-TASK-03: Policy Challenge Workflow

Target metrics:
- End-to-End Task Success Rate

Setup:
- authenticated user
- Phase 3 enabled

User action:
- claim policy has changed
- upload proof
- create ticket

Expected behavior:
- workflow completes without error

## K. Secondary Operational Scenarios

### SCN-OPS-01: Health Endpoint Readiness

Target metrics:
- Response Latency
- Task Success support

Setup:
- app running

User action:
- call health, live, and ready endpoints

Expected behavior:
- endpoints respond correctly

### SCN-OPS-02: Risk Alert Generation

Target metrics:
- Risk Alert Precision

Setup:
- create a conversation with repeated attendance/deadline concern patterns

User action:
- ask another follow-up query

Expected behavior:
- risk alert appears only when pattern is sufficiently strong

### SCN-OPS-03: Extension Execution

Target metrics:
- Extension Execution Success Rate

Setup:
- create or use an extension session

User action:
- invoke prompt-based or script-based extension

Expected behavior:
- extension behavior completes correctly

## Recommended Minimal Benchmark Set

If only a compact set is needed first, start with:

- SCN-PERS-01
- SCN-PERS-03
- SCN-ZKC-01
- SCN-MEM-01
- SCN-MEM-02
- SCN-ISO-01
- SCN-PREFX-01
- SCN-PREFX-02
- SCN-FACT-01
- SCN-GRD-01
- SCN-GRD-02
- SCN-CON-02
- SCN-KE-01
- SCN-KE-02
- SCN-KE-05
- SCN-TASK-01
- SCN-TASK-02

This gives a strong first benchmark without being too large.

## Next Step

Once these scenarios are approved, they can be converted into:

- machine-readable benchmark JSON files
- automated API-driven test runs
- AI-judge scoring workflows
- percentage-based metric reports
