import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, Search, Car, Phone, Calendar, FileText, User, Loader2, Wrench, Hash } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";

export const Route = createFileRoute("/app/configuracoes/clientes")({
  head: () => ({ meta: [{ title: "Clientes — GCT" }] }),
  component: Clientes,
});

type Cliente = {
  id: string;
  nome: string;
  telefone: string | null;
  veiculo: string | null;
  ano_veiculo: string | null;
  placa: string | null;
  ultimo_atendimento: string | null;
  servico_realizado: string | null;
  resumo: string | null;
};

function Clientes() {
  const [list, setList] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [busca, setBusca] = useState("");
  const [open, setOpen] = useState(false);
  const [edit, setEdit] = useState<Cliente | null>(null);
  const [perfil, setPerfil] = useState<Cliente | null>(null);

  useEffect(() => {
    api.get<Cliente[]>("/clients")
      .then(setList)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = list.filter((c) =>
    [c.nome, c.telefone, c.placa, c.veiculo]
      .some((v) => v?.toLowerCase().includes(busca.toLowerCase()))
  );

  const salvar = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const body = {
      nome: String(f.get("nome")),
      telefone: String(f.get("telefone") || ""),
      veiculo: String(f.get("veiculo") || ""),
      ano_veiculo: String(f.get("ano_veiculo") || ""),
      placa: String(f.get("placa") || ""),
      ultimo_atendimento: String(f.get("ultimo_atendimento") || "") || null,
      servico_realizado: String(f.get("servico_realizado") || ""),
      resumo: String(f.get("resumo") || ""),
    };
    setSaving(true);
    try {
      if (edit) {
        const updated = await api.put<Cliente>(`/clients/${edit.id}`, body);
        setList((arr) => arr.map((c) => (c.id === edit.id ? updated : c)));
      } else {
        const created = await api.post<Cliente>("/clients", body);
        setList((arr) => [...arr, created]);
      }
      setOpen(false);
      setEdit(null);
    } catch { /* ignora */ } finally {
      setSaving(false);
    }
  };

  const deletar = async (id: string) => {
    await api.delete(`/clients/${id}`).catch(() => {});
    setList((arr) => arr.filter((c) => c.id !== id));
  };

  const abrirNovo = () => { setEdit(null); setOpen(true); };
  const abrirEdit = (c: Cliente) => { setEdit(c); setOpen(true); };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Clientes</h1>
          <p className="text-sm text-muted-foreground">Histórico de clientes e veículos.</p>
        </div>
        <Button onClick={abrirNovo}><Plus className="mr-1 h-4 w-4" /> Novo cliente</Button>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar por nome, placa..." className="pl-9" />
      </div>

      <div className="rounded-xl border bg-card">
        {loading ? (
          <div className="flex justify-center py-12"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cliente</TableHead>
                <TableHead>Telefone</TableHead>
                <TableHead>Veículo / Ano</TableHead>
                <TableHead>Placa</TableHead>
                <TableHead>Último atendimento</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="py-10 text-center text-sm text-muted-foreground">
                    Nenhum cliente cadastrado.
                  </TableCell>
                </TableRow>
              )}
              {filtered.map((c) => (
                <TableRow key={c.id}>
                  <TableCell>
                    <button type="button" onClick={() => setPerfil(c)} className="group text-left">
                      <p className="cursor-pointer font-medium text-primary underline-offset-2 group-hover:underline">{c.nome}</p>
                      <p className="line-clamp-1 text-xs text-muted-foreground">
                        {c.servico_realizado ?? c.resumo ?? "—"}
                      </p>
                    </button>
                  </TableCell>
                  <TableCell>{c.telefone ?? "—"}</TableCell>
                  <TableCell>
                    {c.veiculo ?? "—"}
                    {c.ano_veiculo ? <span className="ml-1 text-xs text-muted-foreground">({c.ano_veiculo})</span> : null}
                  </TableCell>
                  <TableCell>{c.placa ?? "—"}</TableCell>
                  <TableCell>{c.ultimo_atendimento ?? "—"}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" onClick={() => abrirEdit(c)}><Pencil className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="icon" onClick={() => deletar(c.id)}><Trash2 className="h-4 w-4" /></Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Dialog: Criar / Editar */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>{edit ? "Editar cliente" : "Novo cliente"}</DialogTitle></DialogHeader>
          <form onSubmit={salvar} className="space-y-3">
            <div className="space-y-2"><Label>Nome</Label><Input name="nome" required defaultValue={edit?.nome} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2"><Label>Telefone</Label><Input name="telefone" defaultValue={edit?.telefone ?? ""} /></div>
              <div className="space-y-2"><Label>Placa</Label><Input name="placa" defaultValue={edit?.placa ?? ""} /></div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-2 space-y-2"><Label>Veículo</Label><Input name="veiculo" placeholder="Ex: Onix, Fiesta..." defaultValue={edit?.veiculo ?? ""} /></div>
              <div className="space-y-2"><Label>Ano</Label><Input name="ano_veiculo" placeholder="2024" maxLength={4} defaultValue={edit?.ano_veiculo ?? ""} /></div>
            </div>
            <div className="space-y-2"><Label>Último atendimento</Label><Input name="ultimo_atendimento" type="date" defaultValue={edit?.ultimo_atendimento ?? ""} /></div>
            <div className="space-y-2">
              <Label>Serviço realizado</Label>
              <Input name="servico_realizado" placeholder="Ex: Troca de óleo, alinhamento..." defaultValue={edit?.servico_realizado ?? ""} />
            </div>
            <div className="space-y-2"><Label>Observações</Label><Textarea name="resumo" placeholder="Informações adicionais sobre o cliente ou atendimento..." defaultValue={edit?.resumo ?? ""} /></div>
            <DialogFooter>
              <Button type="submit" disabled={saving}>
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Salvar"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog: Perfil */}
      <Dialog open={!!perfil} onOpenChange={(v) => { if (!v) setPerfil(null); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10">
                <User className="h-5 w-5 text-primary" />
              </div>
              Perfil do cliente
            </DialogTitle>
          </DialogHeader>
          {perfil && (
            <div className="space-y-4">
              <p className="text-lg font-semibold">{perfil.nome}</p>
              <Separator />
              <div className="grid gap-3">
                {[
                  { Icon: Phone, label: "Telefone", value: perfil.telefone },
                  {
                    Icon: Car,
                    label: "Veículo",
                    value: perfil.veiculo
                      ? `${perfil.veiculo}${perfil.ano_veiculo ? ` (${perfil.ano_veiculo})` : ""}`
                      : null,
                  },
                  { Icon: Hash, label: "Placa", value: perfil.placa },
                  { Icon: Calendar, label: "Último atendimento", value: perfil.ultimo_atendimento },
                  { Icon: Wrench, label: "Serviço realizado", value: perfil.servico_realizado },
                  { Icon: FileText, label: "Observações", value: perfil.resumo },
                ].map(({ Icon, label, value }) => (
                  <div key={label} className="flex items-start gap-3 rounded-lg bg-muted/50 px-3 py-2.5">
                    <Icon className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">{label}</p>
                      <p className="text-sm font-medium">{value ?? "—"}</p>
                    </div>
                  </div>
                ))}
              </div>
              <DialogFooter className="gap-2">
                <Button variant="outline" onClick={() => setPerfil(null)}>Fechar</Button>
                <Button onClick={() => { abrirEdit(perfil); setPerfil(null); }}>
                  <Pencil className="mr-1.5 h-3.5 w-3.5" /> Editar
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
