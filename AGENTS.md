# Project instructions for IBM Bob

Save this file at the root of your `qe-agentic-capstone` repository as the project
instruction file your agentic IDE reads automatically (`AGENTS.md`, or the
equivalent your Bob build expects — check doc 04 §2.4). Bob loads it at the start
of every session, so these rules apply without being re-pasted.

Keep it short enough to stay useful. Rules an agent will not read are not rules.

---

## What this repository is

Agent-generated quality engineering assets for the Applied AI Specialist
capstone (QE track). Java test automation across four applications under test.
Every asset traces requirement → acceptance criterion → test case → script →
execution → defect.

## Non-negotiables

1. **You propose, a human approves.** Never mark work complete, never commit,
   never push, never modify a production system.
2. **Ground every factual claim in the QE Industry Context via MCP.** If it is
   not retrievable, write `TBD` — never invent a Jira key, Zephyr key,
   measurement or historical record.
3. **Java 21, Maven, JUnit 5, AssertJ.** Python only as Chaos Toolkit plumbing;
   Node only for axe and Playwright browsers.
4. **Synthetic data only.** No real personal data, no client data, and no value
   that passes a Luhn check as a card number — including in prompts.
5. **Sanctioned targets only.** Load tests and chaos experiments run against the
   local dockerised stack. Never against a public demo site, a client system or
   anything IBM-internal.

## MCP knowledge calls

Every call to a `context-broker-*` tool must pass:

- `context_id` — the `ctx_…` value for this deployment (see `.bob/mcp.json`)
- `AgentPersona` — the sub-agent role you are currently performing

A call with a missing, empty or placeholder `context_id` is a bug. If a call
returns nothing useful, say so rather than filling the gap from general knowledge.

## Code conventions

| Concern | Rule |
|---|---|
| Language level | Java 21. Records, sealed types, pattern matching, text blocks welcome |
| Test runner | JUnit 5 only. No JUnit 4 |
| Assertions | AssertJ fluent. One logical assertion, or `assertAll` for grouped |
| UI | Page Object Model. Pages expose behaviour, never `WebElement` |
| Waits | Explicit waits only. `Thread.sleep` is banned |
| Locators | `data-test`, `id`, or accessible role/name. Positional XPath is banned |
| API | Shared request specifications. Assert body **and** JSON schema |
| Test data | Never inline in the test body. Use a provider or Datafaker |
| Independence | Each test creates and cleans its own state. No inter-test order |
| Naming | Class `<Feature>Test`; method `tc<zephyrNumber>_<behaviour>` |
| Logging | SLF4J. No `System.out.println` |
| Secrets | Environment variables or CI secrets. Never in source |
| Parallelism | Must be safe at JUnit 5 class-level parallel execution |

## Package layout

```
src/test/java/com/ibm/qe/
├── core/       driver factory, config, waits, hooks
├── pages/      page objects
├── api/        request specs, clients, schema validators
├── data/       data providers, Datafaker builders
├── steps/      Cucumber step definitions
├── runners/    JUnit 5 / Cucumber runners
├── tests/      plain JUnit 5 tests
├── a11y/       accessibility suites
└── resilience/ post-fault integrity assertions
src/test/resources/
├── features/   .feature files
├── schemas/    JSON schemas for contract assertions
├── testdata/   SQL seeds and CSV fixtures
├── chaos/      experiments and docker-compose
└── jmeter/     .jmx plans
```

## Definition of Done for anything you generate

- [ ] Traces to a requirement and an acceptance criterion
- [ ] Compiles (`mvn -q test-compile` clean)
- [ ] Runs green against the local application under test
- [ ] Deterministic across 3 consecutive runs, no order dependency
- [ ] No secret, no real personal data, no client-identifying content
- [ ] Reviewed and approved by a named Quality Engineer

## How to behave in a session

- State which sub-agent role you are performing and which context tools you
  called at the top of each response.
- Generate complete, compiling code. No placeholder bodies, no
  "implementation left as an exercise".
- Prefer editing an existing file over creating a parallel one.
- When uncertain, say what you would need. A flagged gap is useful; a confident
  invention is a defect.
