# Architecture audit report template

This is the official Phase 2 output format. Produce the report in the user's language when they write in that language; keep section titles in English as specified below unless the user asked for a fully localized report. Finding bodies may be in the user's language.

**Phase 2 must not modify any application files.** State that at the end.

Do not invent counts, files, lines, endpoints, or vulnerabilities.

---

# Architecture Audit Report

## 1. Executive Summary

Short paragraph: stack, architecture label, overall risk, whether Phase 3 is recommended. Include total finding count.

## 2. Detected Stack

- Language:
- Language version:
- Framework:
- Framework version:
- Runtime:
- Package manager:
- Database:
- ORM:
- Main libraries:
- Test system:
- Build system:
- Docker:
- External integrations:

Use `not detected` / `unknown` when evidence is missing.

## 3. Current Architecture

Label (monolithic, MVC, partial MVC, layered, hybrid, unstructured, etc.) and a factual description of how responsibilities are actually distributed. Note mismatches between folder names and real behavior.

## 4. Architecture Flow

Show actual flow vs intended/adapted MVC flow.

```text
Actual:
...

Intended (technology-adapted):
...
```

## 5. Severity Summary

| Severity | Count |
|----------|-------|
| CRITICAL | X |
| HIGH | X |
| MEDIUM | X |
| LOW | X |

Counts must equal the findings listed in section 6.

## 6. Findings

Every finding uses a unique sequential ID: `FINDING-001`, `FINDING-002`, ...

### FINDING-001 — [CRITICAL] Name

- Category:
- File:
- Line:
- Evidence:
- Problem:
- Impact:
- MVC/SOLID Violation:
- Recommended Fix:
- Refactoring Strategy:

Repeat for each finding. Severity in the heading must be one of `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.

### File and line

Prefer:

```text
File: app.py
Line: 42
```

or:

```text
File: models.py
Lines: 1-350
```

If the location cannot be determined: `Line: unavailable`. Never invent line numbers.

### Evidence

Evidence must be observable (what the code does). Example:

```text
Evidence:
Controller directly executes SQL queries and contains business rules
for order calculation.
```

Do not promote a hypothesis to a finding. If uncertain, omit or mark as observation in the executive summary, not as a CRITICAL fact.

### Secrets

Never paste secret values. Example allowed: `Hardcoded credential detected at app.py:42`.

## 7. Security Findings

List security-related finding IDs and a short restatement (no secret values). If none: `None detected with current evidence.`

Cover: hardcoded secrets, SQLi, command injection, path traversal, XSS, SSRF, authn/authz, data exposure, sensitive logs.

## 8. Performance Findings

List performance-related finding IDs (N+1, queries in loops, chatty HTTP, missing pagination, etc.). If none: `None detected with current evidence.` Classify by real impact, not theoretical micro-optimizations.

## 9. Deprecated APIs

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

If the replacement cannot be determined from the detected technology/version: `Modern Equivalent: Unable to determine safely`.

If none: `None detected with current evidence.`

## 10. Architectural Improvements

Ordered list of structural improvements (layers, DI, validation, config, adapters) without implementing them in Phase 2.

## 11. Refactoring Plan

Ordered by severity. Map each planned step to finding IDs. Prefer incremental: new abstraction → migrate consumers → remove old responsibility.

State explicitly that execution waits for user confirmation.

## 12. Validation Plan

What will be run in Phase 3 for this stack: build command, test command, boot command, which endpoints (only those discovered), and what will be marked `NOT VALIDATED` if it cannot be run.

---

## Closing (required)

```text
No files were modified during Phase 2.

Proceed with refactoring (Phase 3)? [y/n]
```

Stop. Do not start Phase 3 until the user confirms.
