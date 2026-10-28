# **Architecture Audit Report**

## **1. Executive Summary**

A API é Python/Flask 3.1.1 com SQLite (`loja.db`), CORS e SQL cru, sem ORM, testes, Docker ou arquivos de ambiente. A arquitetura é **MVC parcial híbrida com monólito não estruturado**: existem `app.py`, `controllers.py` e `models.py`, mas rotas executam SQL, controllers misturam validação, regras, I/O e persistência, e `models.py` concentra vários agregados. O risco geral é **alto**: injeção SQL, SQL arbitrário, ausência de autenticação, segredos no código e exposição de senhas. **23 findings** (5 CRITICAL, 7 HIGH, 8 MEDIUM, 3 LOW). A Fase 3 é recomendada, de forma incremental, **após confirmação explícita**.

## **2. Detected Stack**

- Language: Python
- Language version: unknown
- Framework: Flask
- Framework version: 3.1.1
- Runtime: not detected (execução via `python app.py`)
- Package manager: pip (`requirements.txt`; sem lockfile)
- Database: SQLite (`loja.db`)
- ORM: not detected (sqlite3)
- Main libraries: flask==3.1.1, flask-cors==5.0.1; sqlite3 (stdlib)
- Test system: not detected
- Build system: not detected
- Docker: not detected
- External integrations: not detected (notificações apenas via `print`)

## **3. Current Architecture**

**Híbrido: MVC parcial + monólito não estruturado.**

- `app.py`: composition root, rotas, duas handlers com SQL (`/admin/reset-db`, `/admin/query`).
- `controllers.py`: HTTP, validação, regras, JSON, prints de notificação e SQL no `health_check`.
- `models.py`: acesso a dados de produtos, usuários, pedidos e relatório, com regras de estoque/total/desconto e montagem de dicts.
- `database.py`: singleton global, DDL, seed.

Não há services, repositories, validators, middleware, DTOs, jobs nem views/templates. Os nomes dos módulos **não** correspondem a camadas corretas.

## **4. Architecture Flow**

Actual:

HTTP (app.py add_url_rule / @app.route)

  → controllers.py (validação, regras, JSON, print, SQL em health_check)

  → models.py (SQL concatenado, regras de pedido/relatório, dicts)

  → database.get_db() (global + schema + seed)

