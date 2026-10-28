Architecture Audit Report
1. Executive Summary
API de Task Manager em Python 3 / Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 sobre SQLite. A arquitetura é MVC parcial / híbrida: existe uma camada de Models real, mas a pasta services/ está vazia na prática e os três arquivos de routes/ funcionam simultaneamente como controller, service, repository e serializer. O risco geral é alto: credenciais e segredo de aplicação no código-fonte, hash de senha MD5, campo password exposto publicamente em 6 respostas HTTP, ausência total de autenticação/autorização nas 20 rotas, além de N+1, lógica de domínio duplicada em 5 pontos e código morto.

Total: 23 findings — 3 CRITICAL, 7 HIGH, 9 MEDIUM, 4 LOW. A Fase 3 é recomendada, de forma incremental, preservando todas as 22 rotas e os contratos de payload.

2. Detected Stack
Language: Python
Language version: unknown no projeto (sem pin); runtime local 3.13.5
Framework: Flask
Framework version: 3.0.0 (requirements.txt:1)
Runtime: Python (WSGI/desenvolvimento embutido)
Package manager: pip (requirements.txt; sem lockfile)
Database: SQLite (sqlite:///tasks.db, app.py:11)
ORM: Flask-SQLAlchemy 3.1.1 (requirements.txt:2), SQLAlchemy 2.x
Main libraries: flask-cors 4.0.0 (pin) — marshmallow, requests, python-dotenv declarados e não utilizados
Test system: not detected
Build system: not detected
Docker: not detected
External integrations: SMTP Gmail (services/notification_service.py:7-10) — não registrado nem invocado
3. Current Architecture
MVC parcial / híbrido. Os nomes de pasta sugerem camadas, mas o comportamento desmente:

Pasta	O que realmente é
models/	Model legítimo — entidades, persistência, invariantes. Porém sobrecarregado com serialização que vaza password.
services/	Pasta fachada: 1 arquivo, 0 imports em todo o projeto. Camada inexistente.
routes/	Controller + Service + Repository + Serializer acumulados. Toda query ORM, validação, regra de domínio e montagem de dicionário JSON vive aqui.
utils/helpers.py	Depósito de utilidades: já contém a validação de task pronta, mas é ignorado pelas rotas, que reimplementam inline.
raiz	app.py faz bootstrap + config inline + segredo + db.create_all() no import.
4. Architecture Flow

Actual:

HTTP → app.py (config/secret/create_all)
        └─ Blueprint (routes/*.py)
             ├── request.get_json / request.args        (HTTP)
             ├── validação inline                        (Validator)
             ├── regra de negócio (overdue, %, cascade)  (Service)
             ├── Task.query / db.session / query em loop (Repository)
             ├── dict montado à mão / to_dict()          (View/Serializer)
             └── jsonify + status                        (Response)
        └─ models/*.py  → SQLAlchemy + to_dict + MD5 + invariantes
        └─ services/notification_service.py → ÓRFÃO (0 imports)

Intended (technology-adapted):

HTTP → Route/Blueprint → Controller → Service/Use Case → Repository → Model → SQLite
                                          ↘ validators/ (DTO)
                                          ↘ serializers/ (View JSON)
Config/secrets → config.py + environment
Erros → handler centralizado
Authn/Authz → middleware/decorator

## 5. Severity Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 3 |
| HIGH | 7 |
| MEDIUM | 9 |
| LOW | 4 |

## 6. Findings

### FINDING-001 — [CRITICAL] Credenciais de SMTP hardcoded no código-fonte

- Category: Security
- File: `services/notification_service.py`
- Lines: 9-10
- Evidence: Hardcoded credential detected at `services/notification_service.py:10` (`self.email_password`); `email_user` literal na linha 9; host/porta literais nas linhas 7-8.
- Problem: Usuário e senha de conta de e-mail comitados no repositório.
- Impact: Vazamento do repositório equivale a vazamento da credencial; uso indevido da conta, risco de phishing a partir do domínio.
- MVC/SOLID Violation: Configuração fora de um limite de config/env (DIP — serviço acoplado a credenciais concretas).
- Recommended Fix: Mover para variáveis de ambiente / secret manager, sem ecoar o valor no relatório.
- Refactoring Strategy: `config.py` + `os.environ`; `NotificationService` recebe credenciais por injeção.

### FINDING-002 — [CRITICAL] Segredo de aplicação hardcoded

- Category: Security
- File: `app.py`
- Line: 13
- Evidence: Hardcoded credential detected at `app.py:13` — `SECRET_KEY` recebe um literal de 21 caracteres.
- Problem: Chave de assinatura de sessão fixa e pública no código.
- Impact: Qualquer pessoa com acesso ao repo pode forjar sessões/cookies assinados; rotação exige alteração de código.
- MVC/SOLID Violation: Configuração misturada ao bootstrap (sem camada de config).
- Recommended Fix: Ler de `FLASK_SECRET_KEY`/`SECRET_KEY` com fallback seguro (`secrets.token_hex`).
- Refactoring Strategy: Extrair `config.py` com classe `Config` e consumir em `create_app()`.

### FINDING-003 — [CRITICAL] Senha exposta em respostas da API (data exposure)

- Category: Security
- File: `models/user.py`
- Line: 21
- Evidence: `to_dict()` inclui a chave `'password'` com o hash. Esse `to_dict()` é retornado em `POST /users` (`user_routes.py:85-86`), `PUT /users/<id>` (`:129`), `GET /users/<id>` (`:33`), `POST /login` (`:209`) e é a base do `user` do relatório (`report_routes.py:138-142` usa campos explícitos, não `to_dict`).
- Problem: Hash de senha (MD5) sai em respostas públicas sem qualquer autenticação.
- Impact: Coleta massiva de hashes → quebra trivial offline (MD5 não salgado). Comprometimento de todas as contas.
- MVC/SOLID Violation: Model acumulando responsabilidade de serialização de API (View) sem política de campos.
- Recommended Fix: Serialização pública sem `password`; hash só acessível internamente.
- Refactoring Strategy: `serializers/user_serializer.py` com `to_public_dict()`, substituindo todos os consumidores.

### FINDING-004 — [CRITICAL] Hash de senha com MD5 sem salt

- Category: Security
- File: `models/user.py`
- Lines: 27-32
- Evidence: `hashlib.md5(pwd.encode()).hexdigest()` usado em `set_password` (linha 29) e `check_password` (linha 32); `hashlib` importado apenas para isso.
- Problem: Algoritmo criptograficamente quebrado, sem salt, sem fator de custo.
- Impact: Rainbow tables e GPU quebram qualquer senha em segundos; viola FINDING-003 amplificando o dano.
- MVC/SOLID Violation: Política de segurança embutida no Model sem abstração substituível (DIP).
- Recommended Fix: `werkzeug.security.generate_password_hash` / `check_password_hash` (já disponível como dependência transitiva do Flask).
- Refactoring Strategy: Migrar `set_password`/`check_password`; manter compatibilidade de login com rehash progressivo.

### FINDING-005 — [HIGH] `routes/task_routes.py` concentra Controller + Service + Repository + Serializer

- Category: Architecture / MVC / SRP
- File: `routes/task_routes.py`
- Lines: 1-299
- Evidence: Todas as 7 rotas de task; HTTP (`request`, `jsonify`), validação inline (linhas 89-124, 166-213), regra de negócio (`overdue` nas linhas 30-39 e 71-80), acesso a dados (`Task.query`, `User.query.get` em 42, `Category.query.get` em 51) e serialização manual (linhas 17-28) no mesmo arquivo. 299 linhas de 1.141 do projeto.
- Problem: Fat Controller / módulo-deus de domínio único.
- Impact: Impossível testar regra de `overdue` ou busca sem subir servidor e banco; qualquer mudança em task toca um arquivo que faz tudo.
- MVC/SOLID Violation: SRP severo; Controller absorve Model e Service.
- Recommended Fix: Extrair `TaskService` + `TaskRepository`; rota delega e responde.
- Refactoring Strategy: `controllers/task_controller.py` (fino) → `services/task_service.py` → `repositories/task_repository.py`.

### FINDING-006 — [HIGH] Regra de negócio e montagem de resposta em `report_routes.py`

- Category: MVC / SRP
- File: `routes/report_routes.py`
- Lines: 12-101
- Evidence: O handler `summary_report` (89 linhas) executa 12+ queries, calcula `overdue` em loop Python (33-43), `days_overdue` (42), janela `timedelta(days=7)` (45), produtividade por usuário com query por usuário (56) e monta o dicionário final (70-99).
- Problem: Fat Controller com agregação de relatório inteira dentro do handler HTTP.
- Impact: Relatório não reutilizável por job/CLI; impossível testar números sem request.
- MVC/SOLID Violation: SRP e OCP (novas métricas exigem editar o handler).
- Recommended Fix: `ReportService` com métodos de agregação; controller só delega.
- Refactoring Strategy: `services/report_service.py`; rotas passam a 3-5 linhas.

### FINDING-007 — [HIGH] Domínio de `Category` embutido no módulo de relatórios

- Category: Architecture / MVC
- File: `routes/report_routes.py`
- Lines: 157-223
- Evidence: CRUD completo de categorias (`GET`, `POST`, `PUT`, `DELETE /categories`) vive dentro do blueprint `reports` (linha 10), não em um controller de categorias.
- Problem: Coesão de módulo quebrada — recurso de domínio diferente no arquivo de relatórios.
- Impact: Descoberta e evolução do recurso ficam escondidas; blueprint de relatório passa a depender de escrita em `categories`.
- MVC/SOLID Violation: SRP; fronteira de agregado violada.
- Recommended Strategy: `controllers/category_controller.py` + blueprint próprio, mantendo as mesmas URLs.
- Refactoring Strategy: Mover handlers preservando paths e payloads; registrar novo blueprint em `app.py`.

### FINDING-008 — [HIGH] Ausência total de autenticação e autorização

- Category: Security
- File: `app.py`, `routes/user_routes.py`
- Lines: `app.py:18-28`, `user_routes.py:134-151`, `:210`
- Evidence: Nenhum decorator/middleware de auth em nenhuma das 22 rotas. `DELETE /users/<id>` (linha 135) apaga usuário e todas as suas tasks (`:140-142`) sem checagem. `login` (linha 185) retorna `'token': 'fake-jwt-token-' + str(user.id)` (linha 210) — token previsível e não verificável; nenhuma rota consome `Authorization`.
- Problem: Endpoints de escrita destrutiva e dados pessoais abertos; autenticação simulada.
- Impact: IDOR generalizado e destruição de dados por qualquer cliente; falsa sensação de segurança por existir "token".
- MVC/SOLID Violation: Preocupação transversal ausente na borda; política não centralizada.
- Recommended Fix: Middleware/decorator de authn + authz por papel (`role` já existe no Model), token assinado real (itsdangerous, já disponível via Flask).
- Refactoring Strategy: `middleware/auth.py` com `require_auth`/`require_admin`, aplicado rota a rota; preservar `/health` e `/` públicos. **Nota:** altera comportamento observável de acesso — decisão a alinhar antes da Fase 3.

### FINDING-009 — [HIGH] Cascata de exclusão manual sem transação única no controller

- Category: MVC / Data integrity
- File: `routes/user_routes.py`
- Lines: 140-142
- Evidence: `tasks = Task.query.filter_by(user_id=user_id).all()` seguido de `for t in tasks: db.session.delete(t)` antes de `db.session.delete(user)` (linha 145).
- Problem: Regra de integridade do agregado `User→Tasks` implementada como loop no handler; carrega todas as tasks em memória.
- Impact: Custo O(n) de objetos em memória para uma operação de banco; duplicação de política de exclusão em qualquer novo ponto de deleção.
- MVC/SOLID Violation: SRP — política de domínio no Controller.
- Recommended Fix: `ondelete='CASCADE'` na FK ou método de repositório dedicado.
- Refactoring Strategy: `UserService.delete_user()` em transação única; comportamento externo preservado.

### FINDING-010 — [HIGH] Model sobrecarregado com serialização que vaza dados + duplicação de `to_dict` nas rotas

- Category: MVC / Model Overload
- File: `models/task.py`, `routes/task_routes.py`, `routes/user_routes.py`
- Lines: `models/task.py:23-36`, `task_routes.py:17-28`, `user_routes.py:162-169`
- Evidence: `Task.to_dict()` (linhas 23-36) é reimplementado manualmente em `task_routes.py:17-28` e novamente, com subconjunto de campos, em `user_routes.py:162-169`. A serialização de `User` inclui `password` (FINDING-003).
- Problem: Duas representações divergentes do mesmo recurso + Model decidindo contrato de API.
- Impact: `GET /users/<id>/tasks` devolve payload diferente de `GET /tasks` para a mesma entidade — contrato inconsistente e bug latente para consumidores.
- MVC/SOLID Violation: SRP e consistência de contrato; View não isolada.
- Recommended Fix: Serializers dedicados por recurso, usados por todas as rotas.
- Refactoring Strategy: `serializers/task_serializer.py`, `serializers/user_serializer.py`, `serializers/category_serializer.py`.

### FINDING-011 — [HIGH] Lógica de "overdue" duplicada em 5 pontos + invariante `is_overdue` nunca usada

- Category: Quality / Duplicated Logic
- File: `task_routes.py`, `user_routes.py`, `report_routes.py`, `models/task.py`
- Lines: `task_routes.py:30-39`, `task_routes.py:71-80`, `user_routes.py:171-180`, `report_routes.py:33-43`, `report_routes.py:132-135`; definição em `models/task.py:50-60`
- Evidence: Bloco idêntico `due_date < utcnow()` + `status not in (done, cancelled)` copiado 5 vezes. `Task.is_overdue()` existe (linha 50) e tem **0 chamadas** no projeto.
- Problem: Regra de domínio triplicada na camada errada, com a versão correta órfã no Model.
- Impact: Divergência futura (ex.: adicionar status `archived` exige editar 5 lugares); testes não cobrem a regra em um só ponto.
- MVC/SOLID Violation: SRP (regra não mora em um lugar só); OCP.
- Recommended Fix: `Task.is_overdue()` como fonte única, consumida por serializers e relatórios.
- Refactoring Strategy: `serializers/task_serializer.py` e `report_service` passam a chamar o model.

### FINDING-012 — [MEDIUM] N+1 em `GET /tasks` (2 queries por task)

- Category: Performance
- File: `routes/task_routes.py`
- Lines: 41-57
- Evidence: Para cada `t` da lista, `User.query.get(t.user_id)` (linha 42) e `Category.query.get(t.category_id)` (linha 51). Lista sem paginação (`Task.query.all()`, linha 14).
- Problem: 1 + 2N queries; com 500 tasks → ~1001 queries.
- Impact: Latência e carga de DB crescendo linearmente com o volume; sem limite superior.
- MVC/SOLID Violation: API de repositório ingênua dentro do controller.
- Recommended Fix: `joinedload(Task.user)` / `joinedload(Task.category)` no repositório.
- Refactoring Strategy: `TaskRepository.list_with_relations()`.

### FINDING-013 — [MEDIUM] N+1 em `/categories`, `/reports/summary` e `user_count`

- Category: Performance
- File: `routes/report_routes.py`, `routes/user_routes.py`
- Lines: `report_routes.py:163`, `report_routes.py:56`, `user_routes.py:22`
- Evidence: `Task.query.filter_by(category_id=c.id).count()` dentro do loop de categorias (163); `Task.query.filter_by(user_id=u.id).all()` dentro do loop de usuários (56); `len(u.tasks)` por usuário em `GET /users` (22) dispara lazy load por linha.
- Problem: Queries por item em listas.
- Impact: Relatório faz 1 query por usuário + 1 por categoria, além das 15 de contagem.
- MVC/SOLID Violation: Agregação fora de um service/repository especializado.
- Recommended Fix: `GROUP BY` com `func.count` em uma única query por dimensão.
- Refactoring Strategy: `ReportRepository` com agregações SQL.

### FINDING-014 — [MEDIUM] `/tasks/stats` e `/reports/summary` carregam toda a tabela em memória

- Category: Performance
- File: `routes/task_routes.py`, `routes/report_routes.py`
- Lines: `task_routes.py:281-287`, `report_routes.py:30-43`
- Evidence: `all_tasks = Task.query.all()` seguido de loop Python para contar `overdue`, além de 5 contagens separadas (`task_routes.py:275-279`) e 9 em `report_routes.py:15-28`.
- Problem: Contagem de atrasadas e percentuais calculados em memória; 14 queries de contagem na mesma requisição.
- Impact: Memória O(n) e múltiplas varreduras completas por chamada de estatística.
- MVC/SOLID Violation: SRP — estatística de domínio no handler.
- Recommended Fix: `func.count` com filtros `due_date < now` e `status not in (...)`, ou agregação única.
- Refactoring Strategy: `TaskStatsService` / `ReportRepository.count_overdue()`.

### FINDING-015 — [MEDIUM] Ausência de paginação em todos os endpoints de listagem

- Category: Performance / API design
- File: `content` `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`
- Lines: `task_routes.py:14`, `:266`, `user_routes.py:12`, `report_routes.py:159`
- Evidence: `.all()` sem `limit/offset` em `/tasks`, `/tasks/search`, `/users`, `/categories`.
- Problem: Endpoints de coleção sem limite.
- Impact: Crescimento de payload e tempo de resposta sem teto; o próprio seed reconhece a dívida ("Adicionar paginação na API", `seed.py:70`).
- MVC/SOLID Violation: Contrato de listagem não modelado.
- Recommended Fix: `page`/`per_page` opcionais com defaults, preservando resposta atual quando ausentes.
- Refactoring Strategy: Helper de paginação no repository/controller; **não** alterar formato padrão da resposta.

### FINDING-016 — [MEDIUM] Validação duplicada e inconsistente entre rotas e `utils/helpers.py`

- Category: Quality / MVC
- File: `routes/task_routes.py`, `routes/user_routes.py`, `utils/helpers.py`
- Lines: `helpers.py:57-108`, `task_routes.py:89-144`, `user_routes.py:61`, `:106`
- Evidence: `process_task_data()` (helpers.py:57) já valida título/status/prioridade/data/tags — **0 usos**. As rotas reimplementam inline. Regex de e-mail duplicado: inline em `user_routes.py:61` e `:106`, e em `helpers.py:21` (`validate_email`, 0 usos). `POST /tasks` não faz `strip()` no título, embora `process_task_data` faça.
- Problem: Duas fontes de verdade para validação, já divergentes.
- Impact: Bypass de regra por caminho diferente; manutenção duplicada.
- MVC/SOLID Violation: SRP; Controller validando em vez de delegar a validator/DTO.
- Recommended Fix: `validators/` único consumido por todos os handlers.
- Refactoring Strategy: Consolidar em `validators/task_validator.py` e `validators/user_validator.py`.

### FINDING-017 — [MEDIUM] `PUT` de categoria e de usuário quebram com payload ausente/inválido

- Category: Quality / Missing Validation
- File: `routes/report_routes.py`, `routes/user_routes.py`
- Lines: `report_routes.py:196-197`, `user_routes.py:124-125`, `task_routes.py:209-213`
- Evidence: `update_category` chama `request.get_json()` (196) e acessa `'name' in data` (197) sem checar `None` → `TypeError`/500 se o body for vazio ou não-JSON. `update_user` atribui `active` sem checar tipo (`user.active = data['active']`, 125). `PUT /tasks` aceita `tags` string ou lista sem validar os itens (`task_routes.py:209-213`).
- Problem: Validação rasa ausente em caminhos de atualização.
- Impact: 500 em vez de 400; dados corrompidos (ex.: `active="false"` gravado como truthy).
- MVC/SOLID Violation: Controller pulou validação rasa.
- Recommended Fix: Validator/DTO com coerção de tipo por campo.
- Refactoring Strategy: `validators/category_validator.py`, `validators/user_validator.py`.

### FINDING-018 — [MEDIUM] Tratamento de erro inconsistente e 10 `except` genéricos silenciosos

- Category: Quality
- File: todos os `routes/*.py` + `utils/helpers.py`
- Lines: `task_routes.py:62`, `:137`, `:204`, `:236`; `user_routes.py:130`, `:149`; `report_routes.py:186`, `:207`, `:221`; `helpers.py:46`, `:49`, `:88`
- Evidence: 10 ocorrências de `except:` ou `except Exception` sem log/relançamento. `get_tasks` (linha 62) engole qualquer erro e devolve 500 sem detalhe. Mensagens de erro são strings PT-BR soltas, sem código/tipo.
- Problem: Sem handler central; erros de domínio não mapeados para HTTP.
- Impact: Diagnóstico difícil em produção; `GET /tasks` mascara falhas de serialização.
- MVC/SOLID Violation: Preocupação transversal não isolada.
- Recommended Fix: Exceções de domínio + `register_error_handlers(app)`.
- Refactoring Strategy: `errors.py` com `AppError` e handlers 400/404/409/500.

### FINDING-019 — [MEDIUM] `db.create_all()` como efeito colateral no import

- Category: Architecture / Configuration
- File: `app.py`
- Lines: 30-31
- Evidence: `with app.app_context(): db.create_all()` no nível do módulo, executado também quando `seed.py:2` importa `app`.
- Problem: Bootstrap com efeito colateral fora de uma factory; sem migrations.
- Impact: Qualquer import (teste, CLI, script) cria schema no banco configurado; impossível apontar `sqlite:///:memory:` em teste sem reescrever config; sem versionamento de schema.
- MVC/SOLID Violation: Configuração/bootstrap misturados.
- Recommended Fix: `create_app(config)` factory + inicialização explícita.
- Refactoring Strategy: `app.py` expõe `create_app()`; `seed.py` passa a construir a app.

### FINDING-020 — [MEDIUM] Debugger de desenvolvimento exposto em `0.0.0.0`

- Category: Security / Configuration
- File: `app.py`
- Line: 34
- Evidence: `app.run(debug=True, host='0.0.0.0', port=5000)` — sem leitura de env.
- Problem: Werkzeug debugger com console interativo acessível pela rede; stack traces expostos.
- Impact: Execução remota de código via console do debugger (Werkzeug PIN) em ambiente acessível.
- MVC/SOLID Violation: Configuração hardcoded.
- Recommended Fix: `debug` e `host` vindos de config/env, default seguro (`False`, `127.0.0.1`).
- Refactoring Strategy: `Config.DEBUG`/`Config.HOST` com `python-dotenv` (já na stack).

### FINDING-021 — [MEDIUM] Dependências e código mortos

- Category: Quality / Maintainability
- File: `requirements.txt`, `services/notification_service.py`, `utils/helpers.py`, imports
- Lines: `requirements.txt:4-6`, `notification_service.py:1-48`, `helpers.py:31-41`, `:52-55`, `:57-108`, `:110-116`
- Evidence: `marshmallow`, `requests`, `python-dotenv` declarados e **0 imports**. `NotificationService` com **0 imports** no projeto (`notification_service = 0`). Em `helpers.py`: `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `is_valid_color`, `process_task_data` têm 0 usos; `format_date`/`calculate_percentage` são importados por `report_routes.py:7` mas **nunca chamados** (todas as constantes `VALID_*`/`MAX_*` também 0 usos). `Task.validate_status`, `Task.validate_priority`, `User.is_admin` com 0 usos.
- Problem: Superfície morta com aparência de funcionalidade (notificação "existe" mas nunca é disparada).
- Impact: Falsa impressão de features entregues; dependências carregando superfície de ataque/instalação sem uso.
- MVC/SOLID Violation: Camada de serviço fictícia.
- Recommended Fix: Remover código e dependências mortos, ou conectar de fato (decisão de produto).
- Refactoring Strategy: Deletar módulos órfãos e imports em branco; manter apenas o que as rotas usam.

### FINDING-022 — [LOW] Imports não utilizados em todos os módulos

- Category: Quality
- File: `app.py`, `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`, `models/task.py`, `utils/helpers.py`
- Lines: `app.py:7`, `task_routes.py:7`, `user_routes.py:6`, `report_routes.py:8`, `models/task.py:3`, `helpers.py:3-7`
- Evidence: `app.py:7` importa `os, sys, json, datetime` (só `datetime` é usado); `task_routes.py:7` importa `json, os, sys, time` (nenhum usado); `user_routes.py:6` importa `json` (não usado); `report_routes.py:8` importa `json` (não usado); `models/task.py:3` importa `json` (não usado); `helpers.py:3-7` importa `os, sys, json, math` (não usados).
- Problem: Ruído de dependências internas.
- Impact: Leitura prejudicada; sugerem acoplamentos inexistentes.
- MVC/SOLID Violation: Não aplicável.
- Recommended Fix: Remover imports não usados.
- Refactoring Strategy: Limpeza mecânica, sem mudança de comportamento.

### FINDING-023 — [LOW] Código morto local e estilo booleano verboso

- Category: Quality / Readability
- File: `routes/task_routes.py`, `models/task.py`, `models/user.py`, `services/notification_service.py`
- Lines: `task_routes.py:69`; `task.py:38-48`, `:50-60`; `user.py:34-38`; `notification_service.py:6`, `:31-36`
- Evidence: `data = task.to_dict()` seguido de sobrescrita (69); `if x: return True else: return False` em `validate_status` (38-43), `validate_priority` (45-48), `is_overdue` (50-60), `is_admin` (34-38); `self.notifications = []` — lista de classe mutável usada para estado global (31-36).
- Problem: Verbosidade e estado mutável compartilhado latente.
- Impact: Legibilidade; se o serviço fosse ligado, `notifications` seria compartilhado entre requisições.
- MVC/SOLID Violation: SRP menor; risco de global mutable state.
- Recommended Fix: Retorno direto de expressões; estado por requisição/persistido.
- Refactoring Strategy: Simplificação mecânica durante a extração.

## 7. Security Findings

- **FINDING-001** — Credencial SMTP hardcoded (`services/notification_service.py:10`).
- **FINDING-002** — `SECRET_KEY` hardcoded (`app.py:13`).
- **FINDING-003** — Hash de senha exposto em respostas públicas (`models/user.py:21`).
- **FINDING-004** — MD5 sem salt para senha (`models/user.py:27-32`).
- **FINDING-008** — Nenhuma autenticação/autorização; token falso e previsível (`user_routes.py:210`).
- **FINDING-020** — Debugger exposto em `0.0.0.0`.
- **FINDING-018** — Erros genéricos mascaram falhas (disclosure/observabilidade).

Não detectado com a evidência atual: SQL injection (todas as queries usam o ORM; `LIKE` em `task_routes.py:252` é parametrizado), command injection, path traversal, SSRF, XSS (API JSON).

## 8. Performance Findings

- **FINDING-012** — N+1 de usuário e categoria em `GET /tasks` (`task_routes.py:41-57`).
- **FINDING-013** — N+1 em `/categories` (`report_routes.py:163`), `/reports/summary` (`:56`) e `GET /users` (`user_routes.py:22`).
- **FINDING-014** — Varredura full-table em memória para stats (`task_routes.py:281`, `report_routes.py:30`).
- **FINDING-015** — Ausência de paginação.
- **FINDING-009** — Loop de delete carregando todas as tasks do usuário.

## 9. Deprecated APIs

```text
Deprecated API: Query.get()
File: routes/task_routes.py (67, 117, 122, 158, 188, 195, 227, 42, 51)
      routes/user_routes.py (29, 94, 136, 155)
      routes/report_routes.py (105, 192, 213)
Line: ver acima (16 ocorrências)
Technology: SQLAlchemy / Flask-SQLAlchemy
Version: SQLAlchemy 2.x (instalado 2.0.43); Flask-SQLAlchemy 3.1.1 pinado
Reason: Query.get() é legado no SQLAlchemy 2.0; recomendado o novo estilo de execução por Session.
Modern Equivalent: db.session.get(Model, pk)
Migration Recommendation: Substituir mecanicamente; assinatura equivalente para PK.
Severity: MEDIUM

Deprecated API: datetime.datetime.utcnow()
File: models/task.py:15, 16, 52 | models/user.py:14 | models/category.py:11 |
      routes/task_routes.py:31, 72, 215, 285 | routes/user_routes.py:172 |
      routes/report_routes.py:35, 42, 45, 71, 133 | utils/helpers.py:38 |
      services/notification_service.py:35 | seed.py (6 ocorrências)
Line: ver acima
Technology: Python standard library (datetime)
Version: Python 3.12+ marca utcnow() como deprecated (DeprecationWarning)
Reason: Retorna datetime naive representando UTC, ambíguo e removível.
Modern Equivalent: datetime.now(timezone.utc)
Migration Recommendation: Padronizar em datetime.now(timezone.utc); atenção: muda o tipo
  para aware — normalizar antes de comparar com colunas existentes.
Severity: LOW (a versão-alvo do projeto não está pinada)

Deprecated API: Flask app.__version__ / flask.__version__
File: not present in application code
Technology: Flask
Version: 3.0.0 pin
Reason: detectado apenas no ambiente de análise (Warning do próprio Flask 3.1.1)
Modern Equivalent: importlib.metadata.version("flask")
Migration Recommendation: Não aplicável ao código do projeto.
Severity: LOW
10. Architectural Improvements
Introduzir config.py com Config lendo variáveis de ambiente; zero segredos no código.
Introduzir create_app(config) (app factory) e remover create_all() do import.
Dividir routes/ em controllers/ (finos) + services/ (regras) + repositories/ (queries).
Criar serializers/ como camada View JSON (sem password), usada por todos os handlers.
Criar validators/ único, absorvendo utils/helpers.process_task_data e o regex de e-mail.
Criar errors.py + handler central de exceções de domínio.
Criar middleware/auth.py com authn/authz por papel.
Movimentar o CRUD de categorias para controller próprio.
Consolidar stats/relatórios em services/ com agregações SQL (GROUP BY) e eager loading.
Eliminar services/notification_service.py órfão (ou conectá-lo explicitamente, com config).
11. Refactoring Plan
Ordem	Passo	Findings
1	config.py + segredos via env	001, 002, 020
2	Serializers sem password	003, 010
3	Hash seguro de senha (werkzeug)	004
4	create_app() factory, db.create_all() explícito	019
5	errors.py + exceções de domínio	018
6	Repositories (eager loading, GROUP BY, session.get)	012, 013, 014, 009, Deprecated#1
7	Services (task, user, category, report, stats)	005, 006, 007, 011, 009
8	Controllers finos + validators	016, 017
9	Remoção de código/deps mortos	021, 022, 023
10	Autenticação/autorização	008
11	Paginação opcional (contrato preservado)	015
A execução aguarda confirmação explícita do usuário. Dois itens exigem decisão de produto antes da Fase 3, pois alteram comportamento observável: FINDING-008 (rotas passariam a exigir token) e FINDING-015 (paginação). Sem isso, recomendo tratá-los como pendentes documentados.

12. Validation Plan
Dependências: pip install -r requirements.txt — necessário, pois flask_sqlalchemy não está importável no ambiente atual.
Seed: python seed.py (cria tasks.db; hoje ausente).
Build: not detected → SKIPPED.
Testes: No automated tests detected. — não serão inventados.
Boot: python app.py e checagem de GET /health.
Endpoints a exercitar: GET /, GET /health, GET /tasks, GET /tasks/1, GET /tasks/search?status=pending, GET /tasks/stats, GET /users, GET /users/1, GET /users/1/tasks, POST /login, GET /reports/summary, GET /reports/user/1, GET /categories, e POST/PUT/DELETE de task e categoria com payload controlado.
Será marcado NOT VALIDATED: envio de e-mail (SMTP externo com credencial inválida) e qualquer rota de auth que dependa de decisão de produto.