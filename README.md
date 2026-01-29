# **JARVIS SANDBOX SERVICE**

## **Product \+ Platform Architecture & Design Specification**

**Version:** 1.0 (Draft)  
 **Status:** Canonical Engineering Design Document  
 **Audience:** System Architects, Product Engineers, Security Reviewers, Technical Evaluators  
---


## **1\. Introduction and Scope**

This document specifies the architecture, security model, implementation strategy, and evolution plan for the **Jarvis Sandbox Service**, a sandboxed AI reasoning microservice integrated into **DevSync**, a cloud-based real-time collaborative coding platform.  
The Jarvis Sandbox Service is **not** the Jarvis Cognitive OS itself. It is a **separately deployed, strictly sandboxed, stateless reasoning service** that exposes a limited, read-only subset of analytical capabilities derived from the Jarvis architecture.  
The purpose of this document is to:

* Formally describe the **problem being solved**

* Define the **system boundaries**

* Explain the **security and isolation model**

* Specify the **high-level architecture**

* Establish the **design philosophy and invariants**

* Provide a foundation for future extensions and scaling

This document intentionally treats the Jarvis Sandbox Service as a **product-grade platform component**, not as a demo script or experimental prototype.

## **2\. Problem Statement and Motivation**

Modern cloud-based coding platforms such as DevSync require **automated code intelligence** capabilities to assist users with:

* Detecting security vulnerabilities

* Identifying dangerous or destructive code patterns

* Highlighting maintainability and long-term risk

* Enforcing coding standards and organizational rules

* Providing early warnings before code is executed or merged

Typical industry solutions rely on:

* Cloud-hosted LLM APIs

* Third-party SaaS analyzers

* Black-box services with opaque reasoning

* External data transmission of source code

This introduces several fundamental problems:

1. **Trust boundary violation:** Source code must be sent to external systems.

2. **Loss of control:** The reasoning system is not owned or inspectable.

3. **Security and privacy risk:** Proprietary code leaves the platform.

4. **Lack of determinism:** LLM outputs are non-deterministic and hard to govern.

5. **No deep policy integration:** External tools cannot encode platform-specific values or rules.

At the same time, the Jarvis project already exists as a **personal cognitive operating system** with:

* A multi-layer reasoning architecture

* A policy and ethics system

* A risk and scoring engine

* A security guard and gating mechanism

However, **Jarvis Core itself is not deployable**:

* It is stateful

* It has memory

* It has identity and owner authentication

* It has tool access and action execution

* It is safety-critical and not meant to be exposed

Therefore, the core design challenge is:  
How do we reuse the *reasoning intelligence* of Jarvis **without exposing Jarvis itself**?  
The answer is the **Jarvis Sandbox Service**.

## 



## **3\. Conceptual System Decomposition**

The overall ecosystem is deliberately split into **two different AI systems with two different threat models**.  
They are related by architecture, but **never co-deployed**.

### **3.1 Jarvis Core (Cognitive OS)**

Jarvis Core is a **personal cognitive operating system**.  
It is designed to act as a persistent, stateful, owner-locked intelligence system.  
Key properties:

* Runs locally

* Stateful

* Has memory, goals, values, and identity

* Has tool access and can execute actions

* Owner-authenticated and locked

* Persistent across sessions

* Safety-critical

* Never exposed to the network

* Never deployed as a service

* Never shared

Representative components include:

* jarvis.py

* system/judge.py

* system/score\_engine.py

* system/ethics.py

* system/guard.py

* memory/, identity, control plane, state machine, etc.

This system is **not a product API**. It is a **private AI OS**.

### **3.2 Jarvis Sandbox Service (Product Microservice)**

The Jarvis Sandbox Service is a **separate program** with a completely different design goal:  
Expose a **read-only, stateless, killable, sandboxed reasoning engine** for use inside DevSync.  
Key properties:

* Stateless

* No memory

* No identity

* No tools

* No shell access

* No command execution

* No mutation

* No side effects

* Killable and restartable at any time

* Deterministic

* Exposes analysis only

This service is **not Jarvis**.  
It is:  
A sandboxed reasoning engine built using a **re-implemented, stateless subset** of Jarvis’s reasoning architecture.  
This separation is **not an implementation detail**.  
 It is the **core security boundary of the entire system**.

## **4\. Architectural Rationale**

The decision to split the system into:

* A **private cognitive OS** (Jarvis Core)

* A **public sandboxed analysis service** (Jarvis Sandbox)

is driven by the following constraints:

1. Jarvis Core must never be remotely accessible.

2. Jarvis Core must never be callable as an API.

3. Jarvis Core must never accept untrusted input from the network.

4. DevSync requires a network-accessible service.

5. DevSync must not gain access to:

   * Memory

   * Identity

   * Tools

   * Execution

   * Internal state

