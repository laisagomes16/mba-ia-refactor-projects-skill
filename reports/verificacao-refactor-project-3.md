# Verificação da Refatoração — task-manager-api (audit-project-3)

Método: leitura de todos os módulos + scripts de verificação com `TestConfig`
(`sqlite:///:memory:`), `app.test_client()` e listener `before_cursor_execute` para contar queries.
Envio de e-mail não exercitado (a auditoria já previa `NOT VALIDATED` para SMTP).

## Resultado por finding

| # | Sev. | Item | Status | Evidência verificada |
|---|---|---|---|---|
| 001 | CRITICAL | SMTP hardcoded | RESOLVIDO | `notification_service.py` lê `current_app.config['SMTP_*']`; `config.py` usa `os.environ` |
| 002 | CRITICAL | `SECRET_KEY` hardcoded | RESOLVIDO | `app.py` sem literal; `Config.SECRET_KEY` = `FLASK_SECRET_KEY`/`SECRET_KEY` ou `os.urandom(32).hex()` |
| 003 | CRITICAL | `password` exposto | RESOLVIDO | `serialize_user()` sem `password`; 5 respostas testadas (`GET/PUT/POST /users`, `GET /users/<id>`, `/login`) → 0 vazamentos |
| 004 | CRITICAL | MD5 sem salt | RESOLVIDO | `set_password` → `generate_password_hash` (PBKDF2); conta MD5 legada autenticou (200) e foi rehasheada no 1º login |
| 005 | HIGH | `task_routes.py` módulo-deus | RESOLVIDO | 56 linhas (era 299), sem `query`/`db.session`; delega a `TaskService` |
| 006 | HIGH | Regra no handler de relatório | RESOLVIDO | `report_routes.py` = 21 linhas; agregação em `services/report_service.py` |
| 007 | HIGH | `Category` em relatórios | RESOLVIDO | `routes/category_routes.py` com `category_bp` próprio, registrado em `create_app()` |
| 008 | HIGH | Sem authn/authz | RESOLVIDO | sem token → 401; `fake-jwt-token-1` → 401; token adulterado → 401; usuário comum deletando outro → 403; admin → 200; `/` e `/health` → 200 |
| 009 | HIGH | Cascade de delete em loop | RESOLVIDO | `DELETE /users/<id>` emite `DELETE FROM tasks WHERE user_id = ?` (set-based, sem `SELECT ... FROM tasks` prévio) |
| 010 | HIGH | Model sobrecarregado | RESOLVIDO | `serializers.py` único; nenhum `to_dict` nos models |
| 011 | HIGH | `overdue` duplicado 5x | RESOLVIDO | `Task.is_overdue()` chamado 6x; expressão `due_date < utcnow()` só na fonte única (`models/task.py`) e num filtro SQL do repositório |
| 012 | MEDIUM | N+1 em `GET /tasks` | RESOLVIDO | `joinedload(Task.user/Task.category)` → **2 queries** (antes 1+2N) |
| 013 | MEDIUM | N+1 em `/categories`, `/reports/summary`, `GET /users` | **RESOLVIDO** (corrigido) | `/categories` = 2 queries; `GET /users` usa `UserRepository.task_counts_by_user()` (`GROUP BY user_id`) → **0 SELECTs de tasks** (antes 5 lazy loads para 5 usuários); `/reports/summary` usa `count_by_user_status()` (`GROUP BY user_id, status`) — produtos com 1 SELECT por usuário |
| 014 | MEDIUM | Full-table em memória nas stats | **RESOLVIDO** (corrigido) | `/tasks/stats` usa `count_overdue()` (agregação escalar) → **0 SELECTs de tasks**; `/reports/summary` agrega status/prioridade em SQL e a única consulta de tasks é a projeção `id, title, due_date` das atrasadas (3 colunas, sem `joinedload`; antes 11 colunas × N linhas) |
| 015 | MEDIUM | Paginação | **RESOLVIDO** (opcional/aditivo) | `page`/`per_page` aceitos em `/tasks`, `/tasks/search`, `/users`, `/users/<id>/tasks` e `/categories`; sem os parâmetros a resposta continua **array** (contrato preservado); com eles → `{items, page, per_page, total, pages}`; `page=0`/`per_page=abc`/`per_page=101` → 400; 1 query paginada (`LIMIT/OFFSET`) + 1 `COUNT` |
| 016 | MEDIUM | Validação duplicada | RESOLVIDO | regex de e-mail definido 1x (`EMAIL_PATTERN`); validações em `services/*_service.py` como fonte única |
| 017 | MEDIUM | `PUT` quebra com payload inválido | RESOLVIDO | `PUT /categories` com corpo não-JSON → 400 (era 500); sem corpo → 400; `PUT /users {}` → 400 |
| 018 | MEDIUM | `except` silenciosos | RESOLVIDO | `errors.py` + `error_handlers.py`; 0 `except` genérico fora do handler central |
| 019 | MEDIUM | `create_all()` no import | RESOLVIDO | `create_app()` factory + `init_database(app)` explícito |
| 020 | MEDIUM | Debugger exposto | **RESOLVIDO** (corrigido) | `debug` vem de `FLASK_DEBUG` (default `False`); `HOST` default agora é `127.0.0.1` (loopback), sobrescrevível por `TASK_MANAGER_HOST`; `.env.example` e README atualizados |
| 021 | MEDIUM | Dependências/código mortos | **RESOLVIDO** (corrigido) | `requirements.txt` reduzido a `flask`, `flask-sqlalchemy`, `flask-cors` (`marshmallow`/`requests`/`python-dotenv` removidos); `NotificationService` agora é **invocado de fato** por `TaskService` na atribuição/reatribuição de task, com notificador injetável (`set_notifier`) e envio best-effort |
| 022 | LOW | Imports não usados | RESOLVIDO | varredura de imports → nenhum sobrando |
| 023 | LOW | Código morto / booleano verboso | RESOLVIDO | sem `if x: return True else: return False`; `notifications = []` removido |

