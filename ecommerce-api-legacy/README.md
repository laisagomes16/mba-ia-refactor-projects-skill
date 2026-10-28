# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
```

Defina as variáveis de ambiente (veja `.env.example`). Segredos **não** ficam no código-fonte.

Exemplo (PowerShell):

```powershell
$env:DB_USER="admin"
$env:DB_PASS="change-me"
$env:PAYMENT_GATEWAY_KEY="pk_test_change_me"
$env:SMTP_USER="no-reply@example.com"
$env:ADMIN_API_KEY="admin-secret"
$env:PORT="3000"
$env:SEED_USER_PASSWORD="123"
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e carrega seeds no boot (senha do usuário seed = `SEED_USER_PASSWORD`).

## Autenticação admin

Rotas protegidas exigem a chave em `ADMIN_API_KEY` via header:

- `x-admin-key: <ADMIN_API_KEY>`
- ou `Authorization: Bearer <ADMIN_API_KEY>`

Rotas protegidas:

- `GET /api/admin/financial-report`
- `DELETE /api/users/:id`

## Checkout

`POST /api/checkout` mantém o body legado (`usr`, `eml`, `pwd`, `c_id`, `card`).

- Usuário novo: `pwd` é obrigatório e armazenado com hash (scrypt).
- Usuário existente (mesmo `eml`): `pwd` deve conferir com o hash armazenado.

Pagamento simulado: cartão começando com `4` → `PAID`; caso contrário → recusado.

Exemplos de requisições estão em `api.http`.

## Estrutura

```text
src/
  app.js                 # composition root
  config.js              # env
  routes/                # HTTP routes
  controllers/           # request/response
  services/              # use cases
  repositories/          # SQL
  adapters/              # payment, password, cache
  middleware/            # auth + errors
  validators/
  db/
  errors/
```