Therefore:

* The sandbox service **does not import** Jarvis Core.

* The sandbox service **does not share state** with Jarvis Core.

* The sandbox service **does not have the same codebase**.

Instead:

* A **clean-room, stateless reimplementation** of the reasoning layers is created under core/.

* These modules implement:

  * Ethics evaluation

  * Security gating

  * Risk scoring

  * Final decision logic

* All of them operate on **text only**.

This mirrors the Iron Man architecture:  
One central intelligence, multiple shells, strict isolation between shells and the core.

## **5\. High-Level System Architecture**

At runtime, the system is composed of three layers:

DevSync UI  
    |  
    v  
DevSync Backend (/api/ai/review)  
    |  
    v  
Jarvis Sandbox Service (Render)  
    |  
    v  
Sandbox Reasoning Core (stateless)

### 

### 

### 

### **5.1 Request Flow**

1. A user in DevSync selects a file or code fragment.

DevSync backend sends a POST request to the sandbox service:

 POST /review\_code

2.   
3. The sandbox service:

   * Wraps the code in an analysis request

   * Runs static pattern checks

   * Runs the scoring engine

   * Runs the ethics layer

   * Runs the security guard

   * Produces a normalized result list

4. DevSync displays the results in the UI.

### 

### 

### **5.2 Internal Structure of the Sandbox Service**

services/  
  jarvis\_service.py   \-\> HTTP transport layer  
  review\_brain.py     \-\> Orchestration layer

core/  
  ethics.py           \-\> Ethical gating (stateless)  
  guard.py            \-\> Security gating (stateless)  
  score\_engine.py     \-\> Risk scoring (stateless)  
  judge.py            \-\> Final decision pipeline

The **ReviewBrain** component acts as a pure orchestrator:

* It does not store state

* It does not execute code

* It does not call tools

* It only coordinates analysis passes and formats output

## **6\. Security Model and Trust Boundaries**

The Jarvis Sandbox Service is designed under a **deny-by-default security philosophy**.  
The system assumes:

* All input is untrusted.

* The service is internet-accessible.

* The service may be probed, fuzzed, spammed, or crashed.

* The service must remain safe even if fully compromised.

### **6.1 Non-Negotiable Invariants**

The sandbox service MUST:

* Never store memory

* Never load or write persistent state

* Never access the filesystem except for its own code

* Never execute shell commands

* Never execute user code

* Never load plugins

* Never call external tools

* Never mutate any global state

* Never communicate with Jarvis Core

The sandbox service is defined as:  
A pure function: Input text → Analysis result

**6.2 Trust Boundary Diagram**

**![][image1]**

There is no runtime path from the sandbox service to Jarvis Core.  
They are separate programs, separate deployments, separate threat models.

## **7\. Threat Model**

### 7.1 Assumed Threats

The system is designed assuming:

* Attackers can send arbitrary payloads.

* Attackers can attempt prompt injection.

* Attackers can attempt denial-of-service.

* Attackers can attempt to crash the process.

* Attackers can attempt to trigger edge cases in parsers or logic.

### 7.2 Explicitly Out of Scope

The sandbox service:

* Does not execute user code

* Does not evaluate ASTs dynamically

* Does not load plugins

* Does not interpret code

* Does not call any external runtime

Therefore:

* Remote Code Execution (RCE) via user input is structurally impossible.

* Data exfiltration is structurally impossible (no secrets exist).

* Privilege escalation is structurally impossible (no privileges exist).

### 7.3 Failure Philosophy

If the sandbox service:

* Crashes → it restarts

* Is overloaded → requests fail

* Is killed → it is restarted

* Returns wrong analysis → only analysis quality is affected

No persistent damage is possible.

## **8\. API Contract**

The Jarvis Sandbox Service intentionally exposes a minimal API surface.

### 8.1 Endpoints

`GET  /health`  
`POST /review_code`

No other endpoints exist.

### **8.2 GET /health**

Purpose: Liveness and warm-up check.  
Response:  
`{`  
  `"status": "ok",`  
  `"service": "jarvis"`  
`}`

This endpoint is also used on Render to wake the service from sleep.

### **8.3 POST /review\_code**

Purpose: Submit code for analysis.  
Request schema:  
`{`  
  `"file": "string",`  
  `"language": "string",`  
  `"code": "string",`  
  `"scope": "file | selection",`  
  `"range": { "startLine": number, "endLine": number } | null`  
`}`

Response schema:  
`{`  
  `"success": true,`  
  `"results": [`  
    `{`  
   `   "severity": "error | warning | info",`  
      `"category": "security | maintainability | style | performance | bug",`  
      `"message": "string",`  
      `"confidence": "low | medium | high"`  
    `}`  
  `]`  
