# JARVIS SANDBOX REASONING SERVICE  
## Product + Platform Architecture & Technical Design Specification

**Version:** 1.0  
**Status:** Stable (Phase B.3 Complete)  
**Audience:** System Architects, Platform Engineers, Security Reviewers, Technical Evaluators  
**Host Platform:** DevSync (Cloud-Based Realtime Coding Platform)  
**Deployment Environment:** Render Cloud (Stateless Python Service)

---

## 1. Overview

The **Jarvis Sandbox Reasoning Service** is a deterministic, stateless code intelligence engine integrated into the DevSync platform. Its purpose is to perform static analysis, structural reasoning, and policy-driven risk detection on source code **without executing it**.

This system is:

- Not an AI chatbot  
- Not a code generator  
- Not a conversational assistant  

It is a **code intelligence subsystem** focused on:

- security risk detection  
- maintainability analysis  
- structural correctness  
- architectural hygiene  

The service is intentionally isolated from the Jarvis Cognitive OS to preserve strict security and ownership boundaries.

---

## 2. System Context

### 2.1 Relationship to Jarvis Core (Cognitive OS)

Jarvis Core is a private, local, stateful cognitive operating system with:

- memory  
- identity  
- goals and values  
- tool execution  
- command authority  

**Jarvis Sandbox is not Jarvis Core.**

Jarvis Sandbox:

- does not persist state  
- does not execute actions  
- does not access tools or shell  
- does not expose memory  
- does not carry identity  

Only conceptual reasoning patterns are reused.  
No runtime code, state, or authority is shared.

This separation prevents:

- privilege escalation  
- identity leakage  
- state corruption  
- remote execution risk  

---

## 3. Problem Statement & Motivation

Modern collaborative coding platforms require automated intelligence to:

- detect dangerous patterns early  
- flag security risks before execution  
- surface maintainability issues  
- enforce coding standards  
- provide deterministic, auditable feedback  

Typical industry solutions rely on:

- third-party SaaS analyzers  
- cloud-hosted LLM APIs  
- opaque black-box systems  

This introduces problems:

- source code leaves the platform  
- behavior is non-deterministic  
- rules and policy are not owned  
- reasoning cannot be audited  
- costs scale per request  

Jarvis Core already contains a sophisticated reasoning architecture but **cannot be exposed**.

The solution is a **clean-room, sandboxed reimplementation**:  
**Jarvis Sandbox Reasoning Service.**

---

## 4. Design Goals

The system is designed with the following non-negotiable constraints:

1. **Determinism**  
   Same input always produces the same output

2. **Statelessness**  
   No memory across requests

3. **Safety**  
   Zero execution capability

4. **Explainability**  
   Every finding maps to a deterministic rule or structure

5. **Extensibility**  
   New analyzers can be added without redesign

6. **Cloud Compatibility**  
   Killable, restartable, horizontally scalable

---

## 5. High-Level Architecture

# JARVIS SANDBOX REASONING SERVICE  
## Product + Platform Architecture & Technical Design Specification

**Version:** 1.0  
**Status:** Stable (Phase B.3 Complete)  
**Audience:** System Architects, Platform Engineers, Security Reviewers, Technical Evaluators  
**Host Platform:** DevSync (Cloud-Based Realtime Coding Platform)  
**Deployment Environment:** Render Cloud (Stateless Python Service)

---

## 1. Overview

The **Jarvis Sandbox Reasoning Service** is a deterministic, stateless code intelligence engine integrated into the DevSync platform. Its purpose is to perform static analysis, structural reasoning, and policy-driven risk detection on source code **without executing it**.

This system is:

- Not an AI chatbot  
- Not a code generator  
- Not a conversational assistant  

It is a **code intelligence subsystem** focused on:

- security risk detection  
- maintainability analysis  
- structural correctness  
- architectural hygiene  

The service is intentionally isolated from the Jarvis Cognitive OS to preserve strict security and ownership boundaries.

---

## 2. System Context

### 2.1 Relationship to Jarvis Core (Cognitive OS)

Jarvis Core is a private, local, stateful cognitive operating system with:

- memory  
- identity  
- goals and values  
- tool execution  
- command authority  

**Jarvis Sandbox is not Jarvis Core.**

Jarvis Sandbox:

- does not persist state  
- does not execute actions  
- does not access tools or shell  
- does not expose memory  
- does not carry identity  

Only conceptual reasoning patterns are reused.  
No runtime code, state, or authority is shared.

This separation prevents:

- privilege escalation  
- identity leakage  
- state corruption  
- remote execution risk  

---

## 3. Problem Statement & Motivation

Modern collaborative coding platforms require automated intelligence to:

- detect dangerous patterns early  
- flag security risks before execution  
- surface maintainability issues  
- enforce coding standards  
- provide deterministic, auditable feedback  

Typical industry solutions rely on:

- third-party SaaS analyzers  
- cloud-hosted LLM APIs  
- opaque black-box systems  

This introduces problems:

- source code leaves the platform  
- behavior is non-deterministic  
- rules and policy are not owned  
- reasoning cannot be audited  
- costs scale per request  

Jarvis Core already contains a sophisticated reasoning architecture but **cannot be exposed**.

The solution is a **clean-room, sandboxed reimplementation**:  
**Jarvis Sandbox Reasoning Service.**

---

## 4. Design Goals

The system is designed with the following non-negotiable constraints:

1. **Determinism**  
   Same input always produces the same output

2. **Statelessness**  
   No memory across requests

3. **Safety**  
   Zero execution capability

4. **Explainability**  
   Every finding maps to a deterministic rule or structure

