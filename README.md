# qe-agentic-capstone

**Applied AI Specialist — Quality Engineering (QES) Capstone**

![Badge](https://img.shields.io/badge/Track-Applied%20AI%20Specialist%20%E2%80%94%20QE-052FAD)
![Platforms](https://img.shields.io/badge/Platforms-IBM%20Bob%20%2B%20IBM%20ICA-1f883d)
![Language](https://img.shields.io/badge/Language-Java%2021-orange)
![Workflows](https://img.shields.io/badge/Agentic%20Workflows-14-blue)
![Pipeline](https://img.shields.io/badge/Pipeline-12%20Agent--Gated%20Stages-yellow)

> **What this repo contains:** two production-style multi-agent QE solutions — a **shift-left test engineering factory** (IBM Bob, Solution A) and a **quality insights & resilience command centre** (IBM ICA, Solution B) — sharing one MCP-exposed QE knowledge spine, both wired into a 12-stage GitHub Actions pipeline that gates every pull request on agent-produced quality evidence.

---

## The Ask — Badge Requirement

From *AO Practice — Forward Deployed Unit Path V0.6*, slide 5 (QE column):

> "Build and demo at least **two multi-agentic QES agentic solutions** and **integrate with CICD pipeline** using any one or more of the AI platforms: IBM ICA, IBM Bob, watsonX Orchestrate, Claude Code, AWS Kiro, GitHub Copilot, M365 Copilot, Copilot Studio."

All **14 QE workflows** listed on that slide are covered here.  
Platforms chosen: **IBM Bob** (Solution A) + **IBM ICA** (Solution B).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              QE Knowledge Spine — ICA Context Studio             │
│  QE Test Asset Schema (9 entities · 13 relationships · 3 cycles) │
│  QE Industry Context (8 sources · vector index + knowledge graph)│
│                 ↓ exposed via MCP ContextForge                   │
│         context-broker-vector-query                              │
│         context-broker-graph-query                               │
│         context-broker-get-context-metadata                      │
│         context-broker-get-context-schema                        │
└───────────────────┬─────────────────────┬───────────────────────┘
                    │                     │
          ┌─────────▼──────┐    ┌─────────▼──────────────┐
          │  SOLUTION A    │    │      SOLUTION B         │
          │  IBM Bob       │    │      IBM ICA            │
          │  (authoring)   │    │  (runtime / CI-callable)│
          └────────────────┘    └────────────────────────┘
                    │                     │
                    └──────────┬──────────┘
                               │
              ┌────────────────▼─────────────────┐
              │   GitHub Actions — 12-Stage       │
              │   Agent-Gated CI/CD Pipeline      │
              └──────────────────────────────────┘
```

**Core design decision:** Bob is an agentic IDE that authors assets on a QE's desktop — it cannot be called by a pipeline. ICA exposes a Langflow workflow as an HTTP/MCP endpoint that CI *can* call. So Solution A owns *asset creation* and Solution B owns *runtime judgement*. The context is shared so neither solution can disagree about standards, risk or defect history.

**Architectural rule:** Agents explain. Scripts enforce. The deterministic Python scripts in `assets/ci/` compare numbers to thresholds and set the exit code. The pipeline gates correctly even if the ICA agent is unavailable — only the explanation is lost.

---

## Solution A — QE ShiftLeft Factory (IBM Bob)

**Question it answers:** *Do we have the right tests, and do they exist as code?*

| | |
|---|---|
| **Platform** | IBM Bob (agentic IDE) |
| **When it runs** | Authoring time, on the engineer's desktop |
| **Agents** | 1 Supervisor + 9 sub-agents |
| **Output** | Java 21 test assets — cases, BDD feature files, test data, Selenium/Playwright/REST Assured scripts |
| **Workflows** | WF02, WF03, WF04, WF05, WF06, WF07, WF10 |
| **Key file** | `AGENTS.md` at repo root — Bob loads this at every session start |

### Agent Team (Solution A)

| Agent | Workflow | Responsibility |
|---|---|---|
| QEShiftLeftSupervisor | — | Routes and sequences; enforces role isolation |
| IndustryContextAgent | WF01 | Domain briefing before any design starts |
| RequirementQualityAgent | WF02 | Scores requirements 0–100; TESTABLE / AMBIGUOUS / UNTESTABLE per criterion |
| TestCaseDesignAgent | WF02 | Designs cases per authoring standard; mandatory negative + boundary cases |
| TestOptimizationAgent | WF03 | Selects minimum subset; must never de-select a P1 |
| BDDAuthoringAgent | WF04 | Produces `.feature` files with `@tc-` and `@risk-` tags |
| TestDataAgent | WF05 | Generates seed SQL / Datafaker builders + validation query + teardown |
| UIAutomationAgent | WF06 | Selenium 4 + Playwright Java; Page Object Model; explicit waits only |
| APIAutomationAgent | WF07 | REST Assured asserting status + body + JSON schema |
| MigrationAgent | WF10 | Migrates legacy automation with inventory + behavioural-equivalence notes |

### WF02 Requirement Quality Results (live evidence)

| Requirement | Initial Score | Final Score | Verdict |
|---|---|---|---|
| QEC-101 — Fund transfer (ParaBank) | 82 | **82** | APPROVE WITH REWRITES |
| QEC-103 — Loan decision (ParaBank) | 18 | **78** | REWRITTEN — PASS |
| QEC-105 — Shopper checkout (SauceDemo) | 86 | **86** | APPROVE |
| QEC-113 — Checkout WCAG 2.2 AA (SauceDemo) | 88 | **88** | APPROVE |
| QEC-115 — Resilience tolerance (PetClinic) | 15 | **92** | REWRITTEN — PASS |
| QEC-117 — Basket persistence (SauceDemo) | 12 | **74** | REWRITTEN — PASS |
| QEC-118 — Transfer idempotency (ParaBank) | 92 | **92** | APPROVE |
| **Mean** | — | **84.6** | **NFR-001 PASS** (threshold ≥ 70) |

NFR-002: **0 UNTESTABLE** criteria after rewrites. Gate PASS.  
**17 test cases generated:** QEC-T301 → QEC-T317 (13 × P1, 4 × P2).

---

## Solution B — QE Insights & Resilience (IBM ICA)

**Question it answers:** *What is the state of quality, and may we ship?*

| | |
|---|---|
| **Platform** | IBM ICA — Context Studio, Agent & Assistant Studio, Langflow |
| **When it runs** | Runtime — callable from CI/CD as an HTTP/MCP endpoint |
| **Agents** | 1 Supervisor + 7 sub-agents |
| **Output** | Verdicts — defect triage, risk forecasts, gate decisions |
| **Workflows** | WF08, WF09, WF11, WF12, WF13, WF14 |
| **Key file** | `evidence/solutionB/orchestration.yaml` — exported from ICA |

### ICA Components Used

| Component | Role |
|---|---|
| **Context Studio** | Hosts 8-source QE knowledge base (vector + graph indexed); exposes MCP tools to both Bob and ICA agents |
| **Agent & Assistant Studio** | Generated 8-agent LangGraph orchestration (Supervisor pattern) from `assets/prompts/solutionB_orchestration_prompt.txt` |
| **ContextForge / MCP Gateway** | Bridges context to the agentic app. Requires both `Authorization: Bearer` AND `x-api-key` headers simultaneously |
| **Langflow** | 3-node workflow: Chat Input → A2A Agent (QEInsightsSupervisor) → Chat Output. Exposed as HTTP/MCP endpoint callable by CI |
| **Control Tower** | Traces every sub-agent span with populated `context_id` — wire-level grounding proof |

### Agent Team (Solution B)

| Agent | Workflow | Critical contract |
|---|---|---|
| QEInsightsSupervisor | — | Routes quality signals to 7 specialists; owns consolidated verdict |
| DefectTriageAgent | WF08 | `ROOT_CAUSE = TEST_SCRIPT` ⇒ suite maintenance, never a product defect |
| DefectPredictionAgent | WF09 | Explainable heuristic only — must never claim fabricated confidence |
| AgenticAppTestAgent | WF11 | ≥ 6 adversarial probes; assert on invariants, never exact wording |
| PerformanceAgent | WF12 | Never invents a measurement; missing metric ⇒ gate cannot be evaluated |
| ResilienceAgent | WF13 | Refuses any experiment with no defined abort condition |
| AccessibilityAgent | WF14 | Must include what automation cannot confirm; clean scan ≠ conformance claim |
| ReleaseGateAgent | Verdict | Absent evidence = FAIL — never silently omitted, never assumed to pass |

### Solution B Build Checkpoints

| Checkpoint | Status |
|---|---|
| B1 — Agentic app created in Agent & Assistant Studio | ✅ Done |
| B2 — Context tools verified in Sandbox (`squad-payments`, 6–20% quarantine threshold retrieved) | ✅ Done |
| B3 — 8-agent LangGraph orchestration generated, status Success | ✅ Done |
| B4 — YAML audited (8 checks: `context_id` defaults, AgentPersona, `x-api-key`, no stray brackets, required fields, no orphan tools, valid agent names, all 7 sub-agents in `supervises:`) | ✅ Done |
| B5 — Langflow 3-component workflow built | ✅ Done |
| B6 — Playground test passed: 3-failure signal + JMeter result, all 7 grounding expectations met | ✅ Done |
| B7 — Workflow exposed as MCP tool; `ICA_WORKFLOW_URL` recorded | ✅ Done |
| B8 — Control Tower traces show populated `context_id` on every tool call | ✅ Done |

---

## Shared Knowledge Spine (WF01)

Both solutions are grounded in one shared context — neither can disagree about standards, the risk register, or defect history.

| Item | Value |
|---|---|
| Context ID | `ctx_151793f36ee3` |
| Context Name | QE Industry Context |
| MCP Server | `context-studio` |
| Sources ingested | 8 (all Ready) |
| Schema | 9 entities · 13 relationships · 3 lifecycles |
| MCP tools | `context-broker-vector-query` · `context-broker-graph-query` · `context-broker-get-context-metadata` · `context-broker-get-context-schema` |
| Consumed by | IBM Bob via `.bob/mcp.json` and IBM ICA via ContextForge |

**Grounding rule (NFR-A):** Every agent factual claim must be retrievable from this context. Ungrounded output is a defect in the solution, not a quirk.

---

## All 14 QE Workflows

| ID | Name | Platform | Produces |
|---|---|---|---|
| WF01 | Context-Driven Industry Workflows | Shared | Domain briefing; schema; MCP-exposed context |
| WF02 | Requirement Quality & Test Case Generation | Bob | Scored reqs; 17 test cases QEC-T301→T317 |
| WF03 | Test Optimization | Bob | Selected subset; Surefire patterns; residual risk |
| WF04 | BDD Generation | Bob | `.feature` files; step definitions |
| WF05 | Test Data Generation | Bob | `seed.sql`; Datafaker builders; validation query |
| WF06 | UI Script Generation | Bob | Selenium 4 + Playwright Java tests |
| WF07 | API Automation (REST Assured) | Bob | REST Assured tests with JSON schema assertions |
| WF08 | Defect Triage | ICA | Per-failure: severity, priority, squad, root cause |
| WF09 | Defect Prediction | ICA | Top-5 component risk ranking with retrieved signals |
| WF10 | Script Migration & Modernisation | Bob | Migrated legacy suite; inventory; equivalence notes |
| WF11 | Agentic App Testing | ICA | Determinism / groundedness / adversarial probes (≥ 6) |
| WF12 | Performance Testing | ICA | JMeter plan; p95 / error-rate / throughput evaluation |
| WF13 | Chaos / Resilience | ICA | Steady-state hypothesis; chaos journal; data-integrity assertion |
| WF14 | Accessibility Scan | ICA | axe-core report; WCAG 2.2 AA mapping; keyboard walk |

---

## CI/CD Pipeline — 12 Agent-Gated Stages

Pipeline file: [`.github/workflows/qe-agentic-pipeline.yml`](.github/workflows/qe-agentic-pipeline.yml)

### Trigger events

| Trigger | When |
|---|---|
| `pull_request` → `main` | Every PR open / update / synchronise against `main` |
| `push` → `main` | Every direct push or merge to `main` (forces full regression) |
| `schedule` `17 1 * * *` | Nightly at 01:17 UTC — resilience experiments run out of hours |
| `workflow_dispatch` | Manual trigger from the Actions tab; optional "force full regression" checkbox |

### The 12 stages

| # | Stage | Agent-driven | Blocking gate(s) |
|---|---|---|---|
| 1 | Context sync | MCP probe | Context unreachable ⇒ fail fast |
| 2 | Requirement quality gate | RequirementQualityAgent | NFR-001 mean ≥ 70, NFR-002 = 0 UNTESTABLE |
| 3 | Test design sync | TestCaseDesignAgent | — (advisory) |
| 4 | Test optimization | TestOptimizationAgent | — (selects scope; P1 never de-selected) |
| 5 | Build and unit test | — | NFR-006 coverage |
| 6 | Test data provisioning | — | NFR-024 Luhn scan = 0 |
| 7 | API automation | — | NFR-003, NFR-007 |
| 8 | BDD and UI automation | — | NFR-003, NFR-004, NFR-005 |
| 9 | Performance smoke | PerformanceAgent | NFR-008 p95 ≤ 1200 ms, NFR-009 error ≤ 1%, NFR-010 ≥ 40 rps |
| 10 | Accessibility scan | AccessibilityAgent | NFR-017, NFR-020, NFR-022 |
| 11 | Resilience experiment (nightly) | ResilienceAgent | NFR-012–015 |
| 12 | Defect triage and release gate | Triage + Prediction + ReleaseGate | NFR-023, consolidated verdict |

### CI scripts (deterministic gate enforcement)

| Script | Enforces |
|---|---|
| `assets/ci/invoke_agent.sh` | Single place CI calls an ICA agent; 3-retry logic; JSON validation |
| `assets/ci/check_jmeter_thresholds.py` | NFR-008 / 009 / 010 — exits non-zero on missing or failing JMeter results |
| `assets/ci/check_axe_thresholds.py` | NFR-017 / 018 / 020 — exits non-zero on missing or failing axe-core results |
| `assets/ci/collect_failures.py` | Normalises Surefire failure signatures for the triage agent |
| `assets/ci/build_gate_payload.py` | Joins evidence artefacts to the NFR catalogue for the release gate agent |
| `assets/ci/synthesise_wf02.py` | Fallback: generates scored WF02 report from Bob session when ICA is unreachable |

---

## Repository Layout

```
qe-agentic-capstone/
├── AGENTS.md                          ← Bob project instructions (loaded every session)
├── pom.xml                            ← Java 21 · JUnit 5 · Selenium · Playwright · REST Assured · Cucumber
├── .github/
│   └── workflows/
│       └── qe-agentic-pipeline.yml    ← 12-stage agent-gated pipeline
├── assets/
│   ├── ci/                            ← invoke_agent.sh · check_*.py · synthesise_wf02.py
│   ├── prompts/                       ← solutionA_orchestration_prompt.txt · solutionB_orchestration_prompt.txt
│   └── sample_data/                   ← 8 knowledge files ingested into QE Industry Context
│       ├── industry_domain_glossary.md
│       ├── requirements_backlog.csv
│       ├── manual_test_cases.csv
│       ├── defect_history.csv
│       ├── test_execution_history.csv
│       ├── risk_register.csv
│       ├── nfr_catalog.csv
│       └── qe_standards_and_dod.md
├── src/test/java/com/ibm/qe/
│   ├── api/                           ← REST Assured tests (WF07)
│   ├── tests/                         ← Selenium / Playwright UI tests (WF06)
│   ├── steps/                         ← Cucumber step definitions (WF04)
│   ├── runners/                       ← Cucumber runners
│   ├── pages/                         ← Page Object Model classes
│   ├── data/                          ← Datafaker test data builders (WF05)
│   ├── a11y/                          ← Accessibility test runner (WF14)
│   ├── resilience/                    ← Chaos experiment helpers (WF13)
│   └── core/                          ← Shared base classes and utilities
├── src/test/resources/
│   ├── features/                      ← Gherkin .feature files (WF04)
│   ├── schemas/                       ← JSON Schema files for contract assertions (WF07)
│   ├── testdata/                      ← seed.sql · Datafaker configs (WF05)
│   ├── jmeter/                        ← JMeter .jmx plan (WF12)
│   └── chaos/                         ← Chaos Toolkit experiment JSON (WF13)
└── evidence/
    ├── WF01/ … WF14/                  ← Per-workflow artefacts
    ├── solutionA/                     ← Bob session transcripts; grounding checks
    ├── solutionB/                     ← orchestration.yaml; ICA screenshots; Playground run
    ├── build/                         ← Maven logs; JaCoCo coverage
    ├── cicd/                          ← Green run URL; failing-gate run URL
    ├── traceability_report.md         ← req → criterion → test case → script → execution → defect
    ├── rubric_selfassessment.md       ← Self-scored rubric (target ≥ 70/100)
    └── drift_log.md                   ← Where platform UI differed from the kit instructions
```

---

## Maven Profiles

```bash
mvn -q clean verify              # full suite
mvn -q clean verify -Papi        # REST Assured API tests only          (WF07)
mvn -q clean verify -Pui         # Selenium + Playwright UI tests only  (WF06)
mvn -q clean verify -Pbdd        # Cucumber BDD runner only             (WF04)
mvn -q clean verify -Pa11y       # Accessibility suite only             (WF14)
mvn -q clean verify -Pperf       # JMeter performance run               (WF12)
mvn -q clean verify -Pselected   # Agent-selected test subset           (WF03)
```

---

## Six AI Design Elements Demonstrated

| Element | Where |
|---|---|
| **Schema / Ontology** | QE Test Asset Schema — 9 entities, 13 relationships, 3 lifecycles (WF01, ICA Context Studio) |
| **Context** | QE Industry Context — 8 knowledge sources, vector + graph indexed (WF01) |
| **MCP Server** | Context exposed as MCP; consumed by both Bob and ICA (WF01) |
| **Multi-agent Orchestration** | Supervisor pattern in both solutions; 16 sub-agents total |
| **Workflow** | Langflow workflow wrapping Solution B, exposed as an MCP tool (doc 06) |
| **Skills / Tools** | Agent-specific tool assignment; CI invoking agents as tools via `invoke_agent.sh` |

---

## Definition of Done

The capstone is complete when all ten are true and the rubric self-assessment scores **≥ 70 / 100**:

- [ ] **DoD-1** — QE Test Asset Schema published in ICA Context Studio (9 entities, 13 relationships, 3 lifecycles)
- [ ] **DoD-2** — QE Industry Context created, 8 files ingested to *Ready*, exposed as MCP
- [ ] **DoD-3** — Solution A live in IBM Bob: supervisor + 9 sub-agents, MCP-grounded
- [ ] **DoD-4** — Solution B live in IBM ICA: supervisor + 7 sub-agents, status *Success*, wrapped in Langflow and exposed as MCP tool
- [ ] **DoD-5** — All 14 workflows executed at least once with evidence committed to `evidence/WFnn/`
- [ ] **DoD-6** — Java test suite compiles and runs: `mvn -q clean verify` green against the local AUT stack
- [ ] **DoD-7** — CI/CD pipeline green end-to-end, plus one deliberately failing run proving each quality gate blocks a bad PR
- [ ] **DoD-8** — Traceability report: requirement → test case → BDD → script → execution → defect
- [ ] **DoD-9** — Recorded demo (≤ 60 min) scoring ≥ 70/100
- [ ] **DoD-10** — PR raised on personal GitHub with line manager as reviewer + completed rubric

---

## Applications Under Test

| Application | URL (local) | Used for |
|---|---|---|
| Spring PetClinic UI | `http://localhost:8080` | WF06 (Selenium/Playwright), WF08–WF09 |
| Spring PetClinic REST | `http://localhost:9966/petclinic/api` | WF07 (REST Assured), WF12 (JMeter), WF13 (Chaos) |
| SauceDemo | `https://www.saucedemo.com` | WF06 (UI), WF14 (Accessibility) |
| ParaBank | `https://parabank.parasoft.com` | WF02 (requirements), WF07 (API) |

> Load tests and chaos experiments target **only the local Docker stack**. Public demo sites are exercised with functional tests at courteous volume only — never load tested, never attacked.

---

## Ground Rules

1. **Advisory until a human approves.** No agent closes a defect, approves a release, or commits / merges code.
2. **Grounded, not guessed.** Every factual claim must come from the MCP-exposed context. If it is not retrievable, the agent writes `TBD` — never invents a Jira key, measurement, or historical record.
3. **Java is the automation language.** Java 21, Maven, JUnit 5, AssertJ. Python only as CI plumbing; Node only for axe/Pa11y/Playwright browsers.
4. **No secrets in Git.** `.bob/mcp.json` is git-ignored. CI tokens live in GitHub repo secrets only.
5. **Sanctioned targets only.** Only the applications listed above. Never a client, IBM-internal, or third-party production system.
6. **Synthetic data only.** No real PII, no Luhn-valid card numbers — including inside prompts.

---

## Required CI Secrets

Configure these in **GitHub → repo Settings → Secrets and variables → Actions**:

| Secret | Description |
|---|---|
| `ICA_WORKFLOW_URL` | Base URL of the ICA Langflow workflow endpoint |
| `ICA_GATEWAY_TOKEN` | MCP Gateway bearer token |
| `ICA_CONTEXT_KEY` | Context Studio `x-api-key` |
| `ICA_CONTEXT_ID` | Context identifier (`ctx_151793f36ee3`) |

---

## Support

| Need | Channel |
|---|---|
| Peer / SME help | Slack `#applied-ai-specialist-capstone-project` |
| IBM Bob access | Bob access request form + installation guidelines (kit doc 04 §2) |
| ICA access / Context Studio | ICA team owner — needs Editor + Admin on the team |
| Curriculum / certification | L&K team (kit doc 00) |

---

*Kit version 1.0 · Applied AI Specialist — QE Track · IBM Confidential — internal training use*
