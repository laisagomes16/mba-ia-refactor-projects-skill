# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env          # preencha FLASK_SECRET_KEY
python seed.py                # popula o banco SQLite
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`)
com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso
contrário os endpoints vão retornar listas vazias.

## Configuração

Toda configuração sensível vem de variáveis de ambiente (veja `.env.example`). Nenhum
segredo fica no código-fonte.

| Variável | Padrão | Descrição |
|---|---|---|
| `FLASK_SECRET_KEY` | aleatório por processo | Assina os tokens de autenticação |
| `TASK_MANAGER_DATABASE_URI` | `sqlite:///tasks.db` | Conexão do banco |
| `TASK_MANAGER_HOST` / `TASK_MANAGER_PORT` | `127.0.0.1` / `5000` | Bind do servidor (loopback por padrão) |
| `FLASK_DEBUG` | `false` | Modo debug (nunca em produção) |
| `SMTP_*` | — | Opcionais; sem eles o envio de e-mail é apenas registrado em log |

## Autenticação e autorização

`POST /login` devolve um token HMAC assinado (`services/auth_service.py`). Envie-o em
todas as rotas protegidas:

```http
Authorization: Bearer <token>
```

Política aplicada pelo `middleware/auth.py`:

| Rota | Acesso |
|---|---|
| `GET /`, `GET /health`, `POST /login` | público |
| `GET /users*`, `GET /tasks*`, `GET /categories`, `GET /reports/*` | autenticado |
| `POST/PUT/DELETE /tasks` | autenticado |
| `PUT/DELETE /users/<id>` | o próprio usuário **ou** admin |
| `POST /users`, `POST/PUT/DELETE /categories` | admin |

Sem token válido → **401**; sem permissão → **403**; token adulterado/expirado → **401**.
O usuário autenticado fica disponível em `g.current_user`.

## Arquitetura

```text
app.py                  app factory (create_app) + rotas / e /health
config.py               configuração por ambiente (sem segredos)
errors.py               exceções de domínio
error_handlers.py       mapeamento central de erro → HTTP JSON
middleware/auth.py      autenticação/autorização na borda (decorators)
serializers.py          formato JSON público (única fonte)
routes/                  controllers finos (só HTTP)
services/                regras de negócio (sem HTTP, sem SQL)
repositories/            acesso a dados (único lugar com queries)
models/                  entidades e invariantes do domínio
utils/helpers.py         constantes e utilitários compartilhados
```

Fluxo de uma requisição: `route → service → repository → model`, com erros de domínio
traduzidos para HTTP pelo handler central.

## Notificações

`services/notification_service.py` é chamado por `TaskService` sempre que uma task é
(atribuída|reatribuída) a um usuário — na criação (`POST /tasks` com `user_id`) e quando
o `user_id` muda em `PUT /tasks/<id>`. Renomear a task não notifica.

O envio é **best-effort**: sem `SMTP_USER`/`SMTP_PASSWORD` no ambiente nada é enviado,
apenas um `warning` é logado, e a requisição responde normalmente. Para trocar o
notificador (ex.: em testes) use `TaskService.set_notifier(...)`.

## Testes

```bash
python -m pytest test -q
```

Os testes usam banco SQLite em memória e cobrem as regressões da auditoria
(`test/test_audit_findings.py`): contagem de tasks por usuário sem N+1, relatório
agregado em SQL, bind padrão em loopback e notificação de atribuição.

## Paginação (opcional)

Os endpoints de listagem aceitam `page` e `per_page` na query string:

| Endpoint | Observação |
|---|---|
| `GET /tasks` | lista de tasks (com `user_name`/`category_name`) |
| `GET /tasks/search` | combina com `q`, `status`, `user_id`, `priority`, `category_id` |
| `GET /users` | inclui `task_count` |
| `GET /users/<id>/tasks` | tasks do usuário |
| `GET /categories` | inclui `task_count` |

- **Sem os parâmetros a resposta continua sendo um array** — o contrato original é preservado.
- Com `?page=` e/ou `?per_page=` a resposta vira `{items, page, per_page, total, pages}`.
  Defaults: `page=1`, `per_page=20` (máximo `100`).
- Valores inválidos (`page=0`, `per_page=abc`, `per_page=101`) retornam **400**.

```http
GET /tasks?page=2&per_page=10
Authorization: Bearer <token>
```

```json
{"items": [], "page": 2, "per_page": 10, "total": 42, "pages": 5}
```

## Compatibilidade

- O contrato JSON das 22 rotas originais é preservado campo a campo. A única diferença
  intencional é que o campo `password` **não** é mais exposto em nenhuma resposta.
- Contas com hash MD5 legado continuam autenticando e são migradas para PBKDF2 no
  primeiro login bem-sucedido.
- `POST /login` continua devolvendo `token`; o valor agora é um token HMAC assinado e
  validável (`services/auth_service.py`) em vez de `fake-jwt-token-<id>`.
- **Mudança intencional (FINDING-008):** as rotas protegidas agora exigem
  `Authorization: Bearer <token>`. Antes, todas as 22 rotas eram públicas — inclusive
  `DELETE /users/<id>`, que apagava o usuário e todas as suas tasks sem credencial.
  Clientes que chamavam a API sem token passam a receber **401**.

