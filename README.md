# WISDOM AI — Deterministic Code Intelligence Engine
## Product + Platform Architecture & Technical Design Specification


**Version:** 2.0 (Phase H Complete)<br>
**Status:** Enterprise-Grade Deterministic Engine<br>
**Audience:** System Architects, Platform Engineers, Security Reviewers, Technical Evaluators<br>
**Deployment:** Render Cloud (Stateless Microservice)<br>
**Author:** Alfred Jackson I

---

# 1. Overview

**WISDOM AI** is a deterministic code intelligence engine designed to analyze source code for:

- security risks
- structural issues
- maintainability problems
- policy violations

The system performs static analysis and semantic reasoning without executing code.

This is not a chatbot.  
This is not a code generator.  
This is not a wrapper over ChatGPT.

It is a **deterministic static code intelligence engine**.

---

# 2. Academic Explanation of the AI Component

The system performs deterministic static code analysis combined with an optional natural-language explanation layer to assist developers in understanding code quality, security, and maintainability issues.

The core system is deterministic and rule-based, built using static code analysis techniques such as:

- AST parsing
- control-flow analysis
- data-flow tracking
- structural analysis
- policy evaluation

AI is used only as an optional explanation layer that converts verified analysis results into human-readable review feedback.

This ensures reliability, reproducibility, and prevents hallucinations while still providing an intelligent developer experience.

Approximately:

- 80–90% deterministic static analysis
- 10–20% optional AI explanation

The AI does not decide correctness.
The AI does not enforce policy.
The AI does not generate findings.

---

# 3. Core Design Principles

1. Deterministic output for identical input
2. Stateless architecture
3. Zero code execution
4. No memory persistence
5. Cryptographically enforced policy
6. Organization-isolated configuration
7. Enterprise-safe deployment

---

# 4. System Architecture

```
Client / DevSync UI
        |
        v
HTTP API (FastAPI)
        |
        v
WISDOM AI Sandbox Engine
        |
        ├── AST Analyzer
        ├── Structural Analyzer
        ├── Semantic Engine
        ├── Policy Engine
        ├── Audit Logger
        ├── Usage Tracker
        └── Rate Limiter
```

The service behaves as a pure function:

```
Input code → deterministic analysis → structured findings
```

---

# 5. Intelligence Layers

## 5.1 Structural Intelligence

- AST parsing
- naming checks
- unused imports
- complexity warnings
- code hygiene

## 5.2 Semantic Intelligence

- control flow analysis
- data flow tracking
- taint propagation
- resource misuse detection
- unreachable code detection

## 5.3 Policy Engine

Deterministic enforcement:

- error count
- warning thresholds
- org-specific policy
- CI pass/fail decision

## 5.4 Optional AI Explanation Layer

Used only to translate deterministic findings into readable explanations.

Cannot:
- add findings
- modify results
- override policy

---

# 6. Security Architecture

## 6.1 Cryptographic Policy Signing

Each org policy is RSA signed.
Server verifies signature before loading.

Prevents:
- tampering
- unauthorized rule changes
- malicious config injection

## 6.2 API Key Authentication

Every request must include:

```
x-api-key: <org_key>
```

Server resolves:
- organization identity
- policy
- usage tracking
- rate limits

## 6.3 Audit Logging

Every scan produces structured audit event:

```
{"event":"review_completed","org":"devsync",...}
```

Tracks:
- org
- file
- issues
- policy result
- processing time

## 6.4 Usage Tracking

Per-org scan tracking.
Stored as JSON (no DB required).

## 6.5 Rate Limiting

Per-org daily limits enforced.
Example:

```
100 scans/day
```

Blocks abuse and protects system.

---

# 7. Phase Completion Status

## Phase A — Foundation
- Stateless engine
- Cloud deploy
- HTTP API

## Phase B — Structural Intelligence
- AST analysis
- rule engine
- deduplication

## Phase C — Semantic Intelligence
- CFG
- DFG
- taint tracking
- resource analysis

## Phase D — Architectural Intelligence
- module hygiene
- mixed concerns
- god module detection

## Phase E — Advisory Intelligence
- deterministic explanations
- remediation guidance

## Phase F — AI Presentation Layer
- explanation-only LLM
- no decision authority

## Phase G — Platformization
- unified schema
- SARIF export
- autofix suggestions
- policy engine

## Phase H — Enterprise Hardening (COMPLETE)
- signed policies
- org isolation
- tamper verification
- audit logging
- usage tracking
- API authentication
- rate limiting

System is now enterprise-grade.

---

# 8. Deployment & Live Service Testing

Base URL:
https://wisdom-ai-fn24.onrender.com

## Health Check (wake server)
GET
https://wisdom-ai-fn24.onrender.com.com/health

## Main Review Endpoint
POST
https://wisdom-ai-fn24.onrender.com.com/review

Headers:
```
x-api-key: devsync_live_abc123
Content-Type: application/json
```

Body:
```
{
  "file": "test.py",
  "language": "python",
  "code": "print('hello world')",
  "scope": "file",
  "policy": {
    "org": "devsync"
  }
}
```

## Schema Endpoint
GET
https://wisdom-ai-fn24.onrender.com/review/schema

## SARIF Export
POST
https://wisdom-ai-fn24.onrender.com/review/sarif

---

# 9. Local Development

Run locally:
```
uvicorn services.wisdom_service:app --reload --port 8000
```

---

# 10. Policy Signing Rule (Critical)

If editing:
```
core/org_policies/devsync.json
```
You MUST run:
```
python core/security/sign_policy.py
```
before deploy.

Otherwise server will reject policy.

---

# 11. Final Positioning

WISDOM AI is a deterministic code intelligence engine comparable to:

- SonarQube core
- Semgrep engine
- CodeQL static analysis

But:
- self-owned
- deterministic
- auditable
- secure

Built as an enterprise-grade analysis engine, not a demo project.

