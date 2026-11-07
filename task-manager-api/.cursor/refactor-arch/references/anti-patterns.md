# Anti-pattern catalog

Use this catalog in Phase 2. Match **real code evidence**. Do not raise severity just to increase finding count. Suggested default severity is a starting point; adjust with impact in *this* codebase.

Each finding still needs file, line, evidence, and a unique `FINDING-xxx` ID in the report.

---

## Anti-pattern: God Class / God Controller

Severity:
CRITICAL (extreme: many domains + HTTP + SQL + rules in one type) or HIGH (large but single-domain)

Category:
Architecture / MVC / SRP

### Description

One class or module concentrates unrelated responsibilities: routing, validation, business rules, persistence, external I/O, and formatting for multiple domains.

### Detection Signals

- File of hundreds of lines mixing several entity vocabularies
- Methods that both query the database and write HTTP responses
- High fan-in: everything imports this one module
- Names like `AppManager`, `MainController`, `utils` dumping ground

### Example

A single `AppManager` handles users, products, orders, payments, and rendering.

### Why It Is a Problem

Changes in one domain break others. Tests cannot isolate behavior. Cognitive load blocks safe evolution.

### MVC Impact

Destroys Model/View/Controller boundaries.

### SOLID Impact

Violates SRP severely; often ISP and DIP as well.

### Security Impact

Auth checks and data access tend to be inconsistent when everything lives in one place.

### Performance Impact

Hard to optimize one path without risking others; accidental N+1 and duplicate work hide in the mass.

### Recommended Fix

Split by domain and layer (controllers, services, repositories/models, views/DTOs). See playbook: God Class → separation of responsibilities.

### False Positives / Exceptions

Generated code, thin facades that only delegate, or a small script with a handful of functions is not a God Class.

---

## Anti-pattern: Fat Controller

Severity:
HIGH (complex rules) or MEDIUM (moderate orchestration still too thick)

Category:
MVC / SRP

### Description

Controller (or framework “view” acting as controller) contains multi-step business logic instead of delegating.

### Detection Signals

- Pricing, eligibility, state machines inside request handlers
- Nested conditionals spanning many entities
- Transactions and multiple repositories used inline
- Handler longer than a short validate-delegate-respond flow

### Example

An Express route calculates discounts, stock, and invoices before `res.json`.

### Why It Is a Problem

HTTP layer becomes untestable without a server. Rules cannot be reused from jobs or CLI.

### MVC Impact

Controller absorbs Model/service responsibilities.

### SOLID Impact

SRP; often OCP (new rules mean editing the handler).

### Security Impact

Authorization easily mixed with happy-path logic and skipped on some branches.

### Performance Impact

Secondary; but loops and queries in handlers are common companions.

### Recommended Fix

Extract a service/use case. Controller keeps request/response. Playbook: Fat Controller → Controller + Service.

### False Positives / Exceptions

Trivial CRUD mapping with no rules. Framework-required glue.

---

## Anti-pattern: Business Logic in Route/View

Severity:
HIGH

Category:
MVC

### Description

Route definitions, templates, or UI widgets implement domain rules (totals, permissions, workflow).

### Detection Signals

- SQL or domain `if` in `routes.rb`, `urls.py`, `app.get`, Blade/ERB/Jinja
- Flutter widgets calling repositories and encoding business policies
- Templates computing prices or access control

### Example

A Jinja template decides order status with copied Python-like rules.

### Why It Is a Problem

Rules duplicate and drift. Views become undeclarable and hard to test.

### MVC Impact

View/route owns Model responsibilities.

### SOLID Impact

SRP.

### Security Impact

Client-visible templates may leak or skip server-side checks (still verify server).

### Performance Impact

Usually low unless templates trigger queries.

### Recommended Fix

Move rules to service/domain; view only presents. Playbook: Business Logic in Route → Controller/Service.

### False Positives / Exceptions

Simple display formatting (`uppercase`, date format) is presentation, not domain logic.

---

## Anti-pattern: Model Overload

Severity:
HIGH or CRITICAL if one model file owns the whole product

Category:
MVC / SRP

### Description

Model layer owns HTTP, unrelated workflows, mail, payments, or multiple aggregates with no cohesion.

### Detection Signals

- `models.py` / `User.php` importing the web framework
- Active Record callbacks triggering HTTP and emails for unrelated domains
- One “model” module defining all tables and all application services

### Example

`User` model sends invoices, charges cards, and renders JSON.

### Why It Is a Problem

Persistence and application services cannot evolve independently.

### MVC Impact

Model becomes a hidden controller/service.

### SOLID Impact

SRP; DIP if models depend on HTTP clients.

### Security Impact

Mass-assignment and callback side effects.

