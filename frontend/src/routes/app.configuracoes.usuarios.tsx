import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api } from "@/lib/api";

export const Route = createFileRoute("/app/configuracoes/usuarios")({
  head: () => ({ meta: [{ title: "Usuários — GCT" }] }),
  component: UsuariosPage,
});

type Usuario = { id: string; name: string; email: string; role: "ADMIN" | "AGENT" };
type RoleValue = "ADMIN" | "AGENT";

function roleLabel(role: RoleValue) {
  return role === "ADMIN" ? "Admin" : "Atendente";
}

function UsuariosPage() {
  const [users, setUsers] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [novoOpen, setNovoOpen] = useState(false);
  const [editUser, setEditUser] = useState<Usuario | null>(null);
  const [novoRole, setNovoRole] = useState<RoleValue>("AGENT");
  const [editRole, setEditRole] = useState<RoleValue>("AGENT");

  useEffect(() => {
    api.get<Usuario[]>("/users")
      .then(setUsers)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const criar = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setSaving(true);
    try {
      const created = await api.post<Usuario>("/users", {
        nome: String(f.get("nome")),
        email: String(f.get("email")),
        password: String(f.get("password")),
        role: novoRole,
      });
      setUsers((arr) => [...arr, created]);
      setNovoOpen(false);
      setNovoRole("AGENT");
    } catch { /* ignora */ } finally {
      setSaving(false);
    }
  };

  const salvarEdit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editUser) return;
    const f = new FormData(e.currentTarget);
    setSaving(true);
    try {
      const updated = await api.put<Usuario>(`/users/${editUser.id}`, {
        nome: String(f.get("nome")),
        role: editRole,
      });
      setUsers((arr) => arr.map((u) => (u.id === editUser.id ? updated : u)));
      setEditUser(null);
    } catch { /* ignora */ } finally {
      setSaving(false);
    }
  };

  const deletar = async (id: string) => {
    await api.delete(`/users/${id}`).catch(() => {});
    setUsers((arr) => arr.filter((u) => u.id !== id));
  };

  const abrirEdit = (u: Usuario) => {
    setEditUser(u);
    setEditRole(u.role);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold">Usuários</h1>
          <p className="text-sm text-muted-foreground">Gerencie a equipe.</p>
        </div>
        <Button onClick={() => { setNovoOpen(true); setNovoRole("AGENT"); }}>
          <Plus className="mr-1 h-4 w-4" /> Novo usuário
        </Button>
      </div>

      <div className="rounded-xl border bg-card">
        {loading ? (
          <div className="flex justify-center py-12"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead>E-mail</TableHead>
                <TableHead>Perfil</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="py-10 text-center text-sm text-muted-foreground">
                    Nenhum usuário cadastrado.
                  </TableCell>
                </TableRow>
              )}
              {users.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">{u.name}</TableCell>
                  <TableCell className="text-muted-foreground">{u.email}</TableCell>
                  <TableCell>
                    <Badge className={u.role === "ADMIN" ? "bg-primary/15 text-primary border-0" : "bg-muted text-muted-foreground border-0"}>
                      {roleLabel(u.role)}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" onClick={() => abrirEdit(u)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => deletar(u.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Dialog: Novo usuário */}
      <Dialog open={novoOpen} onOpenChange={setNovoOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Adicionar usuário</DialogTitle></DialogHeader>
          <form onSubmit={criar} className="space-y-3">
            <div className="space-y-2"><Label>Nome</Label><Input name="nome" required /></div>
            <div className="space-y-2"><Label>E-mail</Label><Input name="email" type="email" required /></div>
            <div className="space-y-2"><Label>Senha inicial</Label><Input name="password" type="password" required minLength={6} /></div>
            <div className="space-y-2">
              <Label>Perfil</Label>
              <Select value={novoRole} onValueChange={(v) => setNovoRole(v as RoleValue)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="ADMIN">Admin</SelectItem>
                  <SelectItem value="AGENT">Atendente</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button type="submit" disabled={saving}>
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Criar"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog: Editar usuário */}
      <Dialog open={!!editUser} onOpenChange={(v) => { if (!v) setEditUser(null); }}>
        <DialogContent>
          <DialogHeader><DialogTitle>Editar usuário</DialogTitle></DialogHeader>
          {editUser && (
            <form onSubmit={salvarEdit} className="space-y-3">
              <div className="space-y-2">
                <Label>Nome</Label>
                <Input name="nome" required defaultValue={editUser.name} />
              </div>
              <div className="space-y-2">
                <Label>E-mail</Label>
                <Input value={editUser.email} disabled className="opacity-60" />
              </div>
              <div className="space-y-2">
                <Label>Perfil</Label>
                <Select value={editRole} onValueChange={(v) => setEditRole(v as RoleValue)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ADMIN">Admin</SelectItem>
                    <SelectItem value="AGENT">Atendente</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setEditUser(null)}>Cancelar</Button>
                <Button type="submit" disabled={saving}>
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Salvar"}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
