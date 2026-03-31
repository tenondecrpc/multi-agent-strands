import type { ReactNode } from "react";
import { Button } from "@/atoms/Button";
import { Icon } from "@/atoms/Icon";
import { Separator } from "@/components/ui/separator";
import { useUIStore } from "@/lib/stores/uiStore";
import { cn } from "@/lib/utils";

interface DashboardLayoutProps {
  children: ReactNode;
  className?: string;
}

export const DashboardLayout = ({ children, className }: DashboardLayoutProps) => {
  const { theme, toggleTheme, sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <div className={cn("min-h-screen bg-background", className)}>
      <header className="sticky top-0 z-50 flex h-14 items-center gap-4 border-b bg-background px-4">
        <Button variant="ghost" size="icon" onClick={toggleSidebar}>
          <Icon name="menu" />
        </Button>
        <h1 className="text-lg font-semibold">Multi-Agent System</h1>
        <div className="ml-auto flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={toggleTheme} className="rounded-full">
            <Icon name={theme === "dark" ? "sun" : "moon"} />
          </Button>
        </div>
      </header>
      <div className="flex">
        {sidebarOpen && (
          <aside className="w-64 border-r bg-background p-4">
            <nav className="space-y-2">
              <Button variant="ghost" className="w-full justify-start">
                Dashboard
              </Button>
              <Button variant="ghost" className="w-full justify-start">
                Sessions
              </Button>
              <Button variant="ghost" className="w-full justify-start">
                Settings
              </Button>
            </nav>
            <Separator className="my-4" />
            <div className="text-sm text-muted-foreground">
              <p className="font-medium">Sessions</p>
              <p className="mt-1">No active sessions</p>
            </div>
          </aside>
        )}
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
};