### Performance Impact

Callbacks causing extra queries (N+1 in after-save).

### Recommended Fix

Keep entities/invariants in models; extract services and adapters. Playbook: God Class / Model split.

### False Positives / Exceptions

Rich domain models with invariants are valid. Framework Active Record with simple callbacks is not overload by itself.

---

## Anti-pattern: Tight Coupling

Severity:
HIGH

Category:
Architecture / DIP

### Description

High-level modules depend on concrete infrastructure (SQL driver, HTTP SDK, global app instance) with no seam.

### Detection Signals

- Controllers `new MysqlConnection()` or import `db` and write SQL
- Business functions import `flask.request` or `HttpContext` deep in domain
- Impossible to unit-test without a database

### Example

Order total function opens a TCP connection to MySQL internally.

### Why It Is a Problem

Cannot substitute fakes; every test is an integration test. Infrastructure changes ripple everywhere.

### MVC Impact

Layers collapse.

### SOLID Impact

DIP (and often SRP).

### Security Impact

Connection strings and credentials spread with the coupling.

### Performance Impact

Hidden connections per call; no shared pooling policy.

### Recommended Fix

Inject repositories/clients. Playbook: Global State → DI; External Integration → Adapter.

### False Positives / Exceptions

Small scripts; composition root that *wires* concretes is expected.

---

## Anti-pattern: Global Mutable State

Severity:
HIGH

Category:
Architecture / Testability

### Description

Shared mutable module-level or singleton state (connections, “current user”, caches without invalidation, in-memory DB) written from many places.

### Detection Signals

- `global db`, `App.instance`, mutable `users = []` at module scope
- Request data stored on a process-wide object
- Tests that pass only in isolation because order mutates globals

### Example

Express app puts `global.cart` on the Node process.

### Why It Is a Problem

Race conditions, leaked data between requests, unreproducible tests.

### MVC Impact

Hidden dependencies bypass constructor/controller flow.

### SOLID Impact

DIP; SRP of “who owns lifecycle”.

### Security Impact

Data leakage across users; auth context mix-ups.

### Performance Impact

Unbounded in-memory growth.

### Recommended Fix

Request-scoped context, DI, explicit stores. Playbook: Global State → Dependency Injection.

### False Positives / Exceptions

Immutable constants, properly pooled connection *objects* created at startup if not mutated per request.

---

## Anti-pattern: Duplicated Business Logic

Severity:
MEDIUM or HIGH if security/pricing rules diverge

Category:
Quality / SRP

### Description

The same rule (discount, permission, status transition) is copy-pasted across handlers.

### Detection Signals

- Near-identical blocks in several files
- Divergent constants (tax rates) in two places
- Copy-paste comments

### Example

`calculateTotal` exists in `order_routes` and `report_routes` with different rounding.

### Why It Is a Problem

Fixes apply to one path only; production inconsistencies.

### MVC Impact

Rules do not live in one Model/service.

### SOLID Impact

SRP of the rule; OCP harder.

### Security Impact

One endpoint authorizes, the duplicate does not.

### Performance Impact

Duplicate queries as well as duplicate rules.

### Recommended Fix

Shared domain/service function. Playbook: Duplicated Logic → Shared Service.

### False Positives / Exceptions

Similar-looking mapping code that is actually different DTOs.

---

## Anti-pattern: N+1 Query

Severity:
MEDIUM (HIGH if unbounded lists in hot paths)

Category:
Performance

### Description

Loading a collection then querying per item in a loop.

### Detection Signals

- `for item in list: db.query(...)`
- ORM lazy associations accessed in loops without prefetch
- Request logs showing 1 + N identical queries

### Example

List orders, then `SELECT * FROM items WHERE order_id=?` per order.

### Why It Is a Problem

Latency and DB load grow with list size.

### MVC Impact

Often sits in controllers/templates that walk graphs.

### SOLID Impact

Indirect (repository API too naive).

### Security Impact

Rare; timeouts can become availability issues.

### Performance Impact

Primary impact: latency and connection use.

### Recommended Fix

Eager load, join, or batch `WHERE id IN (...)`. Playbook: N+1 → Eager Loading/Batch.

### False Positives / Exceptions

Loops over a **bounded** tiny set (e.g. 2 system rows) with no growth. Still note if it can grow.

---

## Anti-pattern: Missing Validation

Severity:
MEDIUM or HIGH if it enables injection/corrupt data

Category:
Quality / Security

### Description

Handlers persist or compute from untrusted input without schema/type/range checks.

### Detection Signals

- `request.json` used directly in SQL or ORM create
- No DTO/class-validator/pydantic/FormRequest
- Implicit trust of query params for IDs and roles

### Example

User role taken from body and stored.

