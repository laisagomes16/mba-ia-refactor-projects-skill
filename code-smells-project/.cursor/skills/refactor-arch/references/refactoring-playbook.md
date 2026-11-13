# Refactoring playbook (Phase 3)

Execute only after explicit user confirmation. Preserve public contracts and behavior. Prefer incremental steps:

```text
Problem → create new abstraction → migrate consumers → remove old responsibility → tests → validate → continue
```

Prioritize CRITICAL → HIGH → MEDIUM → LOW. Do not force zero remaining findings.

Adapt examples to the **real** stack. Examples below use different languages on purpose; they are patterns, not copy-paste for every project.

---

## Transformation 1 — Fat Controller → Controller + Service

### Problem

Request handlers contain multi-step business rules.

### Before

```javascript
// Express
app.post('/orders', async (req, res) => {
  const items = req.body.items
  let total = 0
  for (const item of items) {
    const product = await db.query('SELECT * FROM products WHERE id = ?', [item.id])
    total += product.price * item.qty
  }
  if (total > 1000) total *= 0.9
  const order = await db.query('INSERT INTO orders (total) VALUES (?)', [total])
  res.json(order)
})
```

### After

```javascript
app.post('/orders', async (req, res) => {
  const order = await orderService.create(req.body.items)
  res.json(order)
})

// orderService.js
async function create(items) {
  const total = await pricing.quote(items)
  return orderRepository.insert(total)
}
```

### Why

HTTP mapping stays thin; quoting is testable without a server.

### When to Apply

Handlers with pricing, workflows, or multi-entity transactions.

### Risks

Moving code without extracting a seam can still leave SQL in the service. Continue with repository extraction if needed.

### Validation

Same status codes and JSON shape; existing tests; hit the endpoint if applicable.

---

## Transformation 2 — God Class → Separation of Responsibilities

### Problem

One type owns multiple domains and layers.

### Before

```python
class AppManager:
    def create_user(self, payload): ...
    def create_product(self, payload): ...
    def create_order(self, payload): ...
    def render_home(self): ...
```

### After

```python
# users/user_controller.py + user_service.py + user_model.py
# products/...
# orders/...
```

### Why

Independent change and testing per domain.

### When to Apply

Single module/class mixing several aggregates and HTTP.

### Risks

Big-bang split breaks imports. Extract one domain first.

### Validation

All previous routes still registered; boot; smoke endpoints per domain.

---

## Transformation 3 — Business Logic in Route → Controller/Service

### Problem

Route files or templates implement domain rules.

### Before

```php
// Laravel routes/web.php
Route::get('/checkout', function (Request $request) {
    $total = $request->cart->sum(fn ($i) => $i->price * $i->qty);
    if ($total > 100) { $total *= 0.95; }
    return view('checkout', compact('total'));
});
```

### After

```php
Route::get('/checkout', [CheckoutController::class, 'show']);

class CheckoutController {
    public function show(CheckoutService $checkout) {
        return view('checkout', ['total' => $checkout->total(auth()->user())]);
    }
}
```

### Why

Routes stay declarative; rules have a home.

### When to Apply

Closures in route files with calculations or SQL.

### Risks

Keep URL and view name unchanged.

### Validation

Render the same view/data; no contract change.

---

## Transformation 4 — Database Access in Controller → Repository/Model

### Problem

Controllers embed SQL or DbContext queries.

### Before

```csharp
[HttpGet("users/{id}")]
public async Task<IActionResult> Get(int id)
{
    var user = await _db.Database
        .SqlQuery($"SELECT * FROM Users WHERE Id = {id}")
        .FirstOrDefaultAsync();
    return Ok(user);
}
```

### After

```csharp
[HttpGet("users/{id}")]
public async Task<IActionResult> Get(int id)
{
    var user = await _users.FindByIdAsync(id);
    if (user is null) return NotFound();
    return Ok(user);
}
```

Use parameterized APIs in the repository (never interpolate ids into SQL).

### Why

Persistence is mockable; injection is easier to prevent in one place.

### When to Apply

SQL/ORM sessions leaking into controllers.

### Risks

N+1 if the repository is too chatty. Design query methods for use cases.

### Validation

Same HTTP codes; parameterized SQL; tests.

