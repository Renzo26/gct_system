import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { clearAuth } from "@/lib/auth";
import {
  LayoutDashboard,
  MessagesSquare,
  CalendarDays,
  Users,
  BookOpen,
  Tag,
  UserCircle,
  LogOut,
  Bot,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

const main = [
  { title: "Dashboard", url: "/app", icon: LayoutDashboard, exact: true },
  { title: "Conversas", url: "/app/conversas", icon: MessagesSquare },
  { title: "Agenda", url: "/app/agenda", icon: CalendarDays },
  { title: "Meu Assistente", url: "/app/assistente", icon: Bot },
];

const config = [
  { title: "Usuários", url: "/app/configuracoes/usuarios", icon: Users },
  { title: "Minha oficina", url: "/app/configuracoes/conhecimento", icon: BookOpen },
  { title: "Clientes", url: "/app/configuracoes/clientes", icon: UserCircle },
  { title: "Etiquetas", url: "/app/configuracoes/etiquetas", icon: Tag },
];

export function AppSidebar() {
  const navigate = useNavigate();
  const handleLogout = () => {
    clearAuth();
    navigate({ to: "/login" });
  };
  const path = useRouterState({ select: (s) => s.location.pathname });
  const isActive = (url: string, exact?: boolean) =>
    exact ? path === url : path === url || path.startsWith(url + "/");

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="border-b border-sidebar-border">
        <div className="flex items-center gap-2 px-2 py-1.5">
          <div className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
            <img src="/logo.jfif" alt="GCT" className="h-full w-full object-cover" />
          </div>
          <div className="flex flex-col group-data-[collapsible=icon]:hidden">
            <span className="font-display text-base font-bold leading-tight">GCT</span>
            <span className="text-xs text-sidebar-foreground/60">Gestão de oficina</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Operação</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {main.map((it) => (
                <SidebarMenuItem key={it.url}>
                  <SidebarMenuButton asChild isActive={isActive(it.url, it.exact)} tooltip={it.title}>
                    <Link to={it.url}>
                      <it.icon />
                      <span>{it.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Configurações</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {config.map((it) => (
                <SidebarMenuItem key={it.url}>
                  <SidebarMenuButton asChild isActive={isActive(it.url)} tooltip={it.title}>
                    <Link to={it.url}>
                      <it.icon />
                      <span>{it.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton onClick={handleLogout} tooltip="Sair">
              <LogOut />
              <span>Sair</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