## Deprecated APIs

| API | Status |
|---|---|
| `Query.get()` (16 ocorrências) | RESOLVIDO — uso de `db.session.get(Model, pk)` |
| `datetime.utcnow()` | RESOLVIDO — `utils/helpers.utcnow()` usa `datetime.now(timezone.utc)` normalizado para naive-UTC |

## Resumo

- **CRITICAL: 4/4 resolvidos**
- **HIGH: 7/7 resolvidos**
- **MEDIUM: 9/9 resolvidos**
- **LOW: 2/2 resolvidos**

**Resposta objetiva: sim — todos os 23 findings estão resolvidos.**
Os 4 CRITICAL e os 7 HIGH já estavam fechados na refatoração; os 9 MEDIUM foram fechados
nas rodadas de correção:

1. **FINDING-013** — `GET /users` deixou de fazer `len(user.tasks)`: o controller usa
   `UserService.task_counts()` → `UserRepository.task_counts_by_user()`
   (`SELECT user_id, COUNT(*) FROM tasks GROUP BY user_id`). Medido: **0 SELECTs de tasks** para
   listar os usuários (antes: 1 por usuário). A produtividade de `/reports/summary` também passou
   a usar `count_by_user_status()`.
2. **FINDING-014** — `/tasks/stats` usa `TaskRepository.count_overdue()` (agregação escalar) e
   `/reports/summary` agrega status/prioridade em SQL; a única leitura de tasks é a projeção
   `id, title, due_date` das atrasadas (necessária para `days_overdue`), sem `joinedload`.
   `Query.count()` foi trocado por `SELECT count(...)` escalar (o `count()` do SQLAlchemy 2.0
   envolve um `count(*) FROM (SELECT ...)`).
3. **FINDING-015** — paginação **opcional e aditiva**: `?page=&per_page=` nos endpoints de
   listagem; sem os parâmetros a resposta continua sendo um array (nenhum cliente quebra);
   com os parâmetros devolve `{items, page, per_page, total, pages}`. Valores inválidos → 400.
4. **FINDING-020** — `HOST` default passou a `127.0.0.1` (loopback).
5. **FINDING-021** — dependências mortas removidas do `requirements.txt` e `NotificationService`
   conectado ao fluxo real (`POST /tasks` com `user_id` e mudança de `user_id` em `PUT /tasks/<id>`).

## Notas de execução

- Ambiente: Python 3.13.5, Flask 3.0.0, Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.0.43, pytest 8.3.4.
- Todos os módulos compilam (`python -m py_compile`) e a app sobe com `create_app(TestConfig)`.
- Queries medidas por endpoint (após as correções, com 5 usuários / 10 tasks):
  `/users` 3 (só `users` + agregação `GROUP BY`; antes 7), `/reports/summary` 10
  (nenhuma entidade de task carregada), `/tasks/stats` 3, `/categories` 2, `/tasks` 2;
  `/tasks?page=2&per_page=3` = 1 `LIMIT/OFFSET` + 1 `COUNT`.
- Suíte de regressão permanente em `task-manager-api/test/` (`python -m pytest test -q`):
  **17 testes, todos passando**; validado que o teste de N+1 falha se `len(user.tasks)` voltar.
- Scripts temporários usados na verificação foram removidos do projeto.