---

## Transformation 5 — Duplicated Logic → Shared Service/Domain Component

### Problem

The same rule exists in two handlers.

### Before

```go
func taxA(subtotal float64) float64 { return subtotal * 0.1 }
func taxB(subtotal float64) float64 { return subtotal * 0.1 }
```

### After

```go
func ApplyDefaultTax(subtotal float64) float64 { return subtotal * 0.1 }
```

Call `ApplyDefaultTax` from both HTTP handlers and reports.

### Why

Single rounding and rate.

### When to Apply

Copy-paste domain rules (especially money and authz).

### Risks

Unifying slightly different rules by accident. Compare tests/fixtures first.

### Validation

Both former paths produce the previously intended results (if they already differed, document the chosen behavior — prefer not changing business meaning).

---

## Transformation 6 — Global State → Dependency Injection

### Problem

Mutable globals share DB or user context.

### Before

```typescript
export const db: any = null
export function init(d: any) { (global as any).db = d }

export function listTasks() {
  return (global as any).db.all('SELECT * FROM tasks')
}
```

### After

```typescript
export class TaskRepository {
  constructor(private readonly db: Db) {}
  list() { return this.db.all('SELECT * FROM tasks') }
}

// composition root / NestJS module providers
```

### Why

Request isolation and test doubles.

### When to Apply

Module-level mutable stores, process globals, hidden singletons mutated per request.

### Risks

Over-injecting in tiny scripts. Compose at the edge (main/app factory).

### Validation

Boot still finds a connection; concurrent requests do not share user data.

---

## Transformation 7 — Unsafe SQL → Parameterized Query/ORM

### Problem

User input concatenated into SQL.

### Before

```python
cur.execute("SELECT * FROM users WHERE email = '" + email + "'")
```

### After

```python
cur.execute("SELECT * FROM users WHERE email = ?", (email,))
```

### Why

The driver sends data separately from code.

### When to Apply

Any interpolated SQL. CRITICAL path.

### Risks

Dynamic identifiers (ORDER BY column) still need allowlists, not parameters.

### Validation

Legitimate lookups work; do not add exploit PoCs. Prefer tests with quotes in input if tests exist.

---

## Transformation 8 — Missing Validation → Validator/DTO

### Problem

Raw body persisted without checks.

### Before

```java
@PostMapping("/users")
public User create(@RequestBody Map<String, Object> body) {
    User u = new User();
    u.setEmail((String) body.get("email"));
    u.setRole((String) body.get("role"));
    return repo.save(u);
}
```

### After

```java
public record CreateUserRequest(
    @Email @NotBlank String email
) {}

@PostMapping("/users")
public User create(@Valid @RequestBody CreateUserRequest req) {
    return users.create(req.email());
}
```

Do not take `role` from the client unless that is the existing contract; preserve behavior if the legacy API already accepted it, then constrain safely.

### Why

Invalid data fails at the edge.

### When to Apply

Open maps/dicts written to persistence.

### Risks

Stricter validation can break clients. Match previous implicit rules first, then tighten only unsafe fields (roles, IDs).

### Validation

Happy path unchanged; invalid payloads get 4xx instead of 500 when that does not contradict legacy clients — if legacy accepted garbage, document remaining MEDIUM.

---

## Transformation 9 — Deprecated API → Modern API

### Problem

Calls removed or deprecated APIs for the detected version.

### Before

```python
# Hypothetical: framework docs mark this removed in the project's version
app.before_first_request(initialize)
```

### After

```python
with app.app_context():
    initialize()
```

Only apply a replacement that is documented for **that** technology and version. If unknown:

```text
Modern Equivalent: Unable to determine safely
```

and leave a MEDIUM finding rather than guessing.

### Why

Survives upgrades.

### When to Apply

Proven deprecation for the pinned version.

### Risks

Wrong equivalent silently changes lifecycle (once vs every worker).

### Validation

Boot; lifecycle hooks still run as before.

---

## Transformation 10 — External Integration in Controller → Adapter/Service

### Problem

Controllers call HTTP/mail/payment SDKs.

### Before

```ruby
def create
  resp = Faraday.post(ENV.fetch("PAYMENTS_URL"), token: params[:token])
  @order.update!(paid: resp.success?)
  render json: @order
end
```