`}`

The API is:

* Stateless

* Idempotent

* Side-effect free

## **9\. Internal Decision Pipeline**

The analysis pipeline is layered and ordered:  
`Input Code`  
    `|`  
    `v`  
`Static Pattern Scanner`  
    `|`  
    `v`  
`Score Engine (Risk Scoring)`  
    `|`  
    `v`  
`Ethics Layer (Hard Rules)`  
    `|`  
    `v`  
`Security Guard (Dangerous Intent)`  
    `|`  
    `v`  
`Judge (Final Decision)`  
    `|`  
    `v`  
`Normalized Results`

### 9.1 Design Rationale

* Fast checks first (string patterns)

* Deeper reasoning later

* Multiple independent veto layers

* No single layer is trusted alone

## **10\. Deployment Architecture**

### 10.1 Current Deployment (Demo / Production Preview)

The sandbox is deployed on Render as a public service:  
`https://jarvis-sandbox.onrender.com`

Health check:  
`GET /health`

Service start command:  
`uvicorn services.jarvis_service:app --host 0.0.0.0 --port 3333`

**10.2 Deployment Diagram**

**![][image2]**

### **10.3 Free-Tier Sleep Behavior**

On Render free tier:

* The service may spin down after inactivity.

* First request may take 20–50 seconds.

* The `/health` endpoint is used to warm it up before demos.

## **11\. Integration into DevSync**

### **11.1 Logical Flow**

`User selects code in editor`  
        `|`  
        `v`  
`DevSync UI`  
        `|`  
        `v`  
`/api/ai/review (Next.js backend)`  
        `|`  
        `v`  
`Jarvis Sandbox /review_code`  
        `|`  
        `v`  
`Results returned and rendered`

DevSync does not know:

* How the analysis is implemented

* What rules exist internally

* What engine is used

It only consumes the API.

## **12\. Lifecycle and Failure Semantics**

* The service is stateless.

* Any instance can be killed at any time.

* No recovery is needed.

* No migration is needed.

* No data loss is possible.

This makes the service:

* Horizontally scalable

* Cacheable

* Replaceable

* Versionable

## **13\. Current Functional Capabilities**

As implemented today, the sandbox performs:

* Static dangerous pattern detection:

  * `eval`

  * `exec`

  * `rm -rf`

  * `pickle.loads`

  * `os.system`

* Risk scoring based on heuristics

* Policy-based blocking via judge

* Normalized result reporting

## **14\. Planned Evolution**

The architecture is intentionally designed to support:

* AST-based analysis

* Language-specific analyzers

* Rule packs

* Organization policy layers

* `/explain` endpoint

* Auto-fix suggestions

* Hybrid local LLM (Ollama) reasoning

* Multi-engine ensembles

## **15\. Strategic Positioning**

This system is:

* Not a chatbot

* Not a code generator

* Not a Copilot replacement

It is:

A code intelligence, policy, and risk analysis engine.

Comparable in category to:

* SonarQube

* Snyk

* Semgrep

* ESLint (on steroids)

But with a custom reasoning core.

## **16\. Core Philosophy (Final)**

Jarvis Core is sacred.  
The Sandbox is a tool shell.

The platform owns the reasoning.  
The platform owns the rules.  
The platform owns the policy.

No external AI is required.

# **17\. Concrete Behavioral Examples (Current System)**

This section documents exactly what the Jarvis Sandbox Service does today, using real input → output examples. This is critical for reviewers to understand that the system is not a mock, not a stub, and not a demo illusion.

## 

## **17.1 Example: Dangerous Dynamic Execution**

### Input

`user_code = "print('Hello')"`  
`eval(user_code)`

Request payload:  
`{`  
  `"file": "test.py",`  
  `"language": "python",`  
  `"code": "user_code = \"print('Hello')\"\neval(user_code)",`  
  `"scope": "file",`  
  `"range": null`  
`}`

### Internal Reasoning

* Static scanner detects: `eval(`

* Score engine applies heavy negative weight for arbitrary code execution

* Ethics layer flags destructive capability

* Judge blocks as high-risk

### Output

`{`  
  `"success": true,`  
  `"results": [`  
    `{`  
      `"severity": "error",`  
      `"category": "security",`  
      `"message": "Using eval() allows arbitrary code execution.",`  
      `"confidence": "high"`  
    `},`  
   ` {`  
      `"severity": "warning",`  
      `"category": "security",`  
      `"message": "Catastrophic long-term risk.",`  
      `"confidence": "medium"`  
    `}`  
  `]`  
`}`

## **17.2 Example: Destructive Shell Command**

### Input

`import os`  
`os.system("rm -rf /")`

### Internal Reasoning

* Static scanner detects: `os.system` and `rm -rf`

* Score engine assigns extreme negative score