### Why It Is a Problem

Corrupt data, 500s, injection, privilege issues.

### MVC Impact

Controller skipped shallow validation.

### SOLID Impact

Weak ISP of input types.

### Security Impact

Mass assignment, injection, IDOR if combined with missing authz.

### Performance Impact

Malformed payloads causing expensive work.

### Recommended Fix

Validator/DTO at the edge. Playbook: Missing Validation → Validator/DTO.

### False Positives / Exceptions

Internal trusted workers with a schema at the message boundary already.

---

## Anti-pattern: Deprecated API Usage

Severity:
MEDIUM (HIGH if security-sensitive or removed in the pinned version)

Category:
Quality / Maintainability

### Description

Calls APIs marked deprecated/obsolete in the detected framework/language version.

### Detection Signals

- Docs/changelog vs detected version
- Runtime warnings
- Removed modules still imported (`cgi`, old Flask `before_first_request`, `url_for` patterns, etc.) — **only if true for that version**

### Example

Using a removed Express method on a version that no longer has it.

### Why It Is a Problem

Breaks on upgrade; may miss security fixes.

### MVC Impact

Usually none unless the deprecated piece is the routing model.

### SOLID Impact

None directly.

### Security Impact

Possible if the old API was insecure.

### Performance Impact

Possible if the replacement is the supported fast path.

### Recommended Fix

Document per finding: Deprecated API, File, Line, Technology, Version, Reason, Modern Equivalent, Migration Recommendation, Severity. If unsure: `Modern Equivalent: Unable to determine safely`. Playbook: Deprecated API → Modern API.

### False Positives / Exceptions

Stable old APIs that are not deprecated. Do not invent deprecation.

---

## Anti-pattern: Hardcoded Secrets / Credentials

Severity:
CRITICAL

Category:
Security

### Description

Passwords, API keys, tokens, private keys, or secret strings committed in source.

### Detection Signals

- `password =`, `SECRET_KEY =`, `apiKey:` with literal strings
- Connection URIs with credentials
- Private keys in repo

### Example

`SECRET_KEY` assigned a literal in `app.py` (report **location only**).

### Why It Is a Problem

Repo leak equals credential leak. Rotation is painful.

### MVC Impact

Configuration not in a config/env boundary.

### SOLID Impact

None directly.

### Security Impact

Critical exposure.

### Performance Impact

None.

### Recommended Fix

Environment / secret manager. Never echo the secret in the report. Playbook: Hardcoded Configuration → Configuration/Environment.

### False Positives / Exceptions

Placeholders clearly fake in tests (`password = "test"` in unit tests with no production use) — still prefer env. Public unsecret config (debug flags) is not this pattern.

---

## Anti-pattern: SQL Injection / Unsafe Query Construction

Severity:
CRITICAL when user input reaches the query string; HIGH if only internally concatenated identifiers

Category:
Security

### Description

SQL built with string concatenation/interpolation of untrusted or weakly trusted data.

### Detection Signals

- f-strings / `+` / `.format` into SQL
- `$query = "SELECT ... $id"`
- `where("id = " + req.params.id)`

### Example

`cursor.execute("SELECT * FROM users WHERE id=" + id)`

### Why It Is a Problem

Attacker can read/modify data or run stacked statements depending on the DB.

### MVC Impact

Often in controllers skipping repository parameterization.

### SOLID Impact

None directly.

### Security Impact

Critical.

### Performance Impact

None primary.

### Recommended Fix

Parameterized queries or ORM bind parameters. Playbook: Unsafe SQL → Parameterized Query/ORM.

### False Positives / Exceptions

Static SQL with no interpolation. Identifier allowlists (column names from an enum) may be acceptable if proven.

---

## Anti-pattern: External Integration in Controller

Severity:
HIGH

Category:
MVC / DIP

### Description

Controllers call payment, email, HTTP, or filesystem APIs directly mixed with request handling.

### Detection Signals

- `fetch`/`axios`/`requests` inside route handlers
- SMTP or S3 SDKs in controllers
- Timeouts and retries inline with HTTP mapping

### Example

Laravel controller `Http::post` to a gateway while also saving Eloquent models.

### Why It Is a Problem

Hard to test; retries/timeouts inconsistent; HTTP layer tied to vendors.

### MVC Impact

Controller owns infrastructure.

### SOLID Impact

SRP, DIP.

### Security Impact

SSRF if URLs come from input; tokens in controllers.

### Performance Impact

Synchronous remote calls on the request thread without timeout.

### Recommended Fix

Adapter/service. Playbook: External Integration in Controller → Adapter/Service.

### False Positives / Exceptions

Health-check ping that is the entire purpose of the endpoint.

---

