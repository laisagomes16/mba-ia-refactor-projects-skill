## Impact Verification (CRITICAL/HIGH) — rerun with hardened playbook

| Finding | Impact clause | Check performed | Result |
|---------|---------------|-----------------|--------|
| FINDING-001 | compromisso de segredos | `SECRET_KEY` lida de env; seed usa `hash_password`; `/health` sem `secret_key` | RESOLVED |
| FINDING-002 | injeção SQL | varredura de `execute(...)` com `+` de dados → nenhum (só `?` placeholders) | RESOLVED |
| FINDING-003 | SQL e destruição total via `/admin/query` | handler levanta 403; `/admin/*` exige admin | RESOLVED |
| FINDING-004 | **apagar catálogo** | anônimo `POST /usuarios` → `POST /login` → `DELETE /produtos/<id>` | **200 antes / 403 depois** |
| FINDING-004 | roubo de contas | cliente → `GET /usuarios` | **200 antes / 403 depois**; admin 200 |
| FINDING-004 | resetar o banco | cliente → `POST /admin/reset-db` | 403; sem token 401; admin 200 |
| FINDING-004 | alterar pedidos de qualquer usuário | cliente → `PUT /pedidos/1/status` | 403; sem token 401 |
| FINDING-004 | IDOR pedidos | A lê `GET /pedidos` (pedido próprio 4 sim, de B 5 não) | RESOLVED (escopo por dono) |
| FINDING-004 | auto-promoção no cadastro | `POST /usuarios` com `tipo=admin` → login | persiste `cliente`; 403 nas mutações |
| FINDING-004 | regressão do caminho legítimo | admin → mesmas rotas | 200/201 (delete, put, post, reset-db) |
| FINDING-005 | senhas/metadados expostos | serializers sem `senha`; `/health` só status+counts | RESOLVED |
| FINDING-006 | god controller | maior controller: 39 linhas (era 293) | RESOLVED |
| FINDING-009 | estado global da conexão | conexão request-scoped via `g`, sem `check_same_thread` | RESOLVED |
| FINDING-010 | acoplamento à infra | services sem `get_db`/`sqlite3` | RESOLVED |
| FINDING-011 | notificação no controller | `NotificationService` com `logging`, sem `print` | RESOLVED |
| FINDING-012 | N+1 | `_hydrate` com `IN (...)` + JOIN único | RESOLVED |
| FINDING-013 | PII em log | nenhum `print` de e-mail/senha/nome | RESOLVED |

`Resolved: 5 CRITICAL, 7 HIGH` — with the **only** code change being the authorization floor of
the catalogue mutations (`@require_auth` → `@require_admin` in `controllers/product_controller.py`).
Before that change the hardenend rule itself failed the rerun: FINDING-004 was `NOT RESOLVED`.

## What the rerun proved about the skill

1. The audit's Impact was right and the refactor was wrong — the exploit needed no admin token.
2. `@require_auth` on mutations is a **false resolution signal**; only the low-privilege
   identity test caught it.
3. `GET /pedidos` returning 200 to a client looked like a leak and was not (owner-scoped). The
   per-clause check separates "suspicious status code" from "actual data exposure" instead of
   trusting the status alone.