### After

```ruby
def create
  @order = Payments::Charge.call(order: @order, token: params[:token])
  render json: @order
end
```

`Payments::Charge` owns the Faraday client, timeouts, and error mapping.

### Why

Vendor changes stay in the adapter.

### When to Apply

SDK usage inside controllers/routes.

### Risks

Timeouts and error codes must map to the previous HTTP behavior.

### Validation

Same success/error payloads; if outbound cannot be called, `NOT VALIDATED` with reason or use existing tests/fakes.

---

## Transformation 11 — N+1 Query → Eager Loading/Batch Query

### Problem

Per-item queries in a loop.

### Before

```python
orders = session.query(Order).all()
for order in orders:
    order.items  # lazy SELECT per order
```

### After

```python
orders = session.query(Order).options(selectinload(Order.items)).all()
```

Or batch:

```sql
SELECT * FROM order_items WHERE order_id IN (...)
```

### Why

Constant round-trips vs linear growth.

### When to Apply

List endpoints, reports, serializers walking relations.

### Risks

Over-eager loading huge graphs. Load what the response needs.

### Validation

Same JSON; fewer queries if you can observe logs; response time not required if not measured.

---

## Transformation 12 — Hardcoded Configuration → Configuration/Environment

### Problem

Secrets and environment-specific URLs in source.

### Before

```dart
const apiKey = 'sk-live-example'; // never copy real secrets into reports or new samples
```

### After

```dart
final apiKey = Platform.environment['API_KEY'];
if (apiKey == null || apiKey.isEmpty) {
  throw StateError('API_KEY missing');
}
```

Use `.env.example` with empty placeholders, not real values. Do not print secrets in logs or audit reports.

### Why

Rotation and environment promotion without code edits.

### When to Apply

Any credential or environment URL in source (CRITICAL).

### Risks

App fails closed without env — provide README/example keys only as placeholders. Preserve previous default **only** if it was a non-secret (e.g. port).

### Validation

Boot with env set; boot without secret should fail clearly if that is safer than a hardcoded fallback.

---

## Transformation 13 — Inconsistent Errors → Error Middleware/Handler

### Problem

Each route invents error shapes.

### Before

```javascript
app.get('/a', (req, res) => { throw new Error('fail') })
app.get('/b', (req, res) => res.status(500).send('oops'))
```

### After

```javascript
app.use((err, req, res, next) => {
  const status = err.statusCode || 500
  res.status(status).json({ error: err.publicMessage || 'Internal error' })
})
```

Do not return stack traces to clients.

### Why

Clients and security both improve.

### When to Apply

MEDIUM findings on error handling; HIGH if traces leak.

### Risks

Changing error JSON is a contract change — keep previous shape if public API already documented.

### Validation

One known error path; no stack in body.

---

## Transformation 14 — Missing Authz → Middleware + Policy

### Problem

Sensitive routes unguarded.

### Before

```python
@app.delete("/users/<id>")
def delete_user(id):
    User.delete(id)
    return "", 204
```

### After

```python
@app.delete("/users/<id>")
@require_auth
def delete_user(id):
    users.delete_if_allowed(current_user, id)
    return "", 204
```

Preserve existing auth if it already existed (session, JWT, basic). Do not invent a new auth protocol that changes clients.

### Why

Default deny for mutations.

### When to Apply

Unauthenticated sensitive operations (CRITICAL/HIGH).

### Risks

Locking out legacy open APIs that were intentionally public. Confirm with README/tests/clients.

### Validation

Unauthorized request gets 401/403 as appropriate; authorized path unchanged.

---

### ⚠️ `@require_auth` alone is NOT sufficient for resource mutations

Authentication answers *who are you*. Authorization answers *may you do this*. Applying the
`After` snippet above to every endpoint closes FINDING-level "no authn" but **leaves privilege
escalation open**, because any self-registered account becomes a valid identity:

```text
POST /usuarios  (public self-registration, standard for a storefront)
  → creates a "cliente"-level account
  → POST /login → valid token
  → DELETE /produtos/<id>   ← guarded only by @require_auth
  → catalogue erased by an anonymous visitor
```