* Guard layer blocks immediately

### Output

`{`  
  `"success": true,`  
  `"results": [`  
    `{`  
      `"severity": "error",`  
      `"category": "security",`  
      `"message": "Executing shell commands via os.system is dangerous.",`  
      `"confidence": "high"`  
    `},`  
    `{`  
      `"severity": "error",`  
      `"category": "security",`  
      `"message": "This command deletes files recursively and is extremely dangerous.",`  
      `"confidence": "high"`  
    `}`  
  `]`  
`}`

## **17.3 Example: Normal Code**

### Input

`def add(a, b):`  
    `return a + b`

### Internal Reasoning

* No static danger patterns

* Score engine produces neutral score

* Judge allows

### Output

`{`  
  `"success": true,`  
  `"results": [`  
    `{`  
      `"severity": "info",`  
      `"category": "style",`  
      `"message": "No critical issues detected by Jarvis core or static analyzers.",`  
      `"confidence": "low"`  
    `}`  
  `]`  
`}`

## **17.4 Interpretation**

At present, the system behaves as:

* A security-first reviewer

* A risk detector

* A policy engine

It does not attempt to rewrite code, generate code, or act as a conversational assistant.

# 

# **18\. Comparison with Previous OpenRouter-Based Pipeline**

This section explains why the previous AI integration was replaced and what architectural advantages the new system provides.

## **18.1 Old Architecture (OpenRouter / LLM-as-a-Service)**

`DevSync`  
   `|`  
   `v`  
`/api/ai/review`  
   `|`  
   `v`  
`OpenRouter API`  
   `|`  
   `v`  
`Remote LLM (Black Box)`

### Properties

* Requires API keys

* Sends user code to third-party servers

* Non-deterministic output

* No control over rules

* No control over policy

* No explainable decision path

* Output can break format

* Cost per request

* Subject to rate limits

* Subject to provider downtime

### Engineering Reality

* The system is not really “yours”

* You are renting intelligence

* You cannot certify behavior

* You cannot guarantee safety

* You cannot build real product differentiation

## **18.2 New Architecture (Jarvis Sandbox)**

`DevSync`  
   `|`  
   `v`  
`/api/ai/review`  
   `|`  
   `v`  
`Jarvis Sandbox Service`  
   `|`  
   `v`  
`Your own reasoning core`

### Properties

* No API keys

* No third-party calls

* No data leaves your infrastructure

* Deterministic and reproducible

* Fully auditable logic

* Fully controllable rules

* Fully versioned behavior

* Zero marginal cost per request

* Can run offline

* Can be certified

## **18.3 Strategic Difference**

Old system:  
“We call an AI.”  
New system:  
“We own an intelligence engine.”  
This is the difference between:

* A demo project

* And a real product platform

# **19\. Roadmap: From Review Engine to Full AI Coding Platform**

This section explains how this architecture becomes a full AI coding platform over time, without ever breaking the security or architectural principles.

## **19.1 Phase 1 — Intelligence Deepening** 

* AST-based parsing

* Language-specific analyzers

* Rule packs

* Control-flow analysis

* Data-flow analysis

* Taint analysis

* Architecture linting

* Organization policy engines

At this point, the system becomes comparable to:

* Semgrep

* SonarQube

* Snyk

* Coverity

But fully custom.

## **19.2 Phase 2 — Explainability Layer**

Add:  
`POST /explain`

Which returns:

* Why a rule triggered

* What risk model fired

* What logic path was taken

* What the engine “thought”

This makes the system:

* Auditable

* Teachable

* Trustworthy

## **19.3 Phase 3 — Auto-Fix Layer**

Add:

* Deterministic refactoring rules

* Safe transformations

* Style normalization

* Security patch suggestions

Still:

* No LLM required

* Fully rule-based

* Fully controlled

## **19.4 Phase 4 — Hybrid LLM Reasoning (Optional)**

Only at this point:

* Add local LLM (Ollama)

* Use it for:

  * Explanations

  * Suggestions

  * Refactoring drafts

* Never for:

  * Final decisions

  * Policy enforcement

  * Safety gating

The LLM becomes:  
A consultant, not the authority.

## **19.5 Final Architecture Vision**

`DevSync`  
   `|`  
   `v`  
`Policy & Analysis Engine (Jarvis Sandbox++)`  
   `|`  
   `+--> Static Analyzers`  
   `|`  
   `+--> Rule Engines`  
   `|`  
   `+--> Risk Models`  
   `|`  
   `+--> (Optional) LLM Advisor`

The platform owns:

* The rules

* The policy

* The intelligence

* The safety

# **20\. Final Positioning Statement**

This is not:  
“We added AI to our editor.”

This is:  
“We are building our own code intelligence platform.”

[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,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>
