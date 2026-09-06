import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { MessagesSquare, CalendarDays, CheckCircle2, Clock, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { getSession } from "@/lib/auth";

export const Route = createFileRoute("/app/")({
  head: () => ({ meta: [{ title: "Dashboard — GCT" }] }),
  component: Dashboard,
});

type Conv = {
  id: string;
  lead_name: string;
  last_message: string | null;
  status: string;
  unread_count: number;
  labels: { id: string; name: string; color: string | null }[];
};

type Agendamento = { id: string; data: string; hora: string; titulo: string; cliente: string };

function fmtHoje() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}


function statusBadge(status: string) {
  if (status === "RESOLVED") return { label: "Resolvida", cor: "bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400" };
  if (status === "HUMAN") return { label: "Humano", cor: "bg-blue-100 text-blue-700" };
  if (status === "BOT") return { label: "Bot", cor: "bg-purple-100 text-purple-700" };
  return { label: "Aberta", cor: "bg-primary/15 text-primary" };
}

function Dashboard() {
  const session = getSession();
  const [conversas, setConversas] = useState<Conv[]>([]);
  const [agendamentos, setAgendamentos] = useState<Agendamento[]>([]);
  const [abertas, setAbertas] = useState(0);
  const [resolvidas, setResolvidas] = useState(0);
  const [aguardando, setAguardando] = useState(0);

  useEffect(() => {
    const hoje = fmtHoje();
    Promise.all([
      api.get<Conv[]>("/conversations?tab=ALL"),
      api.get<Conv[]>("/conversations?tab=RESOLVED"),
      api.get<Agendamento[]>(`/appointments?data=${hoje}`),
    ]).then(([todas, resolved, ags]) => {
      setConversas(todas.slice(0, 3));
      const abertasCount = todas.filter((c) => c.status !== "RESOLVED").length;
      setAbertas(abertasCount);
      setResolvidas(resolved.length);
      setAguardando(todas.filter((c) => c.unread_count > 0).length);
      setAgendamentos(ags.sort((a, b) => a.hora.localeCompare(b.hora)));
    }).catch(() => {});
  }, []);

  const stats = [
    { label: "Conversas abertas", value: abertas, icon: MessagesSquare, tone: "text-primary" },
    { label: "Agendados hoje", value: agendamentos.length, icon: CalendarDays, tone: "text-primary" },
    { label: "Concluídas hoje", value: resolvidas, icon: CheckCircle2, tone: "text-success" },
    { label: "Aguardando resposta", value: aguardando, icon: Clock, tone: "text-warning" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold">
          Olá, {session?.user.name.split(" ")[0]} 👋
        </h1>
        <p className="text-sm text-muted-foreground">Visão geral da operação da oficina hoje.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => (
          <Card key={s.label}>
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">{s.label}</p>
                <p className="mt-2 text-3xl font-bold">{s.value}</p>
              </div>
              <s.icon className={`h-8 w-8 ${s.tone}`} />
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="text-base">Conversas recentes</CardTitle>
            <Link to="/app/conversas" className="inline-flex items-center text-sm text-primary hover:underline">
              Ver todas <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </Link>
          </CardHeader>
          <CardContent className="space-y-2">
            {conversas.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                Nenhuma conversa ainda.
              </p>
            ) : (
              conversas.map((c) => {
                const status = statusBadge(c.status);
                return (
                  <div key={c.id} className="flex items-center justify-between rounded-lg border p-3">
                    <div className="min-w-0 flex-1 pr-3">
                      <p className="font-medium">{c.lead_name}</p>
                      <p className="truncate text-sm text-muted-foreground">{c.last_message ?? "—"}</p>
                    </div>
                    {c.labels[0] ? (
                      <Badge
                        className="border-0 shrink-0"
                        style={{ backgroundColor: c.labels[0].color ?? "#64748b", color: "#fff" }}
                      >
                        {c.labels[0].name}
                      </Badge>
                    ) : (
                      <Badge className={status.cor + " border-0 shrink-0"}>{status.label}</Badge>
                    )}
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="text-base">Agendamentos de hoje</CardTitle>
            <Link to="/app/agenda" className="inline-flex items-center text-sm text-primary hover:underline">
              Abrir agenda <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </Link>
          </CardHeader>
          <CardContent className="space-y-2">
            {agendamentos.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                Nenhum agendamento para hoje.
              </p>
            ) : (
              agendamentos.map((a) => (
                <div key={a.id} className="flex gap-3 rounded-lg border p-3">
                  <div className="flex h-10 w-14 shrink-0 flex-col items-center justify-center rounded-md bg-primary/10 text-primary">
                    <span className="text-sm font-bold">{a.hora}</span>
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium">{a.titulo}</p>
                    <p className="truncate text-sm text-muted-foreground">{a.cliente}</p>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
