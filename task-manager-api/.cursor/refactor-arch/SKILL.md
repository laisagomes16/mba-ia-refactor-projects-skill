---
name: refactor-arch
description: >-
  Analyzes an existing codebase, audits architecture/MVC/SOLID/security/performance
  issues, produces a structured report, and refactors only after explicit user
  confirmation. Use when the user invokes refactor-arch, asks for architectural
  refactoring to MVC (or MVC-adapted layered architecture), requests a code
  architecture audit, or wants technology-agnostic cleanup of anti-patterns.
---

# refactor-arch

Act as a senior software engineer specialized in architecture, MVC, SOLID, security, performance, code quality, and refactoring. The skill is **technology-agnostic**. Do not assume Python, Flask, Node, Laravel, Spring, or any specific folder layout.

## Objective

Analyze an existing codebase, identify its real technology and architecture, audit problems, generate a structured report, ask for confirmation, and only then refactor and validate.

## Scope

In scope: stack detection, architecture mapping, anti-pattern audit, MVC/SOLID review, security, performance, deprecated APIs, incremental refactoring, validation, re-audit.

Out of scope (unless the user explicitly expands it): full rewrites, changing public API contracts, inventing features, inventing tests, forcing zero remaining findings.

Do not analyze or modify files that are not part of the target application unless the user points to them.

## References (read when needed)

Do not duplicate these files into the conversation. Read them at the phase that requires them.

- Phase 1: [references/project-analysis.md](references/project-analysis.md)
- Phase 2: [references/anti-patterns.md](references/anti-patterns.md), [references/audit-report-template.md](references/audit-report-template.md), [references/mvc-architecture-guidelines.md](references/mvc-architecture-guidelines.md)
- Phase 3: [references/refactoring-playbook.md](references/refactoring-playbook.md)

## Execution protocol

Follow **exactly three sequential phases**:

1. FASE 1 — ANÁLISE
2. FASE 2 — AUDITORIA
3. FASE 3 — REFATORAÇÃO

Phase 3 must never start before Phase 2 is complete **and** the user gives explicit confirmation (`y`, `yes`, `sim`, `proceed`, `refatore`, or equivalent). If the user says `n` / `no` / `não`, stop. Do not start Phase 3 because the user asked for the skill in general.

**Precision:** never invent files, lines, endpoints, versions, frameworks, dependencies, tests, results, or vulnerabilities. Use only evidence from the real codebase. If unknown: say so.

**Do not force zero findings.** Remaining LOW/MEDIUM items may be acceptable. Document what remains and why.

---

## FASE 1 — ANÁLISE

**Read** [references/project-analysis.md](references/project-analysis.md).

**Forbidden:** modify code, move/remove/create application files, change dependencies, refactor.

### Detect stack from evidence

Inspect manifests and configs (examples, not exhaustive): `package.json`, `composer.json`, `requirements.txt`, `pyproject.toml`, `pom.xml`, `build.gradle`, `go.mod`, `Cargo.toml`, `*.csproj`, `Gemfile`, `mix.exs`, `pubspec.yaml`, `Dockerfile`, `docker-compose.yml`.

Detect, when evidence exists: language, language version, framework, framework version, runtime, package manager, database, ORM, main libraries, test system, build system, entry points, configuration, Docker, external integrations.

Do not guess versions. If a version is not in the codebase, write `unknown`.

### Detect architecture from behavior, not folder names

Map: entry points, routes, controllers, models, views, services, repositories, DTOs, validators, middleware, jobs, events, listeners, adapters, integrations, infrastructure, DB access, configuration.

Map the **real dependency flow**, then compare it to an intended layered flow.

Folder names such as `models/`, `controllers/`, `services/`, `repositories/` do **not** prove a correct architecture. Responsibilities and imports do.

Classify the existing architecture as one of (or hybrid): monolithic, MVC, partial MVC, layered, service/repository, modular monolith, hexagonal, clean architecture, unstructured.

### Phase 1 output

Present a summary in this shape (values must be real):

```text
================================
PHASE 1: PROJECT ANALYSIS
================================

Language:      ...
Framework:     ...
Dependencies:  ...
Domain:        ...
Architecture:  ...
Source files:  N files analyzed
DB:            ...
DB tables:     ...

Entry points:
- ...

Architecture flow:
...

Potential risks:
- ...

================================
```

Then proceed to Phase 2 without modifying files.

---

## FASE 2 — AUDITORIA

**Read** the three Phase 2 references listed above.

**Forbidden:** edit code, create/remove/move application files, change dependencies or config, refactor. Phase 2 is analysis only.

Cross the real implementation against MVC, SOLID (SRP, OCP, LSP, ISP, DIP), security, performance, quality, maintainability, testability, the anti-pattern catalog, and deprecated APIs.

Do not create artificial abstractions just to “satisfy SOLID”. Do not inflate severity to increase finding count.

### Severity (exactly these four)

