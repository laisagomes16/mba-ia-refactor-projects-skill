# **Architecture Audit Report**

## **1. Executive Summary**

API LMS em **Node.js/Express 4.22.1** com **SQLite em memória**, monólito **não estruturado** centrado em `AppManager`. Risco geral **alto**: segredos no código, endpoints sensíveis sem autenticação, God Class com SQL/HTTP/regras misturados, e falhas de integridade/performance. **16 findings** (3 CRITICAL, 8 HIGH, 3 MEDIUM, 2 LOW). **Fase 3 recomendada**, de forma incremental, preservando contratos públicos.

## **2. Detected Stack**

- Language: JavaScript
- Language version: unknown (engines não declarado)
- Framework: Express
- Framework version: 4.22.1 (lockfile); manifest `^4.18.2`
- Runtime: Node.js (versão unknown)
- Package manager: npm (`package-lock.json`)
- Database: SQLite (`:memory:` via `sqlite3`)
- ORM: not detected
- Main libraries: express, sqlite3
- Test system: not detected
- Build system: not detected (`npm start` apenas)
- Docker: not detected
- External integrations: gateway de pagamento simulado inline (uso de chave em config; sem SDK HTTP separado)

## **3. Current Architecture**

**Unstructured monolith.** Não há pastas `controllers`/`services`/`repositories`. `src/app.js` só sobe o Express; `AppManager` concentra schema, seeds, rotas, SQL, checkout, pagamento, relatório e exclusão; `utils.js` mistura config secreta, cache global e “hash” de senha. Nomes de pasta não sugerem MVC — e o comportamento confirma ausência de camadas.

## **4. Architecture Flow**

Actual:

Request → Express (app.js)

       → AppManager.setupRoutes

            ├── validação mínima

            ├── SQL (sqlite3)

            ├── regras (pagamento, matrícula, relatório)

            ├── utils (config/secrets, badCrypto, cache)

            └── res.send / res.json

Intended (technology-adapted):

Route → Controller → Service/Use Case → Repository → SQLite

                 ↘ Adapter (PaymentGateway)

Config/secrets → environment

Authn/Authz middleware nas rotas sensíveis

## **5. Severity Summary**

| **Severity** | **Count** |
| ------------ | --------- |
| CRITICAL     | 3         |
| HIGH         | 8         |
| MEDIUM       | 3         |
| LOW          | 2         |

## **6. Findings**

### **FINDING-001 — [CRITICAL] Hardcoded secrets / credentials**

- Category: Security
- File: `src/utils.js`
- Lines: 1-7
- Evidence: Objeto `config` com literais para `dbUser`, `dbPass`, `paymentGatewayKey` (e usuário SMTP) commitados no fonte. Seed em `AppManager.js:18` também grava senha em texto (`pass`).
- Problem: Credenciais e chave de pagamento versionadas no repositório.
- Impact: Vazamento do repo = vazamento de segredos; rotação difícil.
- MVC/SOLID Violation: Configuração fora de fronteira de ambiente; não é SRP de infraestrutura.
- Recommended Fix: Variáveis de ambiente / secret manager; nunca logar valores.
- Refactoring Strategy: Extrair config sem literais secretos → migrar consumidores → remover literais.

### **FINDING-002 — [CRITICAL] Missing authentication / authorization**

- Category: Security
- File: `src/AppManager.js`
- Lines: 80-128 (`GET /api/admin/financial-report`), 131-137 (`DELETE /api/users/:id`)
- Evidence: Rotas admin e mutação de usuários registradas sem middleware, token, sessão ou checagem de papel.
- Problem: Dados financeiros (nomes, e-mails, receitas) e exclusão de usuários são públicos na API.
- Impact: Exposição e destruição de dados por qualquer cliente que alcance a porta.
- MVC/SOLID Violation: Cross-cutting auth ausente na borda.
- Recommended Fix: Middleware de authn/authz + checagens no serviço.
- Refactoring Strategy: Introduzir guard nas rotas sensíveis sem mudar paths; política centralizada.

### **FINDING-003 — [CRITICAL] God Class (**`AppManager`**)**