Atalhos:

  app.py /admin/* → sqlite3 direto

  controllers.health_check → sqlite3 direto

Intended (technology-adapted Flask):

Route / blueprint

  → Controller (request raso + resposta)

  → Service / use case (pedido, login, relatório)

  → Repository / model (SQL parametrizado)

  → SQLite

Config via environment; authn/authz no limite HTTP; adapter de notificação fora do controller.

## **5. Severity Summary**

| **Severity** | **Count** |
| ------------ | --------- |
| CRITICAL     | 5         |
| HIGH         | 7         |
| MEDIUM       | 8         |
| LOW          | 3         |

## **6. Findings**

### **FINDING-001 — [CRITICAL] Segredos e credenciais hardcoded**

- Category: Security
- File: app.py; database.py; controllers.py
- Line: app.py:7; database.py:75-82; controllers.py:289
- Evidence: `SECRET_KEY` literal em config; senhas em texto no seed de usuários; o mesmo valor de `SECRET_KEY` é reenviado no JSON de `/health`.
- Problem: Credenciais e chave de sessão versionadas no código e repetidas na API.
- Impact: Compromisso do repositório ou de `/health` equivale a compromisso da aplicação e das contas seed.
- MVC/SOLID Violation: Configuração fora de um limite de configuração; não é SOLID em si.
- Recommended Fix: Variáveis de ambiente / secret manager; nunca devolver segredos em respostas; não versionar senhas reais (nem de seed de demo em texto, se o código for compartilhado).
- Refactoring Strategy: Hardcoded Configuration → Configuration/Environment.

### **FINDING-002 — [CRITICAL] SQL montado por concatenação (injeção)**

- Category: Security
- File: models.py
- Lines: 28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-166, 174, 188, 192, 221, 224, 279-281, 289-299
- Evidence: `cursor.execute` recebe SQL com `+ str(...)` e concatenação de `nome`, `descricao`, `email`, `senha`, `termo`, `categoria`, `novo_status` e IDs. Esses valores chegam de `request.get_json()` / `request.args` em `controllers.py` (ex.: busca `q`, login, criar produto/usuário/pedido).
- Problem: Entrada não confiável entra na string SQL.
- Impact: Leitura/alteração do banco conforme o motor permitir; quebra de autenticação no login SQL.
- MVC/SOLID Violation: Persistência insegura na camada de “model”.
- Recommended Fix: Placeholders `?` / `executemany` (já usados no seed em `database.py:70-73`).
- Refactoring Strategy: Unsafe SQL → Parameterized Query.

### **FINDING-003 — [CRITICAL] Endpoint de SQL arbitrário sem controle de acesso**

- Category: Security
- File: app.py
- Lines: 59-78
- Evidence: `POST /admin/query` lê `dados.get("sql")` e chama `cursor.execute(query)`. SELECT devolve linhas; qualquer outro SQL faz `commit`. Sem autenticação no handler.
- Problem: A API executa SQL escolhido pelo cliente.
- Impact: Leitura e destruição total dos dados; bypass de qualquer regra de negócio.
- MVC/SOLID Violation: SQL e operação administrativa na rota; ausência de policy.
- Recommended Fix: Remover o endpoint em produção ou exigir auth forte + allowlist; nunca executar SQL cru do body.
- Refactoring Strategy: eliminar a superfície; operações admin via use cases explícitos.

### **FINDING-004 — [CRITICAL] Ausência de autenticação e autorização**

- Category: Security
- File: app.py; controllers.py
- Line: app.py:11-30, 47-57; controllers.py:167-186 (login não estabelece sessão/token usado depois)
- Evidence: Não há middleware, decorator, sessão Flask, JWT ou checagem de `tipo`. `login` só devolve JSON. `POST /admin/reset-db`, `DELETE /produtos/<id>`, `GET /usuarios`, `GET /pedidos`, `PUT /pedidos/<id>/status` e `GET /pedidos/usuario/<usuario_id>` são alcançáveis sem identidade. Não há checagem de dono do pedido (IDOR).
- Problem: Dados e mutações sensíveis são públicos na rede em que o servidor escuta.
- Impact: Roubo de contas (senhas no GET), apagar catálogo, resetar o banco, alterar pedidos de qualquer usuário.
- MVC/SOLID Violation: Concern transversal ausente na borda HTTP.
- Recommended Fix: Authn no login (sessão/token); authz por rota e por recurso; `/admin/*` restrito.
- Refactoring Strategy: middleware/decorators + checagens no service.

### **FINDING-005 — [CRITICAL] Exposição de senhas e metadados internos na API**

- Category: Security
- File: models.py; controllers.py
- Line: models.py:72-87, 89-103; controllers.py:128-132, 264-290
- Evidence: `get_todos_usuarios` / `get_usuario_por_id` incluem `"senha"`. `listar_usuarios` devolve esse dict. `health_check` inclui `secret_key`, `debug`, `db_path`, `ambiente`: `"producao"`. Senhas no banco estão em texto (`database.py` INSERT de `senha`).
- Problem: Hash inexistente; listagem e health vazam segredos e PII.
- Impact: Qualquer cliente de `GET /usuarios` ou `/health` obtém credenciais e configuração.
- MVC/SOLID Violation: Serialização de persistência crua como “view” JSON; health mistura infra e segredo.
- Recommended Fix: Hash de senha; DTO sem `senha`; health só com status, sem segredos nem path.
- Refactoring Strategy: serializer/DTO; nunca mapear coluna `senha` para JSON.

### **FINDING-006 — [HIGH] God Controller / Fat Controller**

- Category: Architecture / MVC / SRP
- File: controllers.py
- Lines: 1-293 (ex.: 24-62, 188-220, 237-255, 264-292)
- Evidence: Um módulo trata produtos, usuários, login, pedidos, relatório e health. Handlers validam domínio (categorias, estoque, status), disparam “e-mail/SMS/push” via `print`, e `health_check` executa SQL (`SELECT COUNT(*)`).
- Problem: HTTP, regras, persistência pontual e side effects no mesmo módulo.
- Impact: Qualquer mudança de regra exige editar o controller; testes exigem Flask.
- MVC/SOLID Violation: SRP; Controller absorve Model/service; DIP (SQL/get_db no health).
- Recommended Fix: Controllers finos; services por caso de uso; health só ping.
- Refactoring Strategy: Fat Controller → Controller + Service.

### **FINDING-007 — [HIGH] Model Overload**

- Category: MVC / SRP
- File: models.py
- Lines: 1-315
- Evidence: O mesmo módulo persiste produtos, usuários, pedidos e itens, calcula totais/estoque, aplica faixas de desconto no relatório (`256-262`) e monta grafos pedido→itens→nome do produto.
- Problem: Persistência, workflow de pedido e política de desconto no mesmo arquivo “model”.
- Impact: Relatório e checkout não evoluem isolados; SQL e regra se misturam.
- MVC/SOLID Violation: SRP; Model como service oculto.
- Recommended Fix: Repositórios por agregado; serviço de pedido e de relatório.
- Refactoring Strategy: God Class / Model split.

### **FINDING-008 — [HIGH] SQL e destruição de dados na camada de rota**

- Category: MVC
- File: app.py
- Lines: 47-78
- Evidence: `reset_database` e `executar_query` usam `get_db()` e `cursor.execute` no próprio `@app.route`, fora de `controllers.py`.
- Problem: Rotas concentram infraestrutura e operação de banco.
- Impact: Admin acoplado ao Flask app object; difícil reusar ou testar a policy.
- MVC/SOLID Violation: Business/infra na rota; SRP.
- Recommended Fix: Mover para controller admin + service; não SQL no registro de rotas.
- Refactoring Strategy: Business Logic in Route → Controller/Service.

### **FINDING-009 — [HIGH] Estado global mutável da conexão SQLite**

- Category: Architecture / Testability
- File: database.py
- Lines: 4-10, 86
- Evidence: `db_connection = None` no módulo; `global db_connection`; `sqlite3.connect(..., check_same_thread=False)` compartilhado por todas as requests (`app.run` no Flask é threaded em debug).
- Problem: Ciclo de vida da conexão e escritas concorrentes não são por request.
- Impact: Risco de corrupção/erros SQLite; testes e requests se interferem.
- MVC/SOLID Violation: DIP; dono do lifecycle oculto.
- Recommended Fix: Conexão por request (`g`) ou pool adequado; não `check_same_thread=False` sem serialização.
- Refactoring Strategy: Global State → DI / request-scoped connection.

### **FINDING-010 — [HIGH] Acoplamento rígido à infraestrutura**

- Category: Architecture / DIP
- File: controllers.py; models.py
- Line: controllers.py:1-3, 266; models.py:1, 5
- Evidence: Controllers importam `models` e `get_db` concretos. Toda função em `models.py` chama `get_db()` internamente. Não há injeção de repositório.
- Problem: Regras não são testáveis sem SQLite.
- Impact: Qualquer troca de banco ou fake exige reescrever módulos.
- MVC/SOLID Violation: DIP; camadas colapsadas.
- Recommended Fix: Services recebem repositório; composition root em `app.py`.
- Refactoring Strategy: Tight Coupling → inject repository.

### **FINDING-011 — [HIGH] Efeitos colaterais de notificação no controller**

- Category: MVC / SRP
- File: controllers.py
- Lines: 208-210, 247-250
- Evidence: Após criar pedido, três `print` de e-mail/SMS/push. Em mudança de status, `print` de notificação; no cancelamento o texto fala em devolver estoque, mas só `models.atualizar_status_pedido` é chamado.
- Problem: Orquestração de notificações (e regra implícita de estoque) vive no HTTP.
- Impact: Não há adapter testável; cancelamento não devolve estoque apesar da mensagem.
- MVC/SOLID Violation: SRP; side effects deveriam ser adapter/service.
- Recommended Fix: Serviço de pedido + porta de notificação; transação de estoque no use case de status.
- Refactoring Strategy: External Integration in Controller → Adapter/Service (mesmo com stub).

### **FINDING-012 — [HIGH] N+1 e I/O em loop em listagens e criação de pedido**

- Category: Performance
- File: models.py
- Lines: 139-166, 171-201, 203-233
- Evidence: `get_pedidos_usuario` / `get_todos_pedidos`: para cada pedido, `SELECT * FROM itens_pedido`; para cada item, `SELECT nome FROM produtos`. `GET /pedidos` lista todos. `criar_pedido`: um `SELECT *` por item, depois de novo `SELECT preco` e `UPDATE` por item.
- Problem: Consultas crescem com N pedidos × M itens.
- Impact: Latência e carga no SQLite em listagem global e checkout.
- MVC/SOLID Violation: API de persistência ingênua.
- Recommended Fix: JOIN / `IN (...)`; um SELECT de produtos do pedido; atualizar estoque em lote quando possível.
- Refactoring Strategy: N+1 → Eager Loading/Batch.

### **FINDING-013 — [HIGH] Dados sensíveis em logs (**`print`**)**

- Category: Security
- File: controllers.py
- Lines: 161, 179-182
- Evidence: `print("Usuário criado: " + email)`; login sucesso/falha imprime o e-mail.
- Problem: PII de autenticação vai para stdout.
- Impact: Logs viram fonte de enumeração de contas.
- MVC/SOLID Violation: Logging sem política.
- Recommended Fix: Logger estruturado; não logar e-mail em falha de senha (ou mascarar).
- Refactoring Strategy: redact; allowlist de campos.

### **FINDING-014 — [MEDIUM] Validação de produto duplicada**

- Category: Quality / SRP
- File: controllers.py
- Lines: 28-54 e 72-90
- Evidence: Blocos quase iguais de campos obrigatórios, preço/estoque ≥ 0; `criar_produto` ainda valida tamanho do nome e categoria; `atualizar_produto` não replica tamanho/categoria da mesma forma.
- Problem: Regras divergem entre POST e PUT.
- Impact: Atualização aceita nome curto ou categoria não validada da mesma lista.
- MVC/SOLID Violation: SRP da regra; OCP difícil.
- Recommended Fix: Validador/DTO único de produto.
- Refactoring Strategy: Duplicated Logic → Shared Service/Validator.

### **FINDING-015 — [MEDIUM] Validação incompleta na borda**

- Category: Quality / Security
- File: controllers.py
- Lines: 167-171, 188-201, 237-245
- Evidence: `login` chama `dados.get` sem garantir JSON; `criar_pedido` não valida schema de cada item (`produto_id`, `quantidade`); `atualizar_status_pedido` não verifica se o pedido existe (update SQL mesmo assim). Sem unique de e-mail no schema (`database.py:27-34`).
- Problem: Entrada malformada vira 500 ou estado inconsistente.
- Impact: Exceções vazadas; pedidos órfãos de status; e-mails duplicados possíveis.
- MVC/SOLID Violation: Validação rasa ausente/incompleta.
- Recommended Fix: Schema na borda; 404 se pedido inexistente; UNIQUE email.
- Refactoring Strategy: Missing Validation → Validator/DTO.

### **FINDING-016 — [MEDIUM] Tratamento de erro inconsistente e vazamento de internals**

- Category: Quality / Security
- File: controllers.py; app.py
- Line: padrão `except Exception as e` + `str(e)` (ex.: controllers.py:10-12, 219-220; app.py:77-78)
- Evidence: Falhas devolvem a mensagem da exceção ao cliente. Não há error handler Flask central.
- Problem: Detalhe de SQL/Python vaza; clientes não têm contrato único.
- Impact: Information disclosure; DX irregular.
- MVC/SOLID Violation: Concern transversal não isolado.
- Recommended Fix: Handler global; mensagens genéricas ao cliente; log interno.
- Refactoring Strategy: central error mapping.

### **FINDING-017 — [MEDIUM] Listagens sem paginação**

- Category: Performance
- File: controllers.py; models.py
- Line: controllers.py:5-9, 128-132, 229-233; models.py `SELECT *` sem LIMIT (ex.: 7, 75, 205)
- Evidence: `GET /produtos`, `/usuarios`, `/pedidos` carregam todas as linhas e ainda hidratam itens (pedidos).
- Problem: Resposta e memória crescem com a tabela.
- Impact: Degradação em volume real (agravado pelo N+1).
- MVC/SOLID Violation: Nenhum direto; repositório sem cursor/página.
- Recommended Fix: `limit`/`offset` ou cursor; default conservador.
- Refactoring Strategy: pagination no repository.

### **FINDING-018 — [MEDIUM] DEBUG ligado e bind em todas as interfaces**

- Category: Security
- File: app.py
- Lines: 8, 88
- Evidence: `app.config["DEBUG"] = True`; `app.run(host="0.0.0.0", port=5000, debug=True)`. `health_check` declara `"ambiente": "producao"` com `"debug": True`.
- Problem: Debugger e superfícies extras em processo escutando em todas as interfaces.
- Impact: Superfície de ataque maior se o host for alcançável.
- MVC/SOLID Violation: Config hardcoded.
- Recommended Fix: DEBUG só via env; bind localhost em dev.
- Refactoring Strategy: Configuration/Environment.

### **FINDING-019 — [MEDIUM] CORS irrestrito**

- Category: Security
- File: app.py
- Line: 9
- Evidence: `CORS(app)` sem `origins` (padrão flask-cors: qualquer origem).
- Problem: Browsers podem chamar a API a partir de qualquer site.
- Impact: Com FINDING-004, CSRF/cross-origin em ações destrutivas no browser.
- MVC/SOLID Violation: Nenhum.
- Recommended Fix: Allowlist de origens.
- Refactoring Strategy: config CORS explícita.

### **FINDING-020 — [MEDIUM] Lógica duplicada de hidratação de pedidos**

- Category: Quality / SRP
- File: models.py
- Lines: 171-201 e 203-233
- Evidence: Dois blocos quase idênticos montando pedido + itens + nome do produto; diferem só no `WHERE` inicial.
- Problem: Correção de N+1 precisa ser feita duas vezes.
- Impact: Drift entre “meus pedidos” e “todos os pedidos”.
- MVC/SOLID Violation: SRP da montagem do agregado.
- Recommended Fix: Uma função que hidrata uma lista de pedidos.
- Refactoring Strategy: Duplicated Logic → Shared Service.

### **FINDING-021 — [LOW] Números mágicos no desconto do relatório**

- Category: Quality
- File: models.py
- Lines: 256-262
- Evidence: Limiares `10000`, `5000`, `1000` e taxas `0.1`, `0.05`, `0.02` sem nome.
- Problem: Política de desconto opaca.
- Impact: Erro de edição; onboarding.
- MVC/SOLID Violation: Mínimo.
- Recommended Fix: Constantes/config nomeadas.
- Refactoring Strategy: named constants.

### **FINDING-022 — [LOW] Import não usado**

- Category: Quality
- File: models.py
- Line: 2
- Evidence: `import sqlite3` não aparece no restante do arquivo (uso é via `get_db()`).
- Problem: Ruído.
- Impact: Baixo.
- MVC/SOLID Violation: Nenhum.
- Recommended Fix: Remover o import.
- Refactoring Strategy: cleanup.

### **FINDING-023 — [LOW] Código morto /** `os` **não usado em database.py**

- Category: Quality
- File: database.py
- Line: 2
- Evidence: `import os` não é referenciado no arquivo.
- Problem: Dependência implícita falsa.
- Impact: Baixo.
- MVC/SOLID Violation: Nenhum.
- Recommended Fix: Remover.
- Refactoring Strategy: cleanup.

## **7. Security Findings**

- FINDING-001 — Segredos/credenciais no código (localização apenas; valores omitidos).
- FINDING-002 — SQL por concatenação com dados de request.
- FINDING-003 — `POST /admin/query` executa SQL do cliente.
- FINDING-004 — Sem authn/authz; IDOR em pedidos por `usuario_id`.
- FINDING-005 — Senhas em texto na listagem; `secret_key` em `/health`.
- FINDING-013 — E-mail em `print` no login/cadastro.
- FINDING-016 — `str(e)` ao cliente.
- FINDING-018 — DEBUG e `0.0.0.0`.
- FINDING-019 — CORS aberto.

Command injection, path traversal, XSS em HTML e SSRF: **não observados** neste código (API JSON, sem shell/`open` de path de usuário/`requests` outbound).

## **8. Performance Findings**

- FINDING-012 — N+1 em listagem de pedidos; queries repetidas na criação.
- FINDING-017 — Sem paginação em listagens.

## **9. Deprecated APIs**

None detected with current evidence.

Flask 3.1.1: `add_url_rule`, `jsonify`, `app.run` e sqlite3 usados não têm evidência de depreciação neste repositório. Sem changelog/warnings de runtime analisados nesta fase.

## **10. Architectural Improvements**

1. Configuração por ambiente (secret, debug, CORS, path do DB).
2. Authn/authz na borda + política por recurso.
3. Remover ou isolar `/admin/query` e reset.
4. Controllers finos; services (produto, usuário/auth, pedido, relatório).
5. Repositórios com SQL parametrizado; conexão request-scoped.
6. DTOs/serializers (nunca `senha`); validação única.
7. Adapter de notificação; transação de estoque no change de status.
8. Paginação e fetch de pedidos com JOIN.
9. Error handler central; logging redigido.
10. Hash de senha compatível com o contrato atual de login (mesmo comportamento funcional, armazenamento diferente).

## **11. Refactoring Plan**

Execução **somente após** `y` / `sim` / equivalente. Preservar URLs e JSON públicos tanto quanto possível.

1. CRITICAL: parametrizar SQL (002); remover ou proteger `/admin/query` e reset (003, 004, 008); env para segredos (001); DTOs sem senha e health limpo (005); hash de senha + login (005).
2. HIGH: conexão por request (009); extrair services e enxugar controllers (006, 011); fatiar models (007, 010); JOIN/batch pedidos (012); redigir logs (013).
3. MEDIUM: validador de produto (014, 015); erros centrais (016); paginação (017); CORS/debug (018, 019); hidratação única (020).
4. LOW: constantes e imports (021–023).

Padrão: nova abstração → migrar consumidores → remover responsabilidade antiga → validar.

Itens LOW/MEDIUM restantes após a Fase 3 podem ser aceitáveis se documentados.

## **12. Validation Plan**

- Build: `pip install -r requirements.txt` (não há `compileall` obrigatório; opcional `python -m compileall` nos `.py` da app).
- Tests: `No automated tests detected.`
- Boot: `python app.py` a partir de `code-smells-project/`.
- Endpoints descobertos (exercitar os relevantes, sem payloads de exploit):
  - `GET /`
  - `GET /health`
  - `GET /produtos`, `GET /produtos/busca`, `GET /produtos/<id>`
  - `POST /produtos`, `PUT /produtos/<id>`, `DELETE /produtos/<id>`
  - `GET /usuarios`, `GET /usuarios/<id>`, `POST /usuarios`, `POST /login`
  - `POST /pedidos`, `GET /pedidos`, `GET /pedidos/usuario/<id>`, `PUT /pedidos/<id>/status`
  - `GET /relatorios/vendas`
  - `POST /admin/reset-db`, `POST /admin/query` (comportamento pós-refatoração: protegido/ausente, não “SQL livre”)
- `NOT VALIDATED` se a porta 5000 não puder subir neste ambiente.s