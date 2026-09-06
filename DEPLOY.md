# Deploy do GCT no EasyPanel (Docker Compose)

## Serviços

| Serviço  | Porta | Domínio                          | Alias na rede   |
|----------|-------|----------------------------------|-----------------|
| backend  | 8080  | https://SUA-API.easypanel.host | `gct_backend`  |
| frontend | 80    | https://SEU-FRONT.easypanel.host     | `gct_frontend` |

Ambos entram na rede Docker externa `easypanel`, a mesma do WAHA e do Redis já existentes.

## Variáveis de ambiente

Configure no painel do EasyPanel (nunca por arquivo commitado). Os valores prontos
estão em `.env.easypanel`, que é ignorado pelo git.

Pontos de atenção:

- `DATABASE_URL` — Supabase do GCT (projeto `SEU_PROJETO`, região sa-east-1),
  sempre via **Session Pooler** (IPv4, porta 5432). A conexão direta é IPv6 e falha na VPS.
- `JWT_SECRET` — foi gerado um novo, diferente do Mecaflow. Não reaproveite segredo entre projetos.
- `CORS_ORIGINS` — precisa ser a URL **exata** do frontend, sem barra no final.
- `ANTHROPIC_API_KEY` — **vazio de propósito**: mantém o assistente interno desativado.
  A rota `/api/assistant/chat` responde 503 com mensagem amigável. Para reativar, basta
  preencher a variável e reiniciar o backend — não precisa rebuild.
- `VITE_API_URL` — é **build-arg**: vai compilado no bundle do frontend. Mudar exige
  **rebuild da imagem**, reiniciar não resolve.
- `WAHA_SESSION` — apenas fallback. Cada cliente tem sua própria sessão cadastrada no
  sistema (Configurações → Minha oficina), e é ela que manda no envio e no recebimento.

## Ordem do deploy

1. Suba o **backend**. Ele roda `alembic upgrade head` sozinho no start (ver `backend/Dockerfile`).
2. Confira o health: `GET https://SUA-API.easypanel.host/health` → `{"status":"ok"}`.
3. Suba o **frontend** (só inicia depois do backend ficar healthy).
4. Crie o superadmin, se o banco for novo:
   `python -m scripts.create_superadmin --name "Grupo GCT" --email <email> --password <senha>`
5. No WAHA, aponte o webhook da sessão do cliente para:
   `https://SUA-API.easypanel.host/api/webhooks/waha`

## Integração com o n8n

O bloqueio do bot (quando um humano assume a conversa) é gravado no Redis com a chave:

```
gct_{sessao_waha}_{chat_id}_block
```

Exemplo: `gct_heberth_5511999999999@c.us_block`.

O prefixo `gct_` existe porque o Redis é compartilhado com o Mecaflow, que usa
`CloudSolutions_{chat_id}_block`. **O fluxo do n8n do GCT precisa ler exatamente esse
formato novo**, senão o bot vai responder por cima do atendente humano.

## Multi-cliente

Cada cliente do grupo é um registro de "oficina" no banco, com sua própria sessão WAHA,
seus dados e seu prompt de bot. O isolamento é feito pelo `workshop_id` embutido no token
após a escolha do cliente na tela de seleção. Um usuário `SUPERADMIN` enxerga todos os
clientes; os demais, apenas o seu.
