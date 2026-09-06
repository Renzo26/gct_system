# GCT — Onboarding Completo

Sistema de gestão de oficina mecânica com atendimento via WhatsApp. Permite gerenciar conversas, agendamentos, clientes, etiquetas e usuários através de interface web integrada ao WhatsApp via WAHA.

---

## Stack Tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11 + FastAPI + SQLAlchemy 2 async + Alembic + Pydantic v2 |
| Frontend | React 19 + TanStack Router (file-based) + TanStack Start + Tailwind CSS + shadcn/ui |
| Banco | Supabase (PostgreSQL) via Session Pooler IPv4, porta 5432 |
| Cache/Filas | Redis |
| WhatsApp | WAHA (self-hosted no EasyPanel) |
| Auth | JWT com python-jose + bcrypt==3.2.2 + passlib==1.7.4 (pins obrigatórios) |

---

## Estrutura de Pastas

```
gct-workshop-hub/          ← raiz do git
├── backend/                    ← API Python/FastAPI
│   ├── main.py                 ← entry point + CORS + Redis lifespan
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/                ← migrações do banco
│   │   └── versions/
│   └── app/
│       ├── api/                ← routers FastAPI
│       │   ├── auth.py
│       │   ├── conversations.py
│       │   ├── webhooks.py
│       │   ├── sse.py
│       │   ├── clients.py
│       │   ├── appointments.py
│       │   ├── workshop_labels.py
│       │   └── workshop_users.py
│       ├── core/
│       │   ├── config.py       ← Settings (pydantic-settings, extra="ignore")
│       │   ├── database.py     ← AsyncSession factory
│       │   └── redis.py        ← get_redis()
│       ├── models/             ← SQLAlchemy ORM (um arquivo por tabela)
│       ├── schemas/            ← Pydantic v2 (In/Out por módulo)
│       └── services/
│           ├── auth_service.py         ← hash_password, decode_token, ConflictError, AuthError
│           ├── conversation_service.py ← process_webhook (lógica principal do WAHA)
│           ├── waha_service.py         ← cliente HTTP para o WAHA
│           ├── redis_service.py        ← bloquear/liberar bot
│           └── sse_service.py          ← broadcaster de eventos SSE
└── gct-workshop-hub/      ← Frontend React
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── lib/
        │   ├── api.ts          ← cliente fetch (Bearer JWT automático, métodos: get/post/put/patch/delete)
        │   └── auth.ts         ← setAuth/clearAuth/getSession (localStorage)
        └── routes/
            ├── app.tsx                         ← layout + guard (redireciona /login se sem token)
            ├── app.index.tsx                   ← dashboard (conversas + agendamentos de hoje)
            ├── app.conversas.tsx               ← chat em tempo real via SSE
            ├── app.agenda.tsx                  ← calendário + agendamentos
            ├── app.configuracoes.clientes.tsx  ← CRUD clientes
            ├── app.configuracoes.usuarios.tsx  ← CRUD usuários
            ├── app.configuracoes.etiquetas.tsx ← CRUD etiquetas
            ├── login.tsx                       ← login
            └── cadastro.tsx                    ← cadastro de nova oficina
```

---

## Como rodar localmente

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# criar .env (ver seção abaixo)
alembic upgrade head
uvicorn main:app --reload --port 8000
```

### Frontend

```powershell
cd gct-workshop-hub
npm install
npm run dev
```

- Backend: http://localhost:8000
- Frontend: http://localhost:8080

---

## Arquivo backend/.env (não está no git)

```env
DATABASE_URL=postgresql+asyncpg://postgres.SEU_PROJETO:SUA_SENHA@aws-0-sa-east-1.pooler.supabase.com:5432/postgres
WAHA_BASE_URL=https://SEU-WAHA.easypanel.host
WAHA_API_KEY=sua-chave-waha
WAHA_SESSION=Cloudy
REDIS_URL=redis://default:SUA_SENHA@seu-host-redis:6379
JWT_SECRET=gere-um-novo: python -c "import secrets; print(secrets.token_urlsafe(64))"
APP_ENV=development
APP_PORT=8000
CORS_ORIGINS=http://localhost:8080,http://localhost:5173
```

---

## Rotas da API (prefixo `/api`)

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /auth/register | Cria oficina + admin |
| POST | /auth/login | Login, retorna JWT |
| POST | /auth/refresh | Renova access token |
| GET | /conversations | Lista conversas (?tab=ALL/OPEN/RESOLVED) |
| GET | /conversations/{id}/messages | Mensagens de uma conversa |
| POST | /conversations/{id}/messages | Envia mensagem via WAHA |
| PATCH | /conversations/{id}/resolve | Resolve conversa |
| POST | /conversations/{id}/labels | Adiciona etiqueta |
| DELETE | /conversations/{id}/labels/{lid} | Remove etiqueta |
| POST | /webhooks/waha | Recebe eventos do WAHA |
| GET | /sse/events | Stream SSE de eventos em tempo real |
| GET/POST | /clients | Lista/cria clientes |
| PUT/DELETE | /clients/{id} | Atualiza/remove cliente |
| GET/POST | /appointments | Lista/cria agendamentos (?data=YYYY-MM-DD) |
| PUT/DELETE | /appointments/{id} | Atualiza/remove agendamento |
| GET/POST | /labels | Lista/cria etiquetas |
| PUT/DELETE | /labels/{id} | Atualiza/remove etiqueta |
| GET/POST | /users | Lista/cria usuários da oficina |
| PUT/DELETE | /users/{id} | Atualiza/remove usuário |

---

## Fluxo Principal do Sistema

```
Cliente WhatsApp
      │
      ▼
   WAHA (self-hosted)
      │ POST /api/webhooks/waha
      ▼
