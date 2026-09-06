# GCT — Sistema de Gerenciamento de Oficina Mecânica

Sistema SaaS para gestão de oficinas mecânicas com integração ao WhatsApp, atendimento com IA e agenda integrada.

---

## Visão Geral

O **GCT** é uma plataforma multi-tenant que centraliza o atendimento ao cliente via WhatsApp, o agendamento de serviços e o controle da equipe em uma única interface web. Cada oficina opera com dados completamente isolados.

**Funcionalidades principais:**

- Gerenciamento de conversas do WhatsApp em tempo real (via SSE)
- Agenda de serviços com calendário interativo
- Cadastro de clientes com histórico de veículos e serviços
- Controle de usuários com níveis de acesso (ADMIN / AGENT)
- Sistema de etiquetas para organizar conversas
- Assistente de IA integrado (Claude / Anthropic)
- Alternância bot/humano por conversa (controle via Redis)
- Dashboard com agendamentos do dia e conversas abertas

---

## Stack

| Camada | Tecnologia |
|---|---|
| **Frontend** | React 19, TanStack Router, TanStack Query, Tailwind CSS 4, shadcn/ui |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2 (async), Pydantic v2 |
| **Banco de dados** | PostgreSQL via Supabase (asyncpg) |
| **Migrações** | Alembic |
| **Cache / Fila** | Redis |
| **Tempo real** | Server-Sent Events (SSE) |
| **WhatsApp** | WAHA (self-hosted) |
| **Automação** | n8n (CloudyBot) |
| **IA** | Anthropic SDK (Claude) |
| **Infra** | Docker + Nginx, EasyPanel |

---

## Estrutura do Projeto

```
gct/
├── backend/                  # FastAPI
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── alembic/              # Migrações do banco
│   └── app/
│       ├── api/              # Routers (auth, conversations, webhooks, sse…)
│       ├── core/             # Config, database, redis
│       ├── models/           # ORM SQLAlchemy
│       ├── schemas/          # Pydantic schemas
│       └── services/         # Lógica de negócio
│
├── gct-workshop-hub/    # React + TanStack Start
│   ├── src/
│   │   ├── routes/           # Roteamento file-based
│   │   ├── components/       # Componentes reutilizáveis
│   │   ├── hooks/            # Custom hooks
│   │   └── lib/              # api.ts, auth.ts
│   ├── Dockerfile
│   └── nginx.conf
│
└── docker-compose.yml
```

---

## Pré-requisitos

- Python 3.12+
- Node.js 20+
- PostgreSQL (ou conta Supabase)
- Redis
- WAHA rodando e acessível
- Chave de API da Anthropic

---

## Configuração

### 1. Variáveis de ambiente

Copie o arquivo de exemplo e preencha os valores:

```bash
cp .env.example .env
```

```env
# Banco de dados (usar Session Pooler do Supabase, porta 5432)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/postgres

# WhatsApp
WAHA_BASE_URL=https://sua-instancia-waha.exemplo.com
WAHA_API_KEY=sua-chave-waha
WAHA_SESSION=Cloudy

# Redis
REDIS_URL=redis://default:senha@host:6379

# Auth
JWT_SECRET=chave-secreta-256-bits

# IA
ANTHROPIC_API_KEY=sua-chave-anthropic

# App
APP_ENV=development
APP_PORT=8000
CORS_ORIGINS=http://localhost:8080,http://localhost:5173
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

alembic upgrade head
uvicorn main:app --reload --port 8000
```

API disponível em `http://localhost:8000` — documentação em `/docs`.

### 3. Frontend

```bash
cd gct-workshop-hub
npm install
npm run dev
```

Frontend disponível em `http://localhost:8080`.

---

## Rodando com Docker

```bash
docker compose up --build
```

Serviços:
- `backend` — FastAPI na porta 8080 (executa migrações automaticamente)
- `frontend` — React servido pelo Nginx na porta 80

---

## Principais Endpoints da API

| Método | Endpoint | Descrição |
|---|---|---|
| `POST` | `/api/auth/register` | Cadastrar oficina e usuário admin |
| `POST` | `/api/auth/login` | Autenticar (retorna JWT) |
| `POST` | `/api/auth/refresh` | Renovar token de acesso |
| `GET` | `/api/conversations` | Listar conversas (filtros: ALL / OPEN / RESOLVED) |
| `GET` | `/api/conversations/{id}/messages` | Mensagens paginadas |
| `POST` | `/api/conversations/{id}/messages` | Enviar mensagem via WAHA |
| `PATCH` | `/api/conversations/{id}/human` | Assumir atendimento (bloqueia bot) |
| `PATCH` | `/api/conversations/{id}/bot` | Liberar para o bot |
| `PATCH` | `/api/conversations/{id}/resolve` | Resolver conversa |
| `GET/POST` | `/api/clients` | CRUD de clientes |
| `GET/POST` | `/api/appointments` | CRUD de agendamentos |
| `GET/POST` | `/api/users` | CRUD de usuários da oficina |
| `GET/POST` | `/api/labels` | CRUD de etiquetas |
| `POST` | `/api/webhooks/waha` | Receber eventos do WAHA |
| `GET` | `/api/sse/events` | Stream de eventos em tempo real |
| `POST` | `/api/assistant` | Chat com assistente de IA |

---

## Fluxo de Autenticação

1. Oficina se cadastra → backend cria `Workshop` + usuário admin
2. Login com e-mail e senha → JWT de acesso (8h) + refresh token (7d)
3. Frontend armazena tokens no `localStorage`
4. Todas as requisições enviam `Authorization: Bearer <token>`

---

## Decisões Técnicas

**SSE em vez de WebSocket** — o backend utiliza Server-Sent Events para enviar atualizações em tempo real ao frontend. É unidirecional e funciona bem para notificações de novas mensagens e mudanças de status de conversa.

**Redis para controle bot/humano** — cada conversa pode estar em modo bot (n8n responde automaticamente) ou humano (atendente assume). A troca é controlada por uma chave Redis, permitindo bloqueio e liberação sem alterar o banco de dados.

**Pinos de versão críticos no backend:**
```
bcrypt==3.2.2       # bcrypt 4.x quebra o passlib
passlib[bcrypt]==1.7.4
```

**Supabase via Session Pooler (porta 5432)** — a conexão direta usa IPv6, incompatível com muitos ambientes de hospedagem. O Session Pooler garante IPv4.

**Datas no frontend (fuso horário):**
```ts
// Correto — preserva o dia no fuso local (UTC-3 do Brasil)
const d = new Date()
const date = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
```

---

## Variáveis de Build do Frontend

Para builds de produção, defina antes de executar `npm run build`:

```env
VITE_API_URL=https://seu-backend.exemplo.com
```

Para Docker, passe como `build-arg`:

```bash
docker build --build-arg VITE_API_URL=https://seu-backend.exemplo.com .
```

---

## Deploy em Produção

O projeto está configurado para deploy no **EasyPanel** com Docker.

1. Configure as variáveis de ambiente no painel do EasyPanel
2. Aponte o webhook do WAHA para `https://seu-backend/api/webhooks/waha`
3. Execute `docker compose up --build` — as migrações rodam automaticamente

---

## Licença

Este projeto foi desenvolvido como Trabalho de Conclusão de Curso (TCC).