- Category: Architecture / MVC / SRP
- File: `src/AppManager.js`
- Lines: 3-139
- Evidence: Uma classe faz DDL/seeds, registra 3 rotas, executa SQL, orquestra checkout/pagamento/auditoria e monta relatório multi-entidade (users, courses, enrollments, payments, audit_logs).
- Problem: Mudança em um domínio arrisca os demais; testes não isolam comportamento.
- Impact: Manutenção e evolução inseguras; MVC inexistente.
- MVC/SOLID Violation: SRP severo; ISP/DIP comprometidos.
- Recommended Fix: Separar controllers, services, repositories/adapters.
- Refactoring Strategy: Novas abstrações por camada → migrar rota a rota → esvaziar `AppManager`.

### **FINDING-004 — [HIGH] Checkout sem verificação de senha para e-mail existente**

- Category: Security / Authn
- File: `src/AppManager.js`
- Lines: 66-75
- Evidence: Se `users.email` já existe, chama `processPaymentAndEnroll(user.id)` sem comparar `pwd`/hash.
- Problem: Qualquer um pode matricular/pagar em nome de um usuário só informando o e-mail.
- Impact: Impersonação / vínculo indevido de matrículas e pagamentos.
- MVC/SOLID Violation: Política de identidade ausente no use case.
- Recommended Fix: Exigir autenticação ou verificação de senha antes de reutilizar `userId`.
- Refactoring Strategy: Extrair serviço de checkout com regra de identidade explícita.

### **FINDING-005 — [HIGH] Sensitive data in logs**

- Category: Security
- File: `src/AppManager.js`
- Line: 45
- Evidence: `console.log` interpola número do cartão (`cc`) e a chave do gateway (`config.paymentGatewayKey`).
- Problem: Logs viram repositório de dados sensíveis.
- Impact: Exposição via acesso a stdout/arquivos de log.
- MVC/SOLID Violation: Logging sem política de redação.
- Recommended Fix: Redação; campos allowlisted; nunca logar PAN/chave.
- Refactoring Strategy: Adapter de pagamento com logging seguro.

### **FINDING-006 — [HIGH] Weak password hashing (**`badCrypto`**)**

- Category: Security
- File: `src/utils.js`
- Lines: 17-23; uso em `AppManager.js:68-69`
- Evidence: “Hash” = loop de Base64 truncado a 10 chars; seed ainda usa senha em texto puro (`AppManager.js:18`). Default `p || "123456"` se senha omitida.
- Problem: Armazenamento de senha invertível/fraco; default inseguro.
- Impact: Comprometimento de credenciais com baixo esforço.
- MVC/SOLID Violation: Utilitário inseguro no lugar de adapter criptográfico adequado.
- Recommended Fix: Algoritmo de password hashing reconhecido (ex.: bcrypt/scrypt/argon2) via lib adequada; exigir senha.
- Refactoring Strategy: Substituir `badCrypto` e migrar criação de usuário (sem mudar contrato HTTP público além do necessário para segurança mínima acordada — preferir manter shape do body).

### **FINDING-007 — [HIGH] Fat Controller / business logic in routes**

- Category: MVC / SRP
- File: `src/AppManager.js`
- Lines: 28-78 (checkout); 80-128 (report)
- Evidence: Handlers contêm fluxo multi-etapa (curso → usuário → pagamento → matrícula → payment → audit → cache) e agregação financeira com regras `PAID`.
- Problem: Camada HTTP absorve o domínio; regras não reutilizáveis fora do request.
- Impact: Baixa testabilidade; OCP frágil.
- MVC/SOLID Violation: Fat Controller; Business Logic in Route; SRP.
- Recommended Fix: Use cases `CheckoutService`, `FinancialReportService`.
- Refactoring Strategy: Extrair serviço → controller fino validate-delegate-respond.

### **FINDING-008 — [HIGH] Tight coupling to SQLite driver**

- Category: Architecture / DIP
- File: `src/AppManager.js`
- Lines: 1, 6-7, e queries ao longo de 12-136
- Evidence: `new sqlite3.Database(':memory:')` e SQL embutidos nos handlers; impossível testar regras sem DB.
- Problem: Política de alto nível acoplada à infra concreta.
- Impact: Troca de persistência e testes unitários bloqueados.
- MVC/SOLID Violation: DIP; camadas colapsadas.
- Recommended Fix: Repositories injetados; composition root em `app.js`.
- Refactoring Strategy: Criar repositórios → injetar no service → remover SQL dos handlers.

### **FINDING-009 — [HIGH] Global mutable state**

