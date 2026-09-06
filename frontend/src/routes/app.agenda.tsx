import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Plus, Trash2, Loader2, Car, Phone, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";

export const Route = createFileRoute("/app/agenda")({
  head: () => ({ meta: [{ title: "Agenda — GCT" }] }),
  component: Agenda,
});

type Evento = {
  id: string;
  data: string;
  hora: string;
  titulo: string;
  cliente: string;
  veiculo: string | null;
  telefone: string | null;
};

const HOJE = new Date();
const fmt = (d: Date) => {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
};
const DIAS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

function Agenda() {
  const [ref, setRef] = useState(new Date(HOJE.getFullYear(), HOJE.getMonth(), 1));
  const [eventos, setEventos] = useState<Evento[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [open, setOpen] = useState(false);
  const [diaSel, setDiaSel] = useState<string>(fmt(HOJE));
  const [openConfirm, setOpenConfirm] = useState(false);
  const [toDelete, setToDelete] = useState<Evento | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [openEdit, setOpenEdit] = useState(false);
  const [toEdit, setToEdit] = useState<Evento | null>(null);

  useEffect(() => {
    api.get<Evento[]>("/appointments")
      .then(setEventos)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const dias = useMemo(() => {
    const inicio = new Date(ref.getFullYear(), ref.getMonth(), 1);
    const fim = new Date(ref.getFullYear(), ref.getMonth() + 1, 0);
    const cells: (Date | null)[] = [];
    for (let i = 0; i < inicio.getDay(); i++) cells.push(null);
    for (let d = 1; d <= fim.getDate(); d++) cells.push(new Date(ref.getFullYear(), ref.getMonth(), d));
    while (cells.length % 7 !== 0) cells.push(null);
    return cells;
  }, [ref]);

  const mesAno = ref.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
  const evDia = (d: string) => eventos.filter((e) => e.data === d).sort((a, b) => a.hora.localeCompare(b.hora));

  const criar = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setSaving(true);
    try {
      const novo = await api.post<Evento>("/appointments", {
        data: String(f.get("data")),
        hora: String(f.get("hora")),
        titulo: String(f.get("titulo")),
        cliente: String(f.get("cliente")),
        veiculo: String(f.get("veiculo") || "") || null,
        telefone: String(f.get("telefone") || "") || null,
      });
      setEventos((arr) => [...arr, novo]);
      setOpen(false);
    } catch { /* ignora */ } finally {
      setSaving(false);
    }
  };

  const abrirEdit = (ev: Evento) => {
    setToEdit(ev);
    setOpenEdit(true);
  };

  const salvarEdit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!toEdit) return;
    const f = new FormData(e.currentTarget);
    const body = {
      data: toEdit.data,
      hora: toEdit.hora,
      titulo: toEdit.titulo,
      cliente: toEdit.cliente,
      veiculo: String(f.get("veiculo") || "") || null,
      telefone: String(f.get("telefone") || "") || null,
    };
    try {
      const updated = await api.put<Evento>(`/appointments/${toEdit.id}`, body);
      setEventos((arr) => arr.map((e) => (e.id === toEdit.id ? updated : e)));
      setOpenEdit(false);
      setToEdit(null);
    } catch { /* ignora */ }
  };

  const confirmarDeletar = (ev: Evento) => {
    setToDelete(ev);
    setOpenConfirm(true);
  };

  const executarDeletar = async () => {
    if (!toDelete) return;
    setDeleting(true);
    try {
      await api.delete(`/appointments/${toDelete.id}`);
      setEventos((arr) => arr.filter((e) => e.id !== toDelete.id));
      setOpenConfirm(false);
      setToDelete(null);
    } catch { /* ignora */ } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Agenda</h1>
          <p className="text-sm text-muted-foreground">Visualize e gerencie agendamentos.</p>
        </div>
        <Button onClick={() => setOpen(true)}><Plus className="mr-1 h-4 w-4" /> Novo agendamento</Button>
      </div>

      {loading ? (
        <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
          <div className="rounded-xl border bg-card">
            <div className="flex items-center justify-between border-b p-4">
              <h2 className="font-display text-lg font-semibold capitalize">{mesAno}</h2>
              <div className="flex gap-1">
                <Button variant="ghost" size="icon" onClick={() => setRef(new Date(ref.getFullYear(), ref.getMonth() - 1, 1))}>
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm" onClick={() => setRef(new Date(HOJE.getFullYear(), HOJE.getMonth(), 1))}>Hoje</Button>
                <Button variant="ghost" size="icon" onClick={() => setRef(new Date(ref.getFullYear(), ref.getMonth() + 1, 1))}>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="grid grid-cols-7 border-b text-center text-xs font-medium text-muted-foreground">
              {DIAS.map((d) => <div key={d} className="py-2">{d}</div>)}
            </div>
            <div className="grid grid-cols-7">
              {dias.map((d, i) => {
                if (!d) return <div key={i} className="h-24 border-b border-r bg-muted/20" />;
                const k = fmt(d);
                const evs = evDia(k);
                const isHoje = k === fmt(HOJE);
                const isSel = k === diaSel;
                return (
                  <button
                    key={i}
                    onClick={() => setDiaSel(k)}
                    className={`h-24 border-b border-r p-1.5 text-left transition hover:bg-muted/40 ${
                      isSel ? "bg-primary/5 ring-1 ring-inset ring-primary/30" : ""
                    }`}
                  >
                    <span className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs ${
                      isHoje ? "bg-primary text-primary-foreground font-semibold" : ""
                    }`}>{d.getDate()}</span>
                    <div className="mt-1 space-y-0.5">
                      {evs.slice(0, 2).map((e) => (
                        <div key={e.id} className="truncate rounded bg-primary/15 px-1 text-[10px] text-primary">
                          {e.hora} {e.titulo}
                        </div>
                      ))}
                      {evs.length > 2 && <div className="text-[10px] text-muted-foreground">+{evs.length - 2}</div>}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="rounded-xl border bg-card p-4">
            <h3 className="font-display font-semibold">
              {new Date(diaSel + "T00:00:00").toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" })}
            </h3>
            <div className="mt-4 space-y-2">
              {evDia(diaSel).length === 0 && <p className="text-sm text-muted-foreground">Sem agendamentos.</p>}
              {evDia(diaSel).map((e) => (
                <div key={e.id} className="flex gap-3 rounded-lg border p-3">
                  <div className="flex h-12 w-14 flex-col items-center justify-center rounded-md bg-primary/10 text-primary">
                    <span className="text-sm font-bold">{e.hora}</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">{e.titulo}</p>
                    <p className="text-sm text-muted-foreground">{e.cliente}</p>
                    {e.veiculo && (
                      <p className="flex items-center gap-1 text-xs text-muted-foreground mt-0.5">
                        <Car className="h-3 w-3 shrink-0" />
                        {e.veiculo}
                      </p>
                    )}
                    {e.telefone && (
                      <a
                        href={(() => {
                          const digits = e.telefone!.replace(/\D/g, "");
                          const num = digits.startsWith("55") ? digits : `55${digits}`;
                          return `https://wa.me/${num}`;
                        })()}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 text-xs text-green-600 hover:underline mt-0.5"
                      >
                        <Phone className="h-3 w-3 shrink-0" />
                        {e.telefone.replace(/@.*$/, "")}
                      </a>
                    )}
                  </div>
                  <div className="flex shrink-0 self-start flex-col gap-0.5">
                    <Button variant="ghost" size="icon" onClick={() => abrirEdit(e)}>
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => confirmarDeletar(e)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Dialog: Novo agendamento */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Novo agendamento</DialogTitle></DialogHeader>
          <form onSubmit={criar} className="space-y-3">
            <div className="space-y-2"><Label>Cliente</Label><Input name="cliente" required /></div>
            <div className="space-y-2"><Label>Serviço</Label><Input name="titulo" required /></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2"><Label>Veículo</Label><Input name="veiculo" placeholder="Ex: Onix, Fiesta..." /></div>
              <div className="space-y-2"><Label>Telefone</Label><Input name="telefone" placeholder="11999999999" /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2"><Label>Data</Label><Input name="data" type="date" required defaultValue={diaSel} /></div>
              <div className="space-y-2"><Label>Hora</Label><Input name="hora" type="time" required /></div>
            </div>
            <DialogFooter>
              <Button type="submit" disabled={saving}>
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Criar"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog: Editar agendamento */}
      <Dialog open={openEdit} onOpenChange={(v) => { setOpenEdit(v); if (!v) setToEdit(null); }}>
        <DialogContent className="max-w-sm">
          <DialogHeader><DialogTitle>Editar agendamento</DialogTitle></DialogHeader>
          <form onSubmit={salvarEdit} className="space-y-3">
            <div className="space-y-2">
              <Label>Veículo</Label>
              <Input name="veiculo" placeholder="Ex: Onix 2014, Fiesta..." defaultValue={toEdit?.veiculo ?? ""} />
            </div>
            <div className="space-y-2">
              <Label>Telefone (WhatsApp)</Label>
              <Input name="telefone" placeholder="5511999999999" defaultValue={toEdit?.telefone ?? ""} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpenEdit(false)}>Cancelar</Button>
              <Button type="submit">Salvar</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog: Confirmar exclusão */}
      <Dialog open={openConfirm} onOpenChange={(v) => { setOpenConfirm(v); if (!v) setToDelete(null); }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Cancelar agendamento?</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Você está prestes a cancelar o agendamento de{" "}
              <span className="font-medium text-foreground">{toDelete?.cliente}</span> às{" "}
              <span className="font-medium text-foreground">{toDelete?.hora}</span>.
            </p>
            {toDelete?.telefone ? (
              <div className="rounded-lg border border-green-200 bg-green-50 px-3 py-2.5 text-sm dark:border-green-900 dark:bg-green-950/30">
                <p className="font-medium text-green-800 dark:text-green-300">Mensagem automática no WhatsApp</p>
                <p className="mt-0.5 text-green-700 dark:text-green-400">
                  Uma mensagem de cancelamento será enviada para{" "}
                  <span className="font-medium">{toDelete.telefone}</span> informando o cliente.
                </p>
              </div>
            ) : (
              <p className="text-xs text-amber-600 dark:text-amber-400">
                Nenhum telefone cadastrado — o cliente não será notificado automaticamente.
              </p>
            )}
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setOpenConfirm(false)}>Voltar</Button>
            <Button variant="destructive" onClick={executarDeletar} disabled={deleting}>
              {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : "Confirmar cancelamento"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