5. **Extensibility**  
   New analyzers can be added without redesign

6. **Cloud Compatibility**  
   Killable, restartable, horizontally scalable

---

## 5. High-Level Architecture
```
DevSync UI
|
v
DevSync Backend (/api/ai/review)
|
v
Jarvis Sandbox Service (Render Cloud)
|
v
Static Analysis Engine
├── Regex Prefilter
├── AST Analyzer ← Primary Authority
├── Structural Analyzer
└── Result Normalizer
```



Jarvis Sandbox is a pure analysis backend.  
DevSync remains the editor, UI, and collaboration layer.

---

## 6. Internal Module Architecture

### 6.1 Service Transport Layer

**File:** `services/jarvis_service.py`

Responsibilities:

- HTTP request handling  
- payload validation  
- response formatting  

Endpoints:

- `GET /health`  
- `POST /review_code`  

No analysis logic exists here.

---

### 6.2 ReviewBrain (Analysis Orchestrator)

**File:** `services/review_brain.py`

Responsibilities:

- orchestrate analysis passes  
- enforce ordering rules  
- merge results  
- suppress duplicate findings  

Pipeline order:

1. Regex prefilter (limited scope)  
2. AST analyzer (authoritative)  
3. Structural analyzer  
4. Result normalization  

ReviewBrain never executes code.

---

### 6.3 Regex Prefilter

Purpose:

- detect destructive literal strings  
- fast rejection of obvious hazards  

Characteristics:

- string-based  
- non-authoritative  
- shrinking over time  

AST findings always override regex findings.

---

### 6.4 AST Analyzer (Primary Intelligence Layer)

**File:** `core/ast_analyzer.py`

Uses Python’s Abstract Syntax Tree to perform structural inspection.

Current detections:

- infinite loops (`while True` without `break`)  
- `eval` / `exec`  
- `os.system`  
- `subprocess.*`  
- file writes via `open(..., "w"/"a"/"+")`  
- bare `except` blocks  
- empty exception handlers  
- syntax errors  

Properties:

- formatting-independent  
- resilient to obfuscation  
- deterministic  
- language-aware  

AST is the primary source of truth.

---

### 6.5 Structural Analyzer

**File:** `core/structure_analyzer.py`

Focuses on maintainability and readability, not security.

Current detections:

- deep nesting  
- structural complexity warnings  

Answers:

> “Is this code readable, maintainable, and structurally sane?”

---

## 7. Detection Philosophy

Each finding includes:

- severity  
- category  
- message  
- confidence  

Rules:

- one issue produces one result  
- no duplicate reporting  
- no escalation without a concrete finding  
- AST > Regex > Heuristics  

No probabilistic output exists.

---

## 8. Security Model

The service is analysis-only.

Explicitly prohibited:

- code execution  
- shell access  
- filesystem writes  
- network calls  
- memory persistence  
- identity handling  

The service behaves as a pure function:
```
Input text → Analysis result
```

---

## 9. Deployment Architecture

### 9.1 Environment

- Render Cloud  
- stateless container deployment  
- auto-deploy on Git push  

### 9.2 Runtime Behavior

- service may sleep after inactivity  
- first request may incur cold start  
- `/health` endpoint wakes service  

No manual server management is required.

---

## 10. Integration with DevSync

DevSync responsibilities:

- editor UI  
- selection handling  
- request forwarding  
- result visualization  

Jarvis Sandbox responsibilities:

- analysis only  
- no UI  
- no state  

This separation ensures clean ownership boundaries.

---

## 11. Current Capability Summary (Phase B.3)

Implemented and verified:

- deterministic analysis  
- AST-based detection  
- structural warnings  
- duplicate suppression  
- Render deployment  
- DevSync integration  

Verified test cases:

- infinite loop detection  
- `eval` detection  
- `os.system` detection  
- bare `except` detection  
- deep nesting detection  

---

## 12. Roadmap

### Phase A — Sandboxed Reasoning Service  
**Status:** Complete

- stateless service  
- cloud deployment  
- DevSync integration  

---

### Phase B — Structural Intelligence

**B.1**  
- AST parsing  
- basic structural rules  

**B.2**  
- duplicate suppression  
- AST as authority  
- regex minimization  

**B.3**  
- nesting depth detection  
- maintainability warnings  

**B.4 (Next)**  
- cyclomatic complexity  
- large function detection  
- parameter count rules  

---

### Phase C — Semantic Intelligence

- control-flow graphs  
- data-flow analysis  
- taint tracking  
- resource leak detection  

---

### Phase D — Architectural Intelligence

- module dependency graphs  
- circular dependency detection  
- boundary enforcement  
- layered architecture rules  

---

### Phase E — Advisory Layer

- explanation endpoints  
- remediation guidance  
- refactoring advice  
- technical debt scoring  

---

### Phase F — Optional LLM Presentation Layer

- human-readable explanations only  
- no decision authority  
- no execution  
- no policy control  

---

### Phase G — Platformization

- organizations  
- policy packs  
- CI/CD integration  
- audit trails  

---

## 13. Final Positioning

This is not:

> “We added AI to our editor.”

This is:

> “We are building a deterministic, self-owned code intelligence platform.”

Comparable to:

- SonarQube  
- Snyk  
- CodeQL  
- Semgrep  

But fully deterministic, auditable, privacy-preserving, and extensible.

---

## 14. Core Philosophy

Jarvis Core is sacred.  
The Sandbox is a tool shell.

The platform owns:

- the rules  
- the policy  
- the intelligence  
- the safety  

No external AI is required.
.