conversation_service.py
  ├── Cria/atualiza lead (clientes)
  ├── Cria/atualiza conversa
  └── Salva mensagem no banco
      │
      ▼
sse_service.py → broadcast evento
      │
      ▼
Frontend (SSE listener)
  └── Atualiza chat em tempo real
      │
      ▼ (atendente responde)
POST /api/conversations/{id}/messages
      │
      ▼
waha_service.py → envia para WAHA → WhatsApp
```

---

## Telas do Frontend

| Rota | Arquivo | Descrição |
|------|---------|-----------|
| `/login` | login.tsx | Login da oficina |
| `/cadastro` | cadastro.tsx | Cadastro de nova oficina |
| `/app` | app.index.tsx | Dashboard: conversas abertas + agendamentos do dia |
| `/app/conversas` | app.conversas.tsx | Chat em tempo real via SSE |
| `/app/agenda` | app.agenda.tsx | Calendário + gestão de agendamentos |
| `/app/configuracoes/clientes` | app.configuracoes.clientes.tsx | CRUD clientes |
| `/app/configuracoes/usuarios` | app.configuracoes.usuarios.tsx | CRUD usuários |
| `/app/configuracoes/etiquetas` | app.configuracoes.etiquetas.tsx | CRUD etiquetas |

---

## Armadilhas Conhecidas (IMPORTANTE)

### bcrypt/passlib — Pin obrigatório
```
bcrypt==3.2.2
passlib[bcrypt]==1.7.4
```
bcrypt 4.x quebra o passlib completamente. Nunca atualizar sem testar.

### Pydantic v2 — campo `_data`
Atributos com `_` são privados no Pydantic v2. Usar alias:
```python
_data: Optional[dict] = Field(None, alias="_data")

class Config:
    populate_by_name = True
```

### Pydantic v2 — campo `from`
`from` é palavra reservada do Python. Usar alias:
```python
sender: Optional[str] = Field(None, alias="from")
```

### Supabase — IPv4 obrigatório
Usar **Session Pooler** (porta 5432 do pooler), NUNCA a conexão direta (usa IPv6 e não funciona em redes sem IPv6).

### Datas no JavaScript
```typescript
// ERRADO — toISOString() converte para UTC, quebra o dia no fuso UTC-3
const date = new Date().toISOString().split('T')[0]

// CORRETO — usa data local
const d = new Date()
const date = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
```

### Redis hostname no EasyPanel
`seu-host-redis` é o hostname interno Docker do EasyPanel. Só funciona quando o backend está na mesma rede Docker da VPS.

### CORS
O backend precisa incluir a URL exata do frontend em `CORS_ORIGINS`. Sem trailing slash.

### PushName (nome do contato WhatsApp)
O WAHA envia o nome do contato em dois lugares possíveis dependendo da versão:
- `_data.Info.PushName`
- `_data.PushName`

O código tenta ambos com fallback.

---

## Deploy (EasyPanel)

### Backend
1. Criar serviço App a partir do `backend/Dockerfile`
2. Expor porta 8080
3. Configurar todas as variáveis de ambiente do `.env` no painel
4. Após deploy, configurar webhook no WAHA: `https://SEU-DOMINIO/api/webhooks/waha`

### Frontend
1. Definir variável de build: `VITE_API_URL=https://SEU-DOMINIO-BACKEND`
2. Rodar `npm run build`
3. Servir a pasta `dist/`

---

## Git e Repositório

- Repositório: https://github.com/Renzo26/gct-workshop-hub
- Branch principal: `main`
- Git user: `Renzo26`
- Email: `arthur.renzo@uscsonline.com.br`

### Commits recentes relevantes
- `fix: update lead name/phone when current name looks like a phone number`
- `fix: read SenderAlt from _data.Info and use savepoint for duplicate message handling`
- `fix: read PushName from _data.Info instead of _data root`

---

## Padrões de Código

### Backend
- Um arquivo por módulo em `api/`, `models/`, `schemas/`, `services/`
- Services concentram toda lógica de negócio — routers só delegam
- Async em tudo (SQLAlchemy async session, httpx async)
- Pydantic v2 para validação e serialização

### Frontend
- TanStack Router com file-based routing (nome do arquivo = rota)
- `src/lib/api.ts` para todas as chamadas HTTP (nunca fetch direto)
- `src/lib/auth.ts` para ler/gravar sessão
- shadcn/ui para componentes UI
- Tailwind CSS para estilos

---

## Contexto do Projeto

Sistema desenvolvido como TCC. É um SaaS de gestão de oficina mecânica com diferencial de atendimento WhatsApp integrado. A arquitetura foi pensada para ser multi-tenant (cada oficina tem seus próprios dados isolados por `workshop_id`).
