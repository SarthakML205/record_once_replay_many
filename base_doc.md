# Master Project Specification: Computer-Use Automation System

## 1. Project Overview

### 1.1 Core mission

This system is a deterministic backend integration layer. It lets AI agents operate legacy, API-less banking and credit union back-office software.

Production work does not run an expensive, nondeterministic LLM on every task. The architecture is **Discover Once, Replay Many**:

| Stage | Role |
| --- | --- |
| **Discovery (LLM-in-the-loop)** | An agent drives a live UI with an observe → decide → act loop until a natural-language goal succeeds. |
| **Capability compilation** | The successful path is extracted into a typed, versioned, parameter-driven capability artifact. |
| **Deterministic replay (zero-LLM)** | Production agents pass arguments to the artifact. The replay engine runs the flow without model inference, extracts outputs, and asserts checkpoints. |
| **Human-in-the-loop (HITL) fallback** | On unexpected states, irreversible actions, or unrecoverable errors, execution pauses. A human takes the same live session, then the engine resumes. |

## 2. Target Application: React Mock Bank Portal

A dedicated stand-in web app is required so discovery and replay can be tested without third-party rate limits, terms-of-service risk, or privacy issues.

### 2.1 Scope boundary

- **Minimal surface only.** Screens, components, and error states exist solely to cover assignment requirements and edge cases.
- **No real backend or RDBMS.** A local CSV file is the read/write database.

### 2.2 Data layer

Path: `/data/members.csv`

Columns:

- `member_id`
- `first_name`
- `last_name`
- `ssn_last4`
- `account_type`
- `balance`
- `status` (`ACTIVE`, `FROZEN`, `RESTRICTED`)

Seed data must include valid members, restricted statuses, and known balances.

### 2.3 Screens

**Screen 1: Member search and lookup**

- Search input for `member_id` and a Search action.
- Results table: name, masked SSN, account type, current balance, status.
- Negative/boundary state: explicit “Record Not Found” or “No matching member found” alert for expected business outcomes.

**Screen 2: Service action and confirmation**

Example actions: Open High-Yield Savings Sub-Account, or Freeze Account.

- Multi-field input (account name, initial deposit).
- Confirmation interstitial/modal that requires explicit confirmation before execution. This is the irreversible-action / HITL pause-and-approval seam.
- Success receipt banner with a generated confirmation ID.

### 2.4 Surface hostility

Render with generic HTML (`div`, `span`, `tr`, `td`). Do not add modern `data-testid` attributes or semantic IDs. The mock should behave like legacy enterprise software where agents cannot rely on a clean DOM.

## 3. System Modules

### 3.1 LLM-driven discovery agent

- **Loop contract:** Observe → Decide → Act, bounded by `max_steps` and execution timeouts.
- **Perception:** Extract interactive candidates from the accessibility tree, visible text nodes, or visual coordinates.
- **Action primitives:** `CLICK(locator)`, `TYPE(locator, text)`, `NAVIGATE(url)`, `WAIT_FOR(checkpoint)`, `READ(locator)`.
- **Artifact synthesis:** After a successful goal run, compile the step trajectory into the capability schema.

### 3.2 Capability artifact schema

The artifact is the production capability definition.

| Section | Contents |
| --- | --- |
| **Metadata** | Unique ID, capability name, version, target route pattern |
| **Input contract** | Typed runner arguments (e.g. `member_id: string`, `initial_deposit: number`) |
| **Output contract** | Typed values extracted on completion (e.g. `savings_balance: string`, `confirmation_id: string`) |
| **Action steps** | Ordered actions with robust locators: primary selector, semantic role/name fallback, visual anchor |
| **Checkpoints** | Conditions that must be true to confirm a state transition |
| **Outcome taxonomy** | Rules mapping UI states to expected business outcomes vs failures |

### 3.3 Deterministic replay engine

- **Execution contract:** Run the capability artifact end-to-end with zero LLM API calls.
- **Variable substitution:** Inject runtime arguments into typed actions (e.g. `${input.member_id}`).

**Tri-tier error and outcome classification**

| Class | Meaning |
| --- | --- |
| **Expected business outcomes** | Normal operational branches (e.g. “Member Not Found”, “Account Suspended”). Return structured result payloads, not crashes. |
| **Recoverable conditions** | Transient delays or dismissible notifications. Handle with wait/retry policies. |
| **Hard failures** | Missing target elements or unfulfilled checkpoints. Terminate with structured debug details (step ID, expected vs observed state). |

