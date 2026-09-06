import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Building2, LogOut, Plus, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";
import {
  clearAuth,
  getSession,
  isSuperadmin,
  setAuth,
  type TokenResponse,
} from "@/lib/auth";

export const Route = createFileRoute("/selecionar-cliente")({
  head: () => ({ meta: [{ title: "Selecionar cliente — GCT" }] }),
  beforeLoad: () => {
    if (typeof window === "undefined") return;
    if (!localStorage.getItem("access_token")) throw redirect({ to: "/login" });
  },
  component: SelecionarClientePage,
});

interface WorkshopItem {
  id: string;
  name: string;
  city: string | null;
  state: string | null;
}

function SelecionarClientePage() {
  const navigate = useNavigate();
  const [clientes, setClientes] = useState<WorkshopItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busca, setBusca] = useState("");
  const [entrando, setEntrando] = useState<string | null>(null);

  const [dialogAberto, setDialogAberto] = useState(false);
  const [novoNome, setNovoNome] = useState("");
  const [salvando, setSalvando] = useState(false);

  const session = getSession();
  const podeCriar = isSuperadmin();

  const carregar = async () => {
    setLoading(true);
    setError("");
    try {
      setClientes(await api.get<WorkshopItem[]>("/auth/workshops"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar clientes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void carregar();
  }, []);

  const filtrados = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    if (!termo) return clientes;
    return clientes.filter((c) => c.name.toLowerCase().includes(termo));
  }, [clientes, busca]);

  const entrar = async (id: string) => {
    setEntrando(id);
    setError("");
    try {
      const data = await api.post<TokenResponse>("/auth/select-workshop", {
        workshop_id: id,
      });
      setAuth(data);
      navigate({ to: "/app" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao entrar no cliente");
      setEntrando(null);
    }
  };

  const criarCliente = async (e: React.FormEvent) => {
    e.preventDefault();
    setSalvando(true);
    setError("");
    try {
      await api.post("/workshops", { name: novoNome });
      setNovoNome("");
      setDialogAberto(false);
      await carregar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar cliente");
    } finally {
      setSalvando(false);
    }
  };

  const sair = () => {
    clearAuth();
    navigate({ to: "/login" });
  };

  return (
    <div className="min-h-screen bg-background px-4 py-10">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center overflow-hidden rounded-lg bg-primary">
              <img src="/logo.jfif" alt="GCT" className="h-full w-full object-cover" />
            </div>
            <div>
              <h1 className="font-display text-2xl font-bold">Selecione um cliente</h1>
              <p className="text-sm text-muted-foreground">
                {session?.user.name
                  ? `Olá, ${session.user.name}. Escolha em qual cliente deseja trabalhar.`
                  : "Escolha em qual cliente deseja trabalhar."}
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={sair} title="Sair">
            <LogOut className="h-4 w-4" />
          </Button>
        </div>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Buscar cliente..."
              className="pl-9"
            />
          </div>
          {podeCriar && (
            <Button onClick={() => setDialogAberto(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Novo cliente
            </Button>
          )}
        </div>

        {error && (
          <p className="mt-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <div className="mt-6 space-y-2">
          {loading && <p className="text-sm text-muted-foreground">Carregando clientes...</p>}

          {!loading && filtrados.length === 0 && (
            <div className="rounded-xl border border-dashed p-10 text-center">
              <Building2 className="mx-auto h-8 w-8 text-muted-foreground" />
              <p className="mt-3 text-sm text-muted-foreground">
                {clientes.length === 0
                  ? "Nenhum cliente cadastrado ainda."
                  : "Nenhum cliente encontrado para essa busca."}
              </p>
            </div>
          )}

          {filtrados.map((cliente) => (
            <button
              key={cliente.id}
              onClick={() => void entrar(cliente.id)}
              disabled={entrando !== null}
              className="flex w-full items-center justify-between rounded-xl border bg-card p-4 text-left transition-colors hover:border-primary hover:bg-accent disabled:opacity-60"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Building2 className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-medium">{cliente.name}</p>
                  {(cliente.city || cliente.state) && (
                    <p className="text-xs text-muted-foreground">
                      {[cliente.city, cliente.state].filter(Boolean).join(" - ")}
                    </p>
                  )}
                </div>
              </div>
              <span className="text-sm text-muted-foreground">
                {entrando === cliente.id ? "Entrando..." : "Entrar"}
              </span>
            </button>
          ))}
        </div>
      </div>

      <Dialog open={dialogAberto} onOpenChange={setDialogAberto}>
        <DialogContent>
          <form onSubmit={criarCliente}>
            <DialogHeader>
              <DialogTitle>Novo cliente</DialogTitle>
            </DialogHeader>
            <div className="py-4">
              <Label htmlFor="nome">Nome do cliente</Label>
              <Input
                id="nome"
                value={novoNome}
                onChange={(e) => setNovoNome(e.target.value)}
                placeholder="Ex.: Auto Center Silva"
                required
                className="mt-1.5"
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="ghost" onClick={() => setDialogAberto(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={salvando || !novoNome.trim()}>
                {salvando ? "Criando..." : "Criar cliente"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
