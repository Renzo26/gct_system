import { createFileRoute, Outlet, redirect, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { ThemeToggle } from "@/components/theme-toggle";
import { clearAuth, clearWorkshop, getSession, hasWorkshop } from "@/lib/auth";
import { LogOut, Repeat } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Toaster } from "sonner";

export const Route = createFileRoute("/app")({
  beforeLoad: () => {
    if (typeof window === "undefined") return;
    if (!localStorage.getItem("access_token")) throw redirect({ to: "/login" });
    if (!hasWorkshop()) throw redirect({ to: "/selecionar-cliente" });
  },
  component: AppLayout,
});

function AppLayout() {
  const navigate = useNavigate();
  const session = getSession();
  const [workshopName, setWorkshopName] = useState(session?.workshop?.name ?? "GCT");

  useEffect(() => {
    const handler = () => {
      const s = getSession();
      if (s?.workshop) setWorkshopName(s.workshop.name);
    };
    window.addEventListener("workshop-name-updated", handler);
    return () => window.removeEventListener("workshop-name-updated", handler);
  }, []);

  const handleLogout = () => {
    clearAuth();
    navigate({ to: "/login" });
  };

  const handleTrocarCliente = () => {
    clearWorkshop();
    navigate({ to: "/selecionar-cliente" });
  };

  return (
    <SidebarProvider>
      <Toaster richColors position="top-right" />
      <div className="flex min-h-screen w-full bg-background">
        <AppSidebar />
        <div className="flex flex-1 flex-col">
          <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b bg-background/80 px-4 backdrop-blur">
            <div className="flex items-center gap-2">
              <SidebarTrigger />
              <span className="text-sm text-muted-foreground">
                {workshopName}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleTrocarCliente}
                title="Trocar de cliente"
              >
                <Repeat className="h-4 w-4" />
              </Button>
              <ThemeToggle />
              <Button variant="ghost" size="icon" onClick={handleLogout} title="Sair">
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </header>
          <main className="flex-1 p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
