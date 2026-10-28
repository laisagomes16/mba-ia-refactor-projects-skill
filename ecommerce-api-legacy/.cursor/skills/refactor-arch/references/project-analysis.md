# Project analysis (Phase 1)

Read-only phase. No application files may be created, edited, moved, or deleted. No dependency or config changes. No refactoring.

Use evidence from the target codebase only. If a fact is not present, record `unknown` or `not detected`. Never invent stack details.

## 1. Inventory

1. List the target root (the project the user asked to analyze).
2. List manifests, lockfiles, Docker files, CI configs, README (for clues only — verify against code).
3. List source trees: `src/`, `app/`, `lib/`, `routes/`, `controllers/`, `models/`, `views/`, `services/`, `repositories/`, `middleware/`, `config/`, `tests/`, and any language-specific equivalents.
4. Count source files actually read/analyzed. Report that count; do not estimate from folder names alone.
5. Ignore vendor/lock noise unless needed for versions: `node_modules/`, `vendor/`, `.venv/`, `target/`, `dist/`, `.git/`.

## 2. Stack detection signals

Detect **when files exist**. This list is not exhaustive.

| Evidence | Typical meaning |
|----------|-----------------|
| `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` | JavaScript/TypeScript, npm/yarn/pnpm |
| `tsconfig.json`, `*.ts`, NestJS modules | TypeScript; NestJS if `@nestjs/*` |
| `composer.json`, `artisan`, `app/Http` | PHP; Laravel/Symfony by packages and folders |
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `*.py` | Python |
| Flask/Django/FastAPI imports | Framework + version from pins if present |
| `pom.xml`, `build.gradle`, `*.java` | Java; Spring if `spring-boot` |
| `*.csproj`, `*.sln`, `Program.cs` | C# / ASP.NET |
| `Gemfile`, `config/routes.rb` | Ruby / Rails |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `pubspec.yaml` | Dart / Flutter |
| `mix.exs` | Elixir / Phoenix |
| `Dockerfile`, `docker-compose.yml` | Runtime/container clues |
| `*.sqlite`, SQL files, ORM config | Database |
| `phpunit.xml`, `jest`, `pytest`, `*Test.java` | Test system |

Also record: runtime, main libraries, build system, entry points (`app.py`, `server.js`, `main.go`, `Program.cs`, `index.php`, `main.dart`, framework bootstrap), configuration mechanism, external HTTP/SDK integrations.

### Version rules

- Prefer lockfiles and pinned manifests.
- Do not infer a framework version from “it looks like Flask 3”.
- If only a major is known, report that and mark patch as unknown.

## 3. Architecture mapping

For each concern, record **files + how they are used**, not just folder names.

| Concern | What to look for |
|---------|------------------|
| Entry points | Process start, app factory, `main` |
| Routes | HTTP/CLI/message mappings |
| Controllers | Request orchestration |
| Models | Entities, persistence, invariants |
| Views | Templates, serializers, DTOs, JSON resources |
| Services / use cases | Application/business orchestration |
| Repositories | Data access abstraction |
| Validators | Input schemas |
| Middleware | Cross-cutting HTTP/pipeline |
| Jobs / events / listeners | Async and domain events |
| Adapters / integrations | External APIs, mail, queues |
| Infrastructure | DB drivers, file system, clock |
| Configuration | env, config objects, hardcoded values |

### Real vs intended flow

Sketch the **actual** call graph. Example intended:

```text
Route → Controller → Service → Repository → Database
```

Example violation:

```text
Route → Controller
          ├── SQL
          ├── validation
          ├── business rules
          ├── outbound HTTP
          └── HTTP response
```

Treat the second as a likely architectural violation (confirm with file/line evidence in Phase 2).

## 4. Architecture classification

Choose the closest label(s). Hybrid is allowed.

- Unstructured monolith (few files, mixed responsibilities)
- MVC / partial MVC (folders or classes exist but flow is incomplete)
- Layered architecture
- Service + repository
- Modular monolith
- Hexagonal / ports and adapters
- Clean architecture
- Hybrid

**Do not** conclude “MVC is correct” because `models/` and `controllers/` exist. Classify from responsibilities and dependencies (who imports whom, where SQL lives, where HTTP lives).

## 5. Domain and data

Infer domain from route names, entities, table names, and README **after** verifying code. List DB engine and table/collection names only if found in schema, migrations, SQL, or ORM models.

## 6. Potential risks (hypotheses)

Phase 1 may list **potential** risks (business logic in controllers, hardcoded config, string-built SQL). Mark them as risks, not findings. Findings with IDs, severity, and lines belong to Phase 2.

## 7. Unknown / unfamiliar technology

1. Detect language from file extensions and tooling.
2. Detect framework if manifests/imports allow.
3. Identify entry points and data access.
4. Map responsibilities and dependency flow.
5. Apply general separation-of-concerns, not a forced three-folder MVC.
6. Record uncertainties explicitly.

Recognized pattern families include (not a closed list): PHP (Laravel, Symfony), JavaScript (Node.js, Express), TypeScript (NestJS), Python (Flask, Django, FastAPI), Java (Spring), C# (ASP.NET), Ruby (Rails), Go, Rust, Dart (Flutter).

## 8. Phase 1 summary template

Fill with **real** values only:

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

Then continue to Phase 2 still without modifying files.
