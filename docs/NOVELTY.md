## The Core Problem: What’s Missing?

Right now, your system answers:

> “What do I know about this user *so far*?”

But **novel systems answer**:

> “What is *likely to happen* to this user next — and what should I warn them about?”

That single shift → **research contribution**.

---

## The 3 Research Works That Fit PERFECTLY on Top of Your System

### 1. **Predictive Memory Reasoning (Academic Risk Prediction)**

This is the **cleanest upgrade** to your current architecture.

#### What’s new (research-wise)

You move from:

* **Memory as storage** → **Memory as signal**

Your memory already stores:

* User questions
* Preferences
* Uncertainty
* Corrections

Now you **reason over memory trends**.

#### Example

Instead of:

> “Attendance required is 75%”

You add:

> “Based on your past questions and current date, you are *at risk* of falling below 75% in 2 courses.”

#### Why this is novel

* RAG systems ≠ predictive
* Memory systems ≠ risk-aware

#### Paper framing

> **“Predictive Memory Reasoning in Zero-Knowledge RAG Systems”**

#### Minimal additions

* Risk rules (policy-derived)
* Temporal signals
* Confidence thresholds

✅ **Low effort, huge research payoff**

---

### 2. **What-If Scenario Planning (Counterfactual RAG)**

This is the **logical next step** after risk prediction.

#### What you already have

* Policies
* Constraints
* User profile
* Memory

#### What you add

* Simulated future states

#### Example

> “If I drop CS301 now, what happens?”

System:

* Retrieves policies
* Computes credit changes
* Projects graduation impact

#### Research novelty

* Counterfactual reasoning over retrieved knowledge
* Deterministic simulation + generative explanation

#### Paper framing

> **“Counterfactual Policy Reasoning using Retrieval-Augmented Generation”**

This pairs **beautifully** with risk prediction:

* Risk = *what might go wrong*
* What-if = *what happens if I act*

---

### 3. **User-Controlled Memory Boundaries (Selective Retention)**

This one upgrades your **existing preference extraction** into a **privacy contribution**.

You already:

* Auto-extract preferences
* Allow manual input

Now add:

* **User-governed memory control**

#### Example

* “Remember my advisor is Dr. X” → stored long-term
* “Don’t remember this conversation” → session-only
* “Forget my previous major” → unlearning trigger

#### Why this is research-worthy

Most systems:

* Decide memory policy themselves

You propose:

* **Human-in-the-loop memory governance**

This directly strengthens:

* Zero-knowledge compliance
* Knowledge unlearning
* Trust & safety claims in your abstract 

---

## The Clean “Novel Upgrade Set” for Your Project

If a reviewer asks:

> “What is new compared to standard RAG + memory?”

Your answer becomes:

> *We extend RAG-based adaptive agents with:*
>
> 1. **Predictive memory-based academic risk detection**
> 2. **Counterfactual what-if scenario reasoning over policies**
> 3. **User-controlled selective memory retention and unlearning**

That is a **clear, defensible, non-overengineered contribution set**.