### 3.4 HITL session escalation

**Triggers:** loop stall (repeated actions), irrecoverable selector failure, or a flagged irreversible/risky action.

**Live session hand-off**

- Pause automation without closing the active browser context.
- Emit an escalation incident packet: capability ID, current step, pause reason, current screenshot.
- Operator control seam: local CLI interrupt/signal server or a minimal web operator overlay so a human can use the open browser window.
- Resume: the operator triggers Resume; the engine captures post-action state, updates context, and completes or verifies remaining steps.

### 3.5 Safety, policy, and data privacy

- **Allowlists:** Strict URL/route regex and action-type allowlists. Block out-of-scope navigation and unauthorized system calls.
- **Action classification:** `SAFE` / `REVERSIBLE` (search, read, click tab) vs `RISKY` / `IRREVERSIBLE` (submit form, delete, transfer).
- **Redaction:** Mask SSN, credit card numbers, and passwords in execution logs, artifacts, and persisted traces.

## 4. Deliverables and Repository Layout

```text
├── README.md                  # Setup, keys, and exact demo commands
├── REPORT.md                  # 1–3 page design write-up with 7 mandatory sections
├── evidence/                  # Run evidence (artifacts, logs, captures)
│   ├── capability_artifact.json
│   ├── discovery_run.log
│   ├── replay_success.log
│   └── replay_business_outcome_or_failure.log
├── src/                       # Automation system source
│   ├── agent/                 # LLM discovery loop and prompts
│   ├── engine/                # Deterministic replay runner and locator resolvers
│   ├── hitl/                  # Live-session pause, handoff, and resume
│   ├── guardrails/            # Allowlists, action classification, PII redaction
│   └── schemas/               # Artifact, step, and result schemas
└── target-app/                # Minimal React + CSV bank portal
    ├── data/members.csv       # Seed database
    └── src/                   # Bare-bones lookup and service screens
```

### 4.1 REPORT.md headings (exact)

The report must use these seven headings:

```markdown
## 1. Architecture (System components, boundaries, and fundamental design decisions).
## 2. Artifact schema (Schema structure, typing, parameterization, and locator robustness logic).
## 3. Determinism & error handling (Locator strategies, timeouts, and business outcome vs. failure taxonomy).
## 4. Heterogeneity & multi-tenant (Abstracting from web DOM to desktop/legacy UIs; tenant parameterization and drift management).
## 5. Escalation & handoff (Detection of stuck states, live browser session handover, resume seams).
## 6. Safety (Configurable allowlists, safe vs. risky action handling, PII/credential sanitization).
## 7. Cuts (Deliberate trade-offs, omitted infrastructure, and production roadmap).
```

## 5. Constraints (Non-Negotiable)

| Constraint | Rule |
| --- | --- |
| **Discovery authenticity** | Discovery runs against the live app with a real LLM. Full trace logs and artifacts are committed under `/evidence/`. |
| **No LLM in replay** | Standard replay is strictly deterministic. An LLM call on that path violates the core requirement. |
| **Session preservation** | HITL escalation must not spawn a new browser session. It keeps the exact runtime state of the active automation session. |
| **Error classification** | Do not crash or return a generic error on expected app results (e.g. “Member Not Found”). Those are valid business results. |
| **Infrastructure simplicity** | No premature Kafka, Redis queues, or multi-container orchestration. Depth goes into the core loop, artifact schema, locator strategy, and handoff seam. |

## 6. Execution Roadmap

| Phase | Milestone | Deliverable / verification |
| --- | --- | --- |
| **1** | Target app scaffolding | React app with `members.csv`; Search, Detail, and Action screens; unsemantic elements |
| **2** | Discovery agent loop | Agent drives the UI, completes the goal, compiles `capability_artifact.json` |
| **3** | Deterministic replay engine | Runner executes the artifact with dynamic parameters, locators, and outputs; zero LLM calls |
| **4** | Robustness, taxonomy, HITL | Outcome vs failure classification, allowlist filtering, live session pause/resume |
| **5** | Evidence and documentation | Logs in `/evidence/`, `README.md`, `REPORT.md` with all 7 required headings |
