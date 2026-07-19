import { ReactNode } from "react";
import { Link, useLocation } from "wouter";
import { Terminal, LayoutDashboard, FileText, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { ErrorBoundary } from "@/components/error-boundary";
import autopyLogo from "@/assets/autopy-logo.png";

export function Layout({ children }: { children: ReactNode }) {
  const [location] = useLocation();

  const links = [
    { href: "/playground", label: "Playground", icon: Terminal },
    { href: "/docs", label: "Docs", icon: FileText },
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/status", label: "Status", icon: Activity },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-50 w-full border-b border-white/5 bg-background/80 backdrop-blur-xl">
        <div className="container mx-auto flex h-14 items-center px-4 md:px-8">
          <Link href="/" className="flex items-center gap-2 mr-8">
            <img src={autopyLogo} alt="Autopy AI" className="h-7 w-7 object-contain" />
            <span className="font-bold tracking-tight text-lg">Autopy AI</span>
          </Link>
          <nav className="flex items-center space-x-1 flex-1">
            {links.map((link) => {
              const active = location === link.href;
              const Icon = link.icon;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                    active
                      ? "bg-white/10 text-white"
                      : "text-muted-foreground hover:bg-white/5 hover:text-white"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {link.label}
                </Link>
              );
            })}
          </nav>
          <div className="flex items-center space-x-4">
             {/* Future: auth user dropdown etc */}
          </div>
        </div>
      </header>
      <main className="flex-1 flex flex-col">
        <ErrorBoundary>{children}</ErrorBoundary>
      </main>
    </div>
  );
}
