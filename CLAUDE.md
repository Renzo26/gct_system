# GCT — Guia do Projeto

Sistema de gestão de oficina mecânica com atendimento via WhatsApp.

## Estrutura do repositório

```
gct-workshop-hub/          ← raiz do git
├── backend/                    ← API Python/FastAPI
└── gct-workshop-hub/      ← Frontend React
```

## Stack

- **Backend:** Python 3.11 + FastAPI + SQLAlchemy 2 async + Alembic + Pydantic v2
- **Frontend:** React 19 + TanStack Router (file-based) + TanStack Start + Tailwind CSS + shadcn/ui
- **Banco:** Supabase (PostgreSQL) via Session Pooler (IPv4)
- **Cache/Filas:** Redis
- **WhatsApp:** WAHA (self-hosted na VPS EasyPanel)
- **Auth:** JWT com python-jose, bcrypt==3.2.2 + passlib==1.7.4 (pin obrigatório)

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

- Backend roda em: http://localhost:8000
- Frontend roda em: http://localhost:8080

## Arquivo backend/.env (não está no git)

```
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

## Arquitetura do backend

```
backend/
├── main.py                  ← FastAPI app + CORS + Redis lifespan
├── alembic/                 ← migrações do banco
└── app/
    ├── api/                 ← routers (um arquivo por módulo)
    │   ├── auth.py          ← POST /auth/register, /auth/login, /auth/refresh
    │   ├── conversations.py ← GET/PATCH /conversations, mensagens
    │   ├── webhooks.py      ← POST /webhooks/waha (recebe do WAHA)
    │   ├── sse.py           ← GET /sse/events (Server-Sent Events)
    │   ├── clients.py       ← CRUD /clients
    │   ├── appointments.py  ← CRUD /appointments?data=YYYY-MM-DD
    │   ├── workshop_labels.py ← CRUD /labels
    │   └── workshop_users.py  ← CRUD /users
    ├── core/
    │   ├── config.py        ← Settings (pydantic-settings, extra="ignore")
    │   ├── database.py      ← AsyncSession factory
    │   └── redis.py         ← get_redis()
    ├── models/              ← SQLAlchemy ORM (um arquivo por tabela)
    ├── schemas/             ← Pydantic v2 (In/Out por módulo)
    └── services/
        ├── auth_service.py        ← hash_password, decode_token, ConflictError, AuthError
        ├── conversation_service.py ← process_webhook (lógica principal do WAHA)
        ├── waha_service.py        ← cliente HTTP para o WAHA
        ├── redis_service.py       ← bloquear/liberar bot
        └── sse_service.py         ← broadcaster de eventos SSE
```

## Rotas do backend (prefixo /api)

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
| GET/POST | /appointments | Lista/cria agendamentos |
| PUT/DELETE | /appointments/{id} | Atualiza/remove agendamento |
| GET/POST | /labels | Lista/cria etiquetas |
| PUT/DELETE | /labels/{id} | Atualiza/remove etiqueta |
| GET/POST | /users | Lista/cria usuários da oficina |
| PUT/DELETE | /users/{id} | Atualiza/remove usuário |

## Arquitetura do frontend

```
gct-workshop-hub/src/
├── lib/
│   ├── api.ts       ← cliente fetch (Bearer JWT automático, métodos: get/post/put/patch/delete)
│   └── auth.ts      ← setAuth/clearAuth/getSession (localStorage)
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

## Pontos críticos / armadilhas já resolvidas

- **bcrypt:** DEVE ser `bcrypt==3.2.2` com `passlib[bcrypt]==1.7.4`. bcrypt 4.x quebra o passlib.
- **Pydantic v2 + campo `_data`:** usar `Field(None, alias="_data")` com `populate_by_name=True` — atributos começando com `_` são privados no Pydantic v2.
- **Pydantic v2 + campo `from`:** usar `Field(None, alias="from")` pois `from` é palavra reservada do Python.
- **Supabase IPv4:** usar Session Pooler (porta 5432 do pooler), NÃO a conexão direta (IPv6).
- **Data local no JS:** usar `getFullYear()/getMonth()/getDate()` — `toISOString()` converte para UTC e quebra o dia em fusos negativos (Brasil UTC-3).
- **CORS:** o backend precisa incluir a URL do frontend na variável `CORS_ORIGINS`.
- **Redis hostname:** `seu-host-redis` é o hostname interno Docker do EasyPanel — funciona apenas quando o backend está na mesma rede (VPS).

## Deploy (EasyPanel)

- Backend: criar serviço App a partir do `backend/Dockerfile`, expor porta 8080.
- Variáveis de ambiente: mesmas do `.env`, mas sem o arquivo — configurar no painel.
- Webhook WAHA: após deploy, configurar URL `https://SEU-DOMINIO/api/webhooks/waha` no dashboard do WAHA.
- Frontend: definir `VITE_API_URL=https://SEU-DOMINIO-BACKEND` antes do build.

## Git

- Repositório: https://github.com/Renzo26/gct-workshop-hub
- Commits sempre com: `git config user.email "arthur.renzo@uscsonline.com.br"`