The audit still says `apagar catálogo`. That impact is **not resolved** — the refactor merely
replaced "no credential" with "any credential". Verify the impact sentence, not the decorator.

#### Required shape for every mutation

Classify **each mutating route** by *who legitimately owns the decision* and guard it explicitly.
`@require_auth` is the floor, never the ceiling:

| Route kind | Guard | Rationale |
|---|---|---|
| Destructive/shared resource (`DELETE /produtos/<id>`, `PUT /produtos/<id>`) | `@require_role(admin)` | A customer deleting the catalogue is never a legitimate flow |
| Read of any/all sensitive records (`GET /usuarios`, `GET /pedidos`) | `@require_role(admin)` | Cross-tenant data |
| Read/write of *own* records (`GET /pedidos/usuario/<id>`, order status by its owner) | `@require_auth` + owner check (`id == current_user.id`) | IDOR |
| Order lifecycle transitions (`PUT /pedidos/<id>/status`) | `@require_role(admin)` **or** owner-only transitions, stated explicitly | Business rule, must be written down |
| Self-registration (`POST /usuarios`) | public, and **must not** accept a privilege field (`tipo`, `role`) from the body | Otherwise the public endpoint mints admins and every role check is theatre |
| Admin surface (`/admin/*`) | `@require_role(admin)` + strong auth | Never "SQL livre" |

Rules that make this auditable:

1. **Mutations default to privileged.** If you cannot name who is allowed to call a mutation,
   the answer is `admin`, not "any authenticated user".
2. **A public endpoint that issues identities must be privilege-pinned.** Check the service:
   the role must be assigned server-side (e.g. `tipo="cliente"` hardcoded), never read from the
   request body. Also confirm the response has no privilege field the client can then resend.
3. **Role must come from persisted state, not from the token claim alone** when roles can change
   (reload the user row and read the current role). A token minted before a demotion must not
   keep admin rights.
4. **Deny by default in the framework, allow by exception.** If the stack supports it, install a
   global check that rejects unlisted routes (or assert at startup that every rule is guarded);
   a forgotten decorator is a silent vulnerability, not a failing test.
5. **Never trust a client-supplied role or owner id** for the authorization decision itself.

#### Self-registration closure test (mandatory for this transformation)

The exploit path is the acceptance test. It needs no privileged credentials:

```text
1. Anonymously POST the public registration endpoint with an unprivileged body.
2. Log in as that fresh account → token.
3. Attempt every mutating route identified in the audit's Impact sentence.
   Expected: 403 (not 200, not 401).
4. Repeat with a legacy account of the same low role → still 403.
5. Repeat the same routes with the admin → succeeds (authorized path unchanged).
```

If step 3 returns 200 for a mutation named in a CRITICAL/HIGH Impact, the finding is
**NOT RESOLVED** even when every route technically has `@require_auth`.

#### Validation

- Swap one credential at a time: no token → 401; low-role token → 403; admin → 200.
- Re-read the finding's **Impact** line and tick each clause with a concrete request/response.
- A mutation guarded only by authentication is reported as `PARTIALLY RESOLVED`, with the
  escalation path written out.

---

## Phase 3 validation checklist

Detect commands from the real project; never run incompatible tools.

| Check | If possible | If not |
|-------|-------------|--------|
| Build | Run the project’s build | Skip with reason |
| Tests | Run existing suite | `No automated tests detected.` |
| Boot | Start with the real entry command | `NOT VALIDATED` + reason |
| Endpoints | Discover from routes; exercise relevant ones | `NOT VALIDATED` + reason |
| Impact verification | One executed check per Impact clause of every CRITICAL/HIGH finding | `NOT VALIDATED` + reason; the finding stays `Remaining` |
| Privilege matrix | Each mutation as anonymous / fresh low-privilege / admin | `NOT VALIDATED` + reason |
| Re-audit | Recount severities BEFORE/AFTER | Required |

Never claim an endpoint works without testing it.

Never write `Resolved` for a CRITICAL/HIGH whose `Impact` line was not exercised clause by
clause. "The recommended fix is present in the diff" is not a verification.

Report remaining findings and why they stayed (optional quality, out of scope, tech limits). Then emit the Phase 3 completion block from `SKILL.md`.