| Level | Use for |
|-------|---------|
| CRITICAL | Severe architecture or security failures: secrets, SQLi, arbitrary code execution, sensitive data exposure, authn/authz collapse, extreme God Class, total mixing of responsibilities, data integrity at risk |
| HIGH | Strong MVC/SOLID violations: Fat Controller, complex business rules in controllers, infra access in the wrong layer, tight coupling, global mutable state, missing DI when needed, grave SRP violations, overloaded models, complex logic in routes |
| MEDIUM | Moderate architecture/performance/quality: N+1, relevant duplication, deprecated APIs, missing validation, inconsistent errors, oversized methods, weak testability, unnecessary dependencies |
| LOW | Readability/quality: magic numbers, naming, small organization issues, small duplication, stale comments, minor inconsistencies |

### Findings rules

- Unique IDs: `FINDING-001`, `FINDING-002`, ...
- File and line exact when possible. Else `Line: unavailable`. Never invent line numbers.
- Evidence must justify the classification. Do not treat a hypothesis as fact.
- Never print real secrets. Report location only, e.g. `Hardcoded credential detected at app.py:42`.

### Deprecated APIs

For each occurrence:

```text
Deprecated API:
File:
Line:
Technology:
Version:
Reason:
Modern Equivalent:
Migration Recommendation:
Severity:
```

If the modern equivalent cannot be determined safely: `Modern Equivalent: Unable to determine safely`. Do not invent equivalents.

### Security and performance

Security: hardcoded secrets/passwords/API keys/tokens, SQL injection, command injection, path traversal, XSS, SSRF, weak authn/authz, data exposure, sensitive data in logs.

Performance: N+1, duplicate queries, queries in loops, repetitive external calls, unnecessary processing, over-fetching, missing pagination, unnecessary sync work, missing cache only when clearly applicable. Classify by real impact.

### Phase 2 output

Follow [references/audit-report-template.md](references/audit-report-template.md) exactly (sections 1–12).

End Phase 2 with:

```text
No files were modified during Phase 2.

Proceed with refactoring (Phase 3)? [y/n]
```

Stop and wait. Do not refactor yet.

---

## FASE 3 — REFATORAÇÃO

Start only after explicit confirmation.

**Read** [references/refactoring-playbook.md](references/refactoring-playbook.md).

### Strategy

1. Review findings.
2. Prioritize CRITICAL → HIGH → MEDIUM → LOW.
3. Apply transformations from the playbook, adapted to the real stack.
4. Preserve behavior: public endpoints, contracts, auth, business rules.
5. Prefer incremental change:

```text
Problem → create new abstraction → migrate consumers → remove old responsibility → tests → validate → continue
```

Avoid a full rewrite when incremental refactoring is enough. Do not create three folders named Model/View/Controller if the technology uses a better equivalent (e.g. Route → Controller → Service/Use Case → Repository → Database).

For unknown stacks: detect language → detect framework if possible → entry points → data access → map responsibilities → apply general architectural principles → record uncertainties.

### Validation (required)

Refactoring is not complete when files change. Validate with **compatible** commands only (detect from the real project; do not run incompatible tools).

- **Build:** e.g. `npm run build`, `mvn test`, `gradle build`, `dotnet build`, `go test ./...`, `pytest`, `flutter analyze` — only if that ecosystem is present.
- **Tests:** run existing tests. If none: `No automated tests detected.` Do not invent tests.
- **Boot:** verify the app starts with the project’s real start command when feasible.
- **Endpoints:** when applicable, discover real endpoints, start the app, exercise relevant ones (status, body, errors, auth, critical operations). If not possible: `NOT VALIDATED` + reason. Never claim an endpoint works untested.

### Re-audit

After changes, re-audit. Compare BEFORE vs AFTER counts for CRITICAL/HIGH/MEDIUM/LOW. Report `Resolved`, `Remaining`, `New`. Check that refactoring did not introduce new problems.

### Phase 3 output

```text
================================
PHASE 3: REFACTORING COMPLETE
================================

## Refactoring Summary

Resolved:
- X CRITICAL
- X HIGH
- X MEDIUM
- X LOW

Remaining:
- X CRITICAL
- X HIGH
- X MEDIUM
- X LOW

## New Project Structure

...

## Validation

Build:             PASS | FAIL | SKIPPED
Tests:             PASS | FAIL | No automated tests detected.
Application Boot:  PASS | FAIL | NOT VALIDATED
Endpoints:         PASS | FAIL | NOT VALIDATED
Architecture:      PASS | FAIL
Security:          PASS | FAIL

New Issues:
...

## Re-audit

BEFORE:
CRITICAL: X
HIGH:     X
MEDIUM:   X
LOW:      X

AFTER:
CRITICAL: X
HIGH:     X
MEDIUM:   X
LOW:      X

Resolved:
Remaining:
New:

================================
```

Values must reflect real execution. Document remaining findings and why they were left.

## Confirmation rule

Phase 3 requires an explicit affirmative answer after the Phase 2 report. Implicit “continue working” in an earlier message is not confirmation.

## Refactoring rules

- Preserve functional behavior and public contracts.
- Do not rewrite the whole application without necessity.
- Adapt MVC to the technology; do not cargo-cult directories.
- Do not leak secrets in reports or new files.
- Do not add dependencies unless required to complete a finding fix and compatible with the stack.

## Validation rules

- Use only stack-compatible commands.
- Do not claim PASS without having run or attempted the check.
- Use `NOT VALIDATED` with a reason when a check cannot be performed.