## Anti-pattern: Queries Inside Loops (chatty I/O)

Severity:
MEDIUM or HIGH

Category:
Performance

### Description

Database or HTTP I/O inside loops even if not classic ORM N+1.

### Detection Signals

- `for` + `await fetch`
- `foreach` + `save()` without batch
- Template loops that hit the DB

### Example

Notify each user with a separate HTTP call in a request.

### Why It Is a Problem

Latency multiplies; failure modes multiply.

### MVC Impact

Often in fat controllers.

### SOLID Impact

Service should own batch policy.

### Security Impact

Timeouts / DoS against self.

### Performance Impact

Primary.

### Recommended Fix

Batch APIs, queues, eager load. Related to N+1 playbook.

### False Positives / Exceptions

Loop size is strictly 1 or a compile-time tiny constant.

---

## Anti-pattern: Inconsistent Error Handling

Severity:
MEDIUM

Category:
Quality

### Description

Some paths return structured errors; others leak stack traces or empty 500s; mixed exception types.

### Detection Signals

- `except: pass`
- Stack traces in JSON for clients
- Some routes `abort(404)`, others return 200 with `{error}`

### Example

One Flask route returns traceback HTML; another returns `{ok:false}`.

### Why It Is a Problem

Clients cannot handle errors; leaks internals.

### MVC Impact

Missing error middleware/view.

### SOLID Impact

Cross-cutting concern not isolated.

### Security Impact

Information disclosure.

### Performance Impact

None.

### Recommended Fix

Central error handler mapping domain errors to HTTP.

### False Positives / Exceptions

Internal CLI tools that should print traces.

---

## Anti-pattern: Missing Authentication / Authorization

Severity:
CRITICAL if mutating or sensitive data is public; HIGH if partially enforced

Category:
Security

### Description

Endpoints that read/change sensitive data without proving identity or permission.

### Detection Signals

- No middleware/guards on `/admin` or `/users`
- IDOR: access by id without ownership check
- Client-sent `isAdmin` trusted

### Example

`DELETE /users/:id` with no auth.

### Why It Is a Problem

Data theft or destruction.

### MVC Impact

Cross-cutting concern missing at the edge.

### SOLID Impact

Policy not in one place.

### Security Impact

Critical/High by exposure.

### Performance Impact

None.

### Recommended Fix

Authn/authz middleware + service-level checks. Do not claim a vuln without evidence of a reachable path.

### False Positives / Exceptions

Intentionally public endpoints (health, public catalog) documented as such.

---

## Anti-pattern: Magic Numbers and Poor Naming

Severity:
LOW

Category:
Quality

### Description

Unexplained literals and names that hide meaning (`d`, `tmp2`, `42`).

### Detection Signals

- Numeric literals in rules without constants
- Abbreviations unique to one file

### Example

`if status == 3` without an enum.

### Why It Is a Problem

Mis-edits; onboarding cost.

### MVC Impact

Minimal.

### SOLID Impact

Minimal.

### Security Impact

None unless the number is a security timeout wrongly tuned — still usually LOW.

### Performance Impact

None.

### Recommended Fix

Named constants/enums. Do not inflate to MEDIUM.

### False Positives / Exceptions

`0`, `1`, HTTP 200/404 in obvious context.

---

## Anti-pattern: Command Injection / Unsafe OS Execution

Severity:
CRITICAL

Category:
Security

### Description

User-controlled strings passed to shells or `exec`.

### Detection Signals

- `os.system`, `exec(`, `Runtime.getRuntime().exec`, `child_process.exec` with interpolation

### Example

`os.system("convert " + filename)`

### Why It Is a Problem

Arbitrary command execution.

### MVC Impact

Infrastructure in the wrong layer often accompanies this.

### SOLID Impact

None.

### Security Impact

Critical.

### Performance Impact

None.

### Recommended Fix

Avoid shell; use argv arrays; allowlist. Report without reproducing exploits.

### False Positives / Exceptions

Fixed argv lists with no user input.

---

## Anti-pattern: Sensitive Data in Logs

Severity:
HIGH or MEDIUM

Category:
Security

### Description

Passwords, tokens, or PII written to logs.

### Detection Signals

- `console.log(req.body)`, `logger.info(user)` including password fields
- Printing authorization headers

### Example

Middleware logs full request body for `/login`.

### Why It Is a Problem

Log sinks become secret stores.

### MVC Impact

Cross-cutting logging without policy.

### SOLID Impact

None.

### Security Impact

Exposure via log access.

### Performance Impact

Large payloads.

### Recommended Fix

Redact; structured logs with allowlisted fields.

### False Positives / Exceptions

Debug-only local logging clearly stripped in production **and** not committed with secrets — still prefer redaction.
