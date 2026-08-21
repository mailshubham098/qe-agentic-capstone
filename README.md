# qe-agentic-capstone

Applied AI Specialist — Quality Engineering Capstone

## Solutions
- **Solution A:** QE ShiftLeft Factory (IBM Bob) — WF02–WF07, WF10
- **Solution B:** QE Insights & Resilience (IBM ICA) — WF08–WF09, WF11–WF14

## Knowledge Spine
| Item | Value |
|---|---|
| Context ID | `ctx_151793f36ee3` |
| Context Name | QE Industry Context |
| MCP Server | `context-studio` |
| Sources ingested | 8 (all Ready) |

## Requirement Quality Evidence — QEC-101

| Requirement | qualityScore | Verdict |
|---|---|---|
| QEC-101 — Fund transfer (ParaBank) | **82** | APPROVE WITH REWRITES |
| QEC-103 — Loan decision (ParaBank) | 18 → **78** | REWRITTEN — PASS |
| QEC-105 — Shopper checkout (SauceDemo) | **86** | APPROVE |
| QEC-113 — Checkout WCAG 2.2 AA (SauceDemo) | **88** | APPROVE |
| QEC-115 — Resilience tolerance (PetClinic) | 15 → **92** | REWRITTEN — PASS |
| QEC-117 — Basket persistence (SauceDemo) | 12 → **74** | REWRITTEN — PASS |
| QEC-118 — Transfer idempotency (ParaBank) | **92** | APPROVE |
| **Mean** | **84.6** | NFR-001 PASS (threshold ≥70) |

NFR-002: 0 UNTESTABLE criteria after rewrites. Gate PASS.

17 test cases generated: QEC-T301 → QEC-T317 (13×P1, 4×P2).

## CI/CD
12-stage agent-gated pipeline. Agents explain. Scripts enforce.

| Stage | Gate | Status |
|---|---|---|
| 1 — Context sync | MCP reachable | ✅ PASS |
| 2 — Requirement quality gate | NFR-001 ≥70, NFR-002 =0 | ✅ PASS |
| 3 — Test design sync | Advisory | ✅ PASS |
| 4 — Test optimization | Agent selection | ✅ PASS |
| 5 — Build and unit test | Java 21 + JUnit 5 | ✅ PASS |
| 6 — Test data provisioning | NFR-024 Luhn=0 | ✅ PASS |
| 7 — API automation | NFR-003, NFR-007 | ✅ PASS |
| 8 — BDD and UI | NFR-003/004/005 | ⏳ WF04/WF06 pending |
| 9 — Performance smoke | NFR-008/009/010 | ⏳ JMeter plan pending |
| 10 — Accessibility scan | NFR-017/018/020 | ⏳ WF14 pending |
| 11 — Resilience | NFR-012–015 | ⏳ WF13 pending |
| 12 — Triage and release gate | NFR-023 | ✅ ADVISORY |

## Repository
`github.com/mailshubham098/qe-agentic-capstone`
