# MVC architecture guidelines

Apply **principles**, not a cargo-cult of three directories. Adapt names to the technology. Do not force classic MVC onto a stack that already has a better equivalent layered flow.

Do not create artificial interfaces/abstractions only to look like SOLID.

## Target flow (adapt names)

Acceptable for many HTTP APIs:

```text
Route
  ↓
Controller
  ↓
Service / Use Case
  ↓
Repository / Model
  ↓
Database
```

Classic server-rendered MVC:

```text
Route → Controller → Model
                  → View (template)
```

REST/JSON “View” may be: DTO, Resource, Serializer, Response Model, Presenter, or JSON representation.

A flow is acceptable when it improves separation of responsibilities, cohesion, low coupling, testability, and maintainability.

Folder names (`models/`, `controllers/`, `services/`, `repositories/`) are **not** proof of compliance.

## Model

Responsible for:

- entities and domain data
- persistence when appropriate for the stack
- relationships
- invariants of the entity/aggregate

Must not arbitrarily concentrate:

- HTTP / routing
- presentation/serialization of API responses (unless the stack’s model is also the serializer by convention — still keep HTTP out)
- application workflow unrelated to the entity
- arbitrary external integrations (payment SDKs, mail, HTTP clients)

**Model Overload** is a HIGH/CRITICAL smell when one type owns persistence + HTTP + unrelated workflows for many domains.

## Controller

Responsible for:

- receiving the request
- shallow input validation (or delegating to a validator/DTO)
- delegating to services/use cases
- returning the response (status + view/DTO)

Must not contain complex business rules (pricing, eligibility, multi-step workflows, transaction scripts spanning many entities).

**Fat Controller** and **business logic in route/view** are typical HIGH findings.

## View

Responsible for:

- presentation
- templates
- serialization
- representation of data

In APIs, keep controllers from assembling ad-hoc dictionaries mixed with SQL and rules. Extract serializers/DTOs when representation logic is non-trivial.

## Repository / data access

When SQL/ORM access is embedded in controllers or routes, prefer a repository or model persistence API. Controllers should not own query strings or unit-of-work details.

## Services / use cases

Application rules that orchestrate multiple models, transactions, and policies belong here (or in a rich domain model — pick one consistent place, do not duplicate).

## Configuration

No hardcoded secrets. Environment or a config module. Feature flags and URLs should not be scattered magic strings when they affect security or deployment.

## SOLID (audit, do not over-engineer)

| Principle | What to check |
|-----------|----------------|
| SRP | A module/class should not mix HTTP, SQL, and unrelated business policies |
| OCP | Repeated `if type ==` explosion for every new variant without a stable extension point — only when it clearly hurts change |
| LSP | Subtypes that break caller expectations |
| ISP | Fat interfaces that force unused methods |
| DIP | High-level policy depending on concrete SQL/HTTP drivers with no seam for tests — when tests or substitution are needed |

Do not introduce DI containers, interfaces, or extra layers if the app is tiny and a single extraction already restores SRP.

## Technology-adapted mapping (examples)

| Stack | Typical names |
|-------|----------------|
| Express / Node | router → controller/handler → service → repository |
| NestJS | controller → service → repository/TypeORM |
| Flask / FastAPI | blueprint/router → controller or route module → service → model/repository |
| Django | urls → views (controllers) → models; services if views fat |
| Laravel | routes → controller → service/action → Eloquent model |
| Spring | `@RestController` → `@Service` → repository |
| ASP.NET | controller → service → DbContext/repository |
| Rails | routes → controller → model; service objects if fat |
| Go | mux/handler → service → store |
| Flutter | UI widgets (view) → controllers/BLoC → repositories |

For unknown stacks: map “input adapter”, “orchestration”, “domain”, “output adapter” and apply the same rules.

## What not to do

- Rewrite the entire app to Clean Architecture when extracting a service + repository fixes the findings.
- Change public URL paths, payloads, or auth behavior while refactoring.
- Claim MVC is done because empty folders were created.
