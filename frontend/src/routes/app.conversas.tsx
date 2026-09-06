import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import { Search, Send, MoreVertical, CheckCircle2, Tag, Loader2, RotateCcw, Pencil, Bot, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";

export const Route = createFileRoute("/app/conversas")({
  head: () => ({ meta: [{ title: "Conversas — GCT" }] }),
  component: Conversas,
});

type ConvStatus = "BOT" | "HUMAN" | "UNASSIGNED" | "RESOLVED";
type Label = { id: string; name: string; color: string | null };
type Conv = {
  id: string;
  waha_chat_id: string;
  lead_name: string;
  lead_phone: string;
  status: ConvStatus;
  assigned_agent_id: string | null;
  assigned_agent_name: string | null;
  unread_count: number;
  last_message: string | null;
  last_message_at: string | null;
  labels: Label[];
};
type Msg = {
  id: string;
  conversation_id: string;
  content: string | null;
  type: "TEXT" | "IMAGE" | "AUDIO" | "DOCUMENT";
  sender_name: string;
  is_from_lead: boolean;
  created_at: string;
};

function badgeStyle(color: string | null) {
  return { backgroundColor: color ?? "#64748b", color: "#fff" };
}

type Etiqueta = { id: string; nome: string; cor: string | null };

const TAB_MAP: Record<string, string> = {
  todas: "ALL",
  abertas: "UNASSIGNED",
  resolvidas: "RESOLVED",
};

function fmtHora(iso: string | null) {
  if (!iso) return "";
  const d = new Date(iso);
  const hoje = new Date();
  if (d.toDateString() === hoje.toDateString())
    return d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
}

const BASE_URL = (import.meta.env?.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

function Conversas() {
  const [conversas, setConversas] = useState<Conv[]>([]);
  const [loadingConvs, setLoadingConvs] = useState(true);
  const [tab, setTab] = useState<"todas" | "abertas" | "resolvidas">("todas");
  const [busca, setBusca] = useState("");
  const [filtroEtiquetas, setFiltroEtiquetas] = useState<Set<string>>(new Set());
  const [sel, setSel] = useState<string | null>(null);

  const [mensagens, setMensagens] = useState<Msg[]>([]);
  const [loadingMsgs, setLoadingMsgs] = useState(false);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);

  const [etiquetaDialogOpen, setEtiquetaDialogOpen] = useState(false);
  const [etiquetasSel, setEtiquetasSel] = useState<string[]>([]);
  const [salvandoEtiquetas, setSalvandoEtiquetas] = useState(false);
  const [labelsDisponiveis, setLabelsDisponiveis] = useState<Etiqueta[]>([]);

  const [nomeDialogOpen, setNomeDialogOpen] = useState(false);
  const [nomeEdit, setNomeEdit] = useState("");
  const [salvandoNome, setSalvandoNome] = useState(false);

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletando, setDeletando] = useState(false);

  const endRef = useRef<HTMLDivElement>(null);

  const ativa = conversas.find((c) => c.id === sel) ?? null;

  // Carregar conversas
  const carregarConversas = async (t: string) => {
    setLoadingConvs(true);
    try {
      const data = await api.get<Conv[]>(`/conversations?tab=${TAB_MAP[t]}`);
      setConversas(data);
      if (!sel && data.length > 0) setSel(data[0].id);
    } catch {
      // ignora erro silenciosamente
    } finally {
      setLoadingConvs(false);
    }
  };

  useEffect(() => { carregarConversas(tab); }, [tab]);

  useEffect(() => {
    api.get<Etiqueta[]>("/labels").then(setLabelsDisponiveis).catch(() => {});
  }, []);

  // Carregar mensagens e marcar como lida ao abrir conversa
  useEffect(() => {
    if (!sel) return;
    setLoadingMsgs(true);
    api.get<{ items: Msg[] }>(`/conversations/${sel}/messages`)
      .then((data) => setMensagens(data.items))
      .catch(() => {})
      .finally(() => setLoadingMsgs(false));
    api.patch(`/conversations/${sel}/read`).catch(() => {});
    setConversas((prev) =>
      prev.map((c) => (c.id === sel ? { ...c, unread_count: 0 } : c))
    );
  }, [sel]);

  // Auto-scroll para última mensagem
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensagens]);

  // SSE — atualizações em tempo real
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const url = token
      ? `${BASE_URL}/api/sse/events?token=${token}`
      : `${BASE_URL}/api/sse/events`;
    const es = new EventSource(url);

    es.addEventListener("message", (e) => {
      const raw = JSON.parse(e.data) as {
        messageId: string;
        conversationId: string;
        content: string | null;
        type: "TEXT" | "IMAGE" | "AUDIO" | "DOCUMENT";
        senderName: string;
        isFromLead: boolean;
        createdAt: string;
      };
      const msg: Msg = {
        id: raw.messageId,
        conversation_id: raw.conversationId,
        content: raw.content,
        type: raw.type,
        sender_name: raw.senderName,
        is_from_lead: raw.isFromLead,
        created_at: raw.createdAt,
      };
      if (raw.conversationId === sel) {
        setMensagens((prev) => {
          if (prev.some((m) => m.id === msg.id)) return prev;
          return [...prev, msg];
        });
      }
      // Atualiza last_message no painel esquerdo
      setConversas((prev) =>
        prev.map((c) =>
          c.id === raw.conversationId
            ? { ...c, last_message: raw.content, unread_count: c.id === sel ? 0 : c.unread_count + 1 }
            : c
        )
      );
    });

    es.addEventListener("conversation", (e) => {
      const updated = JSON.parse(e.data) as Partial<Conv> & { id: string };
      setConversas((prev) =>
        prev.map((c) => (c.id === updated.id ? { ...c, ...updated } : c))
      );
    });

    es.onerror = () => es.close();
    return () => es.close();
  }, [sel]);

  const filtradas = useMemo(() => {
    return conversas.filter((c) => {
      const passaBusca = !busca || c.lead_name.toLowerCase().includes(busca.toLowerCase());
      const passaEtiqueta = filtroEtiquetas.size === 0 || c.labels.some((l) => filtroEtiquetas.has(l.name));
      return passaBusca && passaEtiqueta;
    });
  }, [conversas, busca, filtroEtiquetas]);

  const enviar = async () => {
    if (!sel || !texto.trim() || enviando) return;
    const conteudo = texto.trim();
    setTexto("");
    setEnviando(true);
    try {
      const msg = await api.post<Msg>(`/conversations/${sel}/messages`, { content: conteudo });
      setMensagens((prev) => {
        if (prev.some((m) => m.id === msg.id)) return prev;
        return [...prev, msg];
      });
    } catch {
      setTexto(conteudo);
    } finally {
      setEnviando(false);
    }
  };

  const resolverConversa = async () => {
    if (!sel) return;
    try {
      const updated = await api.patch<Conv>(`/conversations/${sel}/resolve`);
      setConversas((prev) =>
        prev.map((c) => (c.id === sel ? (updated ?? { ...c, status: "RESOLVED" as ConvStatus }) : c))
      );
      toast.success("Conversa resolvida");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao resolver conversa");
    }
  };

  const reabrirConversa = async () => {
    if (!sel) return;
    try {
      const updated = await api.patch<Conv>(`/conversations/${sel}/reopen`);
      setConversas((prev) =>
        prev.map((c) => (c.id === sel ? (updated ?? { ...c, status: "UNASSIGNED" as ConvStatus }) : c))
      );
      toast.success("Conversa reaberta");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao reabrir conversa");
    }
  };

  const ativarBot = async () => {
    if (!sel) return;
    try {
      const updated = await api.patch<Conv>(`/conversations/${sel}/bot`);
      setConversas((prev) =>
        prev.map((c) => (c.id === sel ? (updated ?? { ...c, status: "BOT" as ConvStatus }) : c))
      );
      toast.success("Bot ativado");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao ativar bot");
    }
  };

  const abrirEditarNome = () => {
    if (ativa) {
      setNomeEdit(ativa.lead_name);
      setNomeDialogOpen(true);
    }
  };

  const salvarNome = async () => {
    if (!sel || !nomeEdit.trim()) return;
    setSalvandoNome(true);
    try {
      const updated = await api.patch<Conv>(`/conversations/${sel}/name`, { lead_name: nomeEdit.trim() });
      setConversas((prev) => prev.map((c) => (c.id === sel ? (updated ?? { ...c, lead_name: nomeEdit.trim() }) : c)));
      setNomeDialogOpen(false);
      toast.success("Nome atualizado");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao salvar nome");
    } finally {
      setSalvandoNome(false);
    }
  };

  const deletarConversa = async () => {
    if (!sel) return;
    setDeletando(true);
    try {
      await api.delete(`/conversations/${sel}`);
      setConversas((prev) => prev.filter((c) => c.id !== sel));
      setSel(null);
      setMensagens([]);
      setDeleteDialogOpen(false);
      toast.success("Conversa removida");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao remover conversa");
    } finally {
      setDeletando(false);
    }
  };

  const abrirGerenciarEtiquetas = () => {
    if (ativa) {
      setEtiquetasSel(ativa.labels.map((l) => l.name));
      setEtiquetaDialogOpen(true);
    }
  };

  const salvarEtiquetas = async () => {
    if (!sel || !ativa) return;
    setSalvandoEtiquetas(true);
    try {
      const nomesAtuais = ativa.labels.map((l) => l.name);
      const adicionar = etiquetasSel.filter((n) => !nomesAtuais.includes(n));
      const remover = ativa.labels.filter((l) => !etiquetasSel.includes(l.name));

      await Promise.all([
        ...adicionar.map((name) => {
          const found = labelsDisponiveis.find((l) => l.nome === name);
          return api.post(`/conversations/${sel}/labels`, { name, color: found?.cor ?? null });
        }),
        ...remover.map((l) => api.delete(`/conversations/${sel}/labels/${l.id}`)),
      ]);

      // Recarrega conversa para pegar labels atualizados
      const updated = await api.get<Conv>(`/conversations/${sel}`);
      setConversas((prev) => prev.map((c) => (c.id === sel ? updated : c)));
      setEtiquetaDialogOpen(false);
    } catch { /* ignora */ } finally {
      setSalvandoEtiquetas(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-display text-2xl font-bold">Conversas</h1>
        <p className="text-sm text-muted-foreground">Atenda seus clientes em um inbox unificado.</p>
      </div>

      <div className="grid h-[calc(100vh-12rem)] grid-cols-1 gap-4 lg:grid-cols-[360px_1fr]">
        {/* Painel esquerdo */}
        <div className="flex flex-col overflow-hidden rounded-xl border bg-card">
          <div className="space-y-3 border-b p-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar conversa..." className="pl-9" />
            </div>
            <Tabs value={tab} onValueChange={(v) => setTab(v as typeof tab)}>
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="todas">Todas</TabsTrigger>
                <TabsTrigger value="abertas">Abertas</TabsTrigger>
                <TabsTrigger value="resolvidas">Concluídas</TabsTrigger>
              </TabsList>
            </Tabs>
            {labelsDisponiveis.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {labelsDisponiveis.map((l) => {
                  const ativo = filtroEtiquetas.has(l.nome);
                  return (
                    <button
                      key={l.id}
                      type="button"
                      onClick={() =>
                        setFiltroEtiquetas((prev) => {
                          const next = new Set(prev);
                          if (next.has(l.nome)) next.delete(l.nome);
                          else next.add(l.nome);
                          return next;
                        })
                      }
                      className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-all ${
                        ativo ? "border-transparent text-white" : "border-border text-muted-foreground hover:bg-muted"
                      }`}
                      style={ativo ? { backgroundColor: l.cor ?? "#64748b" } : {}}
                    >
                      <span
                        className="h-2 w-2 rounded-full shrink-0"
                        style={{ backgroundColor: ativo ? "#ffffff80" : (l.cor ?? "#64748b") }}
                      />
                      {l.nome}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div className="flex-1 overflow-y-auto">
            {loadingConvs && (
              <div className="flex justify-center p-6">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            )}
            {!loadingConvs && filtradas.length === 0 && (
              <p className="p-6 text-center text-sm text-muted-foreground">Nenhuma conversa.</p>
            )}
            {filtradas.map((c) => (
              <button
                key={c.id}
                onClick={() => setSel(c.id)}
                className={`block w-full border-b p-3 text-left transition hover:bg-muted/60 ${sel === c.id ? "bg-muted" : ""}`}
              >
                <div className="flex items-start gap-2.5">
                  <LeadAvatar name={c.lead_name} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-1">
                      <span className="truncate font-medium">{c.lead_name}</span>
                      <div className="flex shrink-0 items-center gap-1.5">
                        {c.status === "RESOLVED" && <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />}
                        {c.unread_count > 0 && (
                          <Badge className="h-4 min-w-4 bg-primary px-1 text-[10px] text-primary-foreground">
                            {c.unread_count}
                          </Badge>
                        )}
                        <span className="text-xs text-muted-foreground">{fmtHora(c.last_message_at)}</span>
                      </div>
                    </div>
                    <p className="mt-0.5 truncate text-sm text-muted-foreground">{c.last_message ?? "—"}</p>
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {c.labels.map((l) => (
                        <Badge key={l.id} className="border-0 text-xs" style={badgeStyle(l.color)}>{l.name}</Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Painel direito */}
        <div className="flex flex-col overflow-hidden rounded-xl border bg-card">
          {ativa ? (
            <>
              <div className="flex items-center justify-between border-b p-4">
                <div className="flex items-center gap-3">
                  <LeadAvatar name={ativa.lead_name} size="md" />
                  <div>
                  <div className="flex items-center gap-2">
                    <p className="font-semibold">{ativa.lead_name}</p>
                    <button
                      onClick={abrirEditarNome}
                      className="text-muted-foreground hover:text-foreground transition-colors"
                      title="Editar nome"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                    {ativa.status === "RESOLVED" && (
                      <Badge className="border-0 bg-green-100 text-xs text-green-700 dark:bg-green-900/20 dark:text-green-400">Resolvida</Badge>
                    )}
                    {ativa.status === "HUMAN" && (
                      <Badge className="border-0 bg-blue-100 text-xs text-blue-700 dark:bg-blue-900/20 dark:text-blue-400">Humano</Badge>
                    )}
                    {ativa.status === "BOT" && (
                      <Badge className="border-0 bg-purple-100 text-xs text-purple-700 dark:bg-purple-900/20 dark:text-purple-400">Bot</Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">{ativa.lead_phone}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex flex-wrap gap-1.5">
                    {ativa.labels.map((l) => (
                      <Badge key={l.id} className="border-0" style={badgeStyle(l.color)}>{l.name}</Badge>
                    ))}
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-52">
                      {ativa.status !== "RESOLVED" ? (
                        <DropdownMenuItem onClick={resolverConversa} className="gap-2">
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                          Resolver conversa
                        </DropdownMenuItem>
                      ) : (
                        <DropdownMenuItem onClick={reabrirConversa} className="gap-2">
                          <RotateCcw className="h-4 w-4 text-blue-500" />
                          Reabrir conversa
                        </DropdownMenuItem>
                      )}
                      {ativa.status === "HUMAN" && (
                        <>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={ativarBot} className="gap-2">
                            <Bot className="h-4 w-4 text-purple-500" />
                            Ativar bot
                          </DropdownMenuItem>
                        </>
                      )}
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={abrirGerenciarEtiquetas} className="gap-2">
                        <Tag className="h-4 w-4" />
                        Gerenciar etiquetas
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => setDeleteDialogOpen(true)} className="gap-2 text-destructive focus:text-destructive">
                        <Trash2 className="h-4 w-4" />
                        Limpar conversa
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>

              <div className="flex-1 space-y-3 overflow-y-auto bg-muted/30 p-4">
                {loadingMsgs ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                  </div>
                ) : mensagens.length === 0 ? (
                  <p className="text-center text-sm text-muted-foreground">Nenhuma mensagem ainda.</p>
                ) : (
                  mensagens.map((m) => (
                    <Mensagem key={m.id} texto={m.content ?? ""} dele={m.is_from_lead} nome={m.sender_name} />
                  ))
                )}
                <div ref={endRef} />
              </div>

              <div className="flex gap-2 border-t p-3">
                <Input
                  placeholder="Digite uma mensagem..."
                  disabled={ativa.status === "RESOLVED" || enviando}
                  value={texto}
                  onChange={(e) => setTexto(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && enviar()}
                />
                <Button
                  size="icon"
                  disabled={ativa.status === "RESOLVED" || !texto.trim() || enviando}
                  onClick={enviar}
                >
                  {enviando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </Button>
              </div>
            </>
          ) : (
            <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
              Selecione uma conversa
            </div>
          )}
        </div>
      </div>

      {/* Dialog: Editar nome */}
      <Dialog open={nomeDialogOpen} onOpenChange={setNomeDialogOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Editar nome do cliente</DialogTitle>
          </DialogHeader>
          <Input
            value={nomeEdit}
            onChange={(e) => setNomeEdit(e.target.value)}
            placeholder="Nome do cliente"
            onKeyDown={(e) => e.key === "Enter" && salvarNome()}
            autoFocus
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setNomeDialogOpen(false)}>Cancelar</Button>
            <Button onClick={salvarNome} disabled={salvandoNome || !nomeEdit.trim()}>
              {salvandoNome ? <Loader2 className="h-4 w-4 animate-spin" /> : "Salvar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog: Confirmar exclusão de conversa */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Limpar conversa?</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            Todas as mensagens de{" "}
            <span className="font-medium text-foreground">{ativa?.lead_name}</span> serão
            removidas permanentemente. Esta ação não pode ser desfeita.
          </p>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>Cancelar</Button>
            <Button variant="destructive" onClick={deletarConversa} disabled={deletando}>
              {deletando ? <Loader2 className="h-4 w-4 animate-spin" /> : "Limpar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog: Gerenciar etiquetas */}
      <Dialog open={etiquetaDialogOpen} onOpenChange={setEtiquetaDialogOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Gerenciar etiquetas</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            Selecione as etiquetas para <span className="font-medium text-foreground">{ativa?.lead_name}</span>.
          </p>
          <div className="flex flex-wrap gap-2 py-1">
            {labelsDisponiveis.length === 0 ? (
              <p className="text-sm text-muted-foreground">Nenhuma etiqueta cadastrada.</p>
            ) : (
              labelsDisponiveis.map((l) => {
                const ativo = etiquetasSel.includes(l.nome);
                return (
                  <button
                    key={l.id}
                    type="button"
                    onClick={() =>
                      setEtiquetasSel((prev) =>
                        prev.includes(l.nome) ? prev.filter((n) => n !== l.nome) : [...prev, l.nome]
                      )
                    }
                    className={`rounded-full border px-3 py-1 text-sm font-medium transition-all ${
                      ativo
                        ? "border-transparent ring-2 ring-offset-1 ring-primary/40 text-white"
                        : "border-border bg-background text-muted-foreground hover:bg-muted"
                    }`}
                    style={ativo ? { backgroundColor: l.cor ?? "#64748b" } : {}}
                  >
                    {l.nome}
                  </button>
                );
              })
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEtiquetaDialogOpen(false)}>Cancelar</Button>
            <Button onClick={salvarEtiquetas} disabled={salvandoEtiquetas}>
              {salvandoEtiquetas ? <Loader2 className="h-4 w-4 animate-spin" /> : "Salvar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function LeadAvatar({ name, size = "sm" }: { name: string; size?: "sm" | "md" }) {
  const initials = name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase() || "?";
  const sz = size === "md" ? "h-11 w-11 text-base" : "h-9 w-9 text-sm";
  return (
    <div className={`flex shrink-0 items-center justify-center rounded-full bg-primary/10 font-semibold text-primary ${sz}`}>
      {initials}
    </div>
  );
}

function Mensagem({ texto, dele, nome }: { texto: string; dele?: boolean; nome: string }) {
  return (
    <div className={`flex flex-col ${dele ? "items-start" : "items-end"}`}>
      <span className="mb-0.5 text-[11px] text-muted-foreground">{nome}</span>
      <div
        className={`max-w-xs rounded-2xl px-3 py-2 text-sm ${
          dele ? "bg-card" : "bg-primary text-primary-foreground"
        }`}
      >
        {texto}
      </div>
    </div>
  );
}
