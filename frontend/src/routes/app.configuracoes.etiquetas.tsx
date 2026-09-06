import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";

export const Route = createFileRoute("/app/configuracoes/etiquetas")({
  head: () => ({ meta: [{ title: "Etiquetas — GCT" }] }),
  component: Etiquetas,
});

type Etiqueta = { id: string; nome: string; cor: string | null; descricao: string | null };

const CORES = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#64748b"];

function Etiquetas() {
  const [list, setList] = useState<Etiqueta[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [open, setOpen] = useState(false);
  const [edit, setEdit] = useState<Etiqueta | null>(null);
  const [cor, setCor] = useState(CORES[0]);

  useEffect(() => {
    api.get<Etiqueta[]>("/labels")
      .then(setList)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const abrirNovo = () => { setEdit(null); setCor(CORES[0]); setOpen(true); };
  const abrirEdit = (e: Etiqueta) => { setEdit(e); setCor(e.cor ?? CORES[0]); setOpen(true); };

  const salvar = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const body = {
      nome: String(f.get("nome")),
      descricao: String(f.get("descricao") || ""),
      cor,
    };
    setSaving(true);
    try {
      if (edit) {
        const updated = await api.put<Etiqueta>(`/labels/${edit.id}`, body);
        setList((arr) => arr.map((x) => (x.id === edit.id ? updated : x)));
      } else {
        const created = await api.post<Etiqueta>("/labels", body);
        setList((arr) => [...arr, created]);
      }
      setOpen(false);
      setEdit(null);
    } catch { /* ignora */ } finally {
      setSaving(false);
    }
  };

  const deletar = async (id: string) => {
    await api.delete(`/labels/${id}`).catch(() => {});
    setList((arr) => arr.filter((x) => x.id !== id));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold">Etiquetas</h1>
          <p className="text-sm text-muted-foreground">Organize conversas com cores e categorias.</p>
        </div>
        <Button onClick={abrirNovo}><Plus className="mr-1 h-4 w-4" /> Nova etiqueta</Button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {list.length === 0 && (
            <p className="col-span-full py-8 text-center text-sm text-muted-foreground">Nenhuma etiqueta cadastrada.</p>
          )}
          {list.map((e) => (
            <div key={e.id} className="rounded-xl border bg-card p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full" style={{ backgroundColor: e.cor ?? "#64748b" }} />
                  <span className="font-semibold">{e.nome}</span>
                </div>
                <div className="flex">
                  <Button variant="ghost" size="icon" onClick={() => abrirEdit(e)}><Pencil className="h-4 w-4" /></Button>
                  <Button variant="ghost" size="icon" onClick={() => deletar(e.id)}><Trash2 className="h-4 w-4" /></Button>
                </div>
              </div>
              {e.descricao && <p className="mt-2 text-sm text-muted-foreground">{e.descricao}</p>}
            </div>
          ))}
        </div>
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>{edit ? "Editar etiqueta" : "Nova etiqueta"}</DialogTitle></DialogHeader>
          <form onSubmit={salvar} className="space-y-3">
            <div className="space-y-2"><Label>Nome</Label><Input name="nome" required defaultValue={edit?.nome} /></div>
            <div className="space-y-2"><Label>Descrição</Label><Textarea name="descricao" defaultValue={edit?.descricao ?? ""} /></div>
            <div className="space-y-2">
              <Label>Cor</Label>
              <div className="flex flex-wrap gap-2">
                {CORES.map((c) => (
                  <button
                    key={c} type="button" onClick={() => setCor(c)}
                    className={`h-8 w-8 rounded-full border-2 transition ${cor === c ? "border-foreground scale-110" : "border-transparent"}`}
                    style={{ backgroundColor: c }}
                  />
                ))}
              </div>
            </div>
            <DialogFooter>
              <Button type="submit" disabled={saving}>
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Salvar"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