- Category: Architecture / Testability
- File: `src/utils.js`
- Lines: 9-14; uso `AppManager.js:59`
- Evidence: `globalCache` e `totalRevenue` no escopo do módulo; `logAndCache` muta cache compartilhado do processo.
- Problem: Estado entre requests; testes dependem de ordem; crescimento sem invalidação.
- Impact: Vazamento lógico entre requisições; flakiness.
- MVC/SOLID Violation: DIP; ownership de lifecycle obscuro.
- Recommended Fix: Store explícito/DI; evitar mutáveis de módulo para dados de request.
- Refactoring Strategy: Global State → Dependency Injection / store scoped.

### **FINDING-010 — [HIGH] Payment processing inside route handler**

- Category: MVC / DIP
- File: `src/AppManager.js`
- Lines: 43-48
- Evidence: Decisão de pagamento (`cc.startsWith("4")`) e uso da chave do gateway ocorrem dentro do handler HTTP.
- Problem: Vendor/regra de pagamento colada à rota.
- Impact: Difícil mockar gateway; política de cobrança espalhada.
- MVC/SOLID Violation: External Integration in Controller; SRP/DIP.
- Recommended Fix: `PaymentGateway` adapter + serviço de checkout.
- Refactoring Strategy: Extrair adapter → serviço consome interface simples → rota só orquestra HTTP.

### **FINDING-011 — [HIGH] DELETE user breaks referential integrity (and ignores DB errors)**

- Category: Security / Data integrity / Quality
- File: `src/AppManager.js`
- Lines: 131-136
- Evidence: `DELETE FROM users` sem remover/ajustar `enrollments`/`payments`; callback ignora `err` e sempre responde sucesso com mensagem admitindo dados “sujos”.
- Problem: Órfãos no banco; falhas de delete mascaradas.
- Impact: Relatórios e dados inconsistentes; falsa confirmação ao cliente.
- MVC/SOLID Violation: Regra de consistência ausente no model/serviço.
- Recommended Fix: Transação com cascade/cleanup; propagar erro real.
- Refactoring Strategy: Use case `DeleteUser` no service + repository em transação.

### **FINDING-012 — [MEDIUM] N+1 / queries inside loops**

- Category: Performance
- File: `src/AppManager.js`
- Lines: 89-126
- Evidence: Para cada course → query enrollments; para cada enrollment → query user + query payment.
- Problem: Latência e carga crescem com volume (padrão N+1 aninhado).
- Impact: Relatório admin degrada com dados.
- MVC/SOLID Violation: API de repositório ingênua (indireto).
- Recommended Fix: JOINs / batch `IN (...)` / uma query agregada.
- Refactoring Strategy: Repositório de relatório com query set-based.

### **FINDING-013 — [MEDIUM] Missing / weak input validation**

- Category: Quality / Security
- File: `src/AppManager.js`
- Lines: 29-35, 68, 132
- Evidence: Só checa presença de `usr`/`eml`/`c_id`/`card`; sem tipos, formato de e-mail, validação de cartão; `pwd` opcional; `id` de delete sem checagem de existência/ownership.
- Problem: Dados corruptos e fluxos parciais (ex.: senha default).
- Impact: 4xx/5xx irregulares; superfície para abuso.
- MVC/SOLID Violation: Validação rasa incompleta na borda.
- Recommended Fix: DTO/validator no controller (schema simples).
- Refactoring Strategy: Missing Validation → Validator/DTO antes do service.

### **FINDING-014 — [MEDIUM] Inconsistent error handling**

- Category: Quality
- File: `src/AppManager.js`
- Lines: 35-61, 131-136
- Evidence: Mistura `send("Bad Request")` texto, `json` de sucesso, erros DB genéricos; erro de `audit_logs` (linha 57) não tratado antes do 200; DELETE ignora `err`.
- Problem: Cliente não tem contrato de erro estável; sucesso mentiroso.
- Impact: Integrações frágeis; possível mascarar falhas.
- MVC/SOLID Violation: Cross-cutting de erros não isolado.
- Recommended Fix: Handler central mapeando erros de domínio → HTTP.
- Refactoring Strategy: Extrair tipos de erro de domínio + middleware Express.

### **FINDING-015 — [LOW] Magic numbers and poor naming**

- Category: Quality
- File: `src/AppManager.js`, `src/utils.js`
- Lines: `AppManager.js` 29-33, 46; `utils.js` 19-22
- Evidence: Body `usr`/`eml`/`pwd`/`c_id`; regra mágica `startsWith("4")`; loop `10000` e `substring(0, 10)` sem nome semântico.
- Problem: Legibilidade e risco de edição errada.
- Impact: Onboarding e manutenção.
- MVC/SOLID Violation: Mínimo.
- Recommended Fix: Constantes/enums nomeados (sem mudar contrato JSON público).
- Refactoring Strategy: Aliases internos + constantes de domínio.

### **FINDING-016 — [LOW] Dead / unused global revenue state**

- Category: Quality
- File: `src/utils.js` Lines: 10, 25; `src/AppManager.js` Line: 2
- Evidence: `totalRevenue` exportado e importado em `AppManager`, mas nunca lido/atualizado no fluxo analisado.
- Problem: Estado morto aumenta ruído.
- Impact: Confusão; falsa impressão de agregação global.
- MVC/SOLID Violation: Mínimo.
- Recommended Fix: Remover ou implementar no serviço de relatório.
- Refactoring Strategy: Eliminar no cleanup após extrair serviços.

## **7. Security Findings**

- **FINDING-001** — Segredos hardcoded em `utils.js` (e senha em seed).
- **FINDING-002** — `/api/admin/financial-report` e `DELETE /api/users/:id` sem authn/authz.
- **FINDING-004** — Checkout reutiliza usuário por e-mail sem verificar senha.
- **FINDING-005** — Cartão e chave de gateway no `console.log`.
- **FINDING-006** — Hash de senha frágil / senha default / seed em texto.
- **FINDING-011** — Delete público + integridade quebrada (amplifica impacto de 002).

SQLi: queries usam placeholders `?` — **não** classificado como injection com a evidência atual. Command injection / XSS / SSRF: **não detectados** no código analisado.

## **8. Performance Findings**

- **FINDING-012** — N+1 aninhado no relatório financeiro.
- **FINDING-006** (secundário) — loop 10k em `badCrypto` no caminho de criação de usuário (CPU desnecessária + inseguro).

## **9. Deprecated APIs**

None detected with current evidence. (APIs usadas de Express/sqlite3 no código da aplicação não foram identificadas como deprecated na evidência do projeto; deprecações transitivas em `node_modules` não são uso da aplicação.)

## **10. Architectural Improvements**

1. Introduzir fluxo Express adaptado: Route → Controller → Service → Repository.
2. Composition root em `app.js` (wiring de DB, repos, services).
3. Config via environment; zero segredos no fonte.
4. Middleware de autenticação/autorização para admin e mutações.
5. Adapter de pagamento isolado.
6. Validação de input (DTO) e tratamento central de erros.
7. Relatório financeiro via query set-based.
8. Remover estado global mutável de módulo.

## **11. Refactoring Plan**

Execução **somente após confirmação** `[y/n]`. Ordem sugerida:

1. **CRITICAL:** Config/env sem segredos (**001**) → auth nas rotas sensíveis (**002**) → quebrar God Class começando por checkout (**003**).
2. **HIGH:** Regra de identidade no checkout (**004**); redacão de logs + adapter pagamento (**005**, **010**); hashing de senha (**006**); extrair services/controllers (**007**); repositories + DI (**008**, **009**); delete com integridade (**011**).
3. **MEDIUM:** Query do relatório (**012**); validators (**013**); error middleware (**014**).
4. **LOW:** Naming/constantes (**015**); remover `totalRevenue` morto (**016**).

Padrão incremental: nova abstração → migrar consumidores → remover responsabilidade antiga → validar → próximo finding.

## **12. Validation Plan**

- **Build:** sem script de build — `SKIPPED` ou checagem `node -c` / require dos módulos.
- **Tests:** `No automated tests detected.`
- **Boot:** `npm start` (ou `node src/app.js`).
- **Endpoints** (descobertos em código/`api.http`):
  - `POST /api/checkout` (sucesso e cartão recusado)
  - `GET /api/admin/financial-report`
  - `DELETE /api/users/:id`
- Preservar paths e shapes de request/response públicos na medida do possível; auth nova deve ser documentada se alterar o requisito de headers (contrato de segurança vs. “mesmo payload”).
- Qualquer checagem não executável: `NOT VALIDATED` + motivo.