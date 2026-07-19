import { useState } from "react";
import { useGetSystemStatus } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Activity, Cpu, Server, Clock, CheckCircle2, AlertTriangle, XCircle, Eye, EyeOff, ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/auth";
import { useToast } from "@/hooks/use-toast";

// ─── Admin gate para Status ───────────────────────────────────────────────────

function StatusAdminGate({ onLogin }: { onLogin: (key: string) => void }) {
  const [key, setKey] = useState("");
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!key.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/admin/verify", {
        method: "POST",
        headers: { "X-Admin-Key": key.trim() },
      });
      if (res.ok) {
        onLogin(key.trim());
        toast({ title: "Acceso concedido" });
      } else {
        setError("Clave incorrecta.");
      }
    } catch {
      setError("No se pudo conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
      <div className="w-full max-w-sm space-y-8 text-center">
        <div className="flex flex-col items-center gap-4">
          <ShieldCheck className="h-12 w-12 text-primary opacity-80" />
          <div>
            <h2 className="text-2xl font-bold">Estado del sistema</h2>
            <p className="text-muted-foreground text-sm mt-1">Solo visible para administradores.</p>
          </div>
        </div>
        <Card className="glass border-white/10 text-left">
          <CardContent className="pt-5">
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="relative">
                <Input
                  type={show ? "text" : "password"}
                  placeholder="Admin Key…"
                  value={key}
                  onChange={(e) => { setKey(e.target.value); setError(""); }}
                  className="bg-black/40 border-white/10 pr-10"
                  autoFocus
                />
                <button type="button" onClick={() => setShow(!show)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white transition-colors">
                  {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {error && <p className="text-xs text-destructive flex items-center gap-1"><AlertTriangle className="h-3 w-3" />{error}</p>}
              <Button type="submit" disabled={!key.trim() || loading} className="w-full">
                {loading ? "Verificando…" : "Ver estado"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function Status() {
  const { adminKey, setAdminKey } = useAuth();

  // Mostrar gate si no hay adminKey
  if (!adminKey) return <StatusAdminGate onLogin={setAdminKey} />;

  return <StatusContent />;
}

function StatusContent() {
  const { data: status, isLoading, isError } = useGetSystemStatus({ query: { refetchInterval: 10000 } });

  if (isLoading) {
    return (
      <div className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        <div className="h-8 w-48 bg-white/5 animate-pulse rounded" />
        <div className="grid md:grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <div key={i} className="h-32 bg-white/5 animate-pulse rounded-xl border border-white/5" />)}
        </div>
        <div className="h-[400px] bg-white/5 animate-pulse rounded-xl border border-white/5" />
      </div>
    );
  }

  if (isError || !status) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 text-center text-muted-foreground">
        <div>
          <AlertTriangle className="h-10 w-10 mx-auto mb-3 opacity-40" />
          <p>No se pudo cargar el estado del sistema.</p>
        </div>
      </div>
    );
  }

  const uptimeSecs = status.uptime ?? 0;
  const modelsDown = status.modelsDown ?? 0;
  const modelsActive = status.modelsActive ?? 0;
  const isHealthy = modelsDown === 0;
  const isDegraded = modelsDown > 0 && modelsActive > 0;

  function formatUptime(secs: number): string {
    if (secs < 60) return `${Math.floor(secs)}s`;
    if (secs < 3600) return `${Math.floor(secs / 60)}m ${Math.floor(secs % 60)}s`;
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    if (h < 24) return `${h}h ${m}m`;
    return `${Math.floor(h / 24)}d ${h % 24}h`;
  }
  
  return (
    <div className="flex-1 flex flex-col p-6 gap-8 max-w-7xl mx-auto w-full">
      <div>
        <h1 className="text-2xl font-bold tracking-tight mb-2">System Status</h1>
        <div className="flex items-center gap-3">
          <span className="relative flex h-3 w-3">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
              isHealthy ? "bg-green-400" : isDegraded ? "bg-yellow-400" : "bg-red-400"
            }`}></span>
            <span className={`relative inline-flex rounded-full h-3 w-3 ${
              isHealthy ? "bg-green-500" : isDegraded ? "bg-yellow-500" : "bg-red-500"
            }`}></span>
          </span>
          <span className="text-sm font-medium">
            {isHealthy ? "All systems operational" : isDegraded ? "Degraded performance" : "System outage"}
          </span>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatusCard
          title="Uptime"
          value={formatUptime(uptimeSecs)}
          icon={Activity}
          status="ok"
        />
        <StatusCard
          title="Avg Latency"
          value={`${Math.round(status.avgLatencyMs || 0)}ms`}
          icon={Clock}
          status={(status.avgLatencyMs || 0) < 500 ? "ok" : "warn"}
        />
        <StatusCard
          title="RAM Usage"
          value={`${Math.round(status.ramUsageMb || 0)} MB`}
          icon={Server}
          status="neutral"
        />
        <StatusCard
          title="CPU Load"
          value={`${(status.cpuPercent || 0).toFixed(1)}%`}
          icon={Cpu}
          status={(status.cpuPercent || 0) < 80 ? "ok" : "warn"}
        />
      </div>

      <div className="grid md:grid-cols-2 gap-8 mt-4">
        <Card className="glass shadow-none bg-black/20">
          <CardHeader>
            <CardTitle>Model Availability</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {status.models?.map((model, i) => (
              <motion.div 
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                key={model.id} 
                className="flex items-center justify-between p-3 rounded-lg border border-white/5 bg-white/[0.02]"
              >
                <div className="flex items-center gap-3">
                  {model.status === 'active' ? (
                    <CheckCircle2 className="w-5 h-5 text-green-500" />
                  ) : model.status === 'degraded' ? (
                    <AlertTriangle className="w-5 h-5 text-yellow-500" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-500" />
                  )}
                  <div>
                    <div className="font-medium">{model.name}</div>
                    <div className="text-xs text-muted-foreground uppercase tracking-wider font-mono mt-0.5">
                      {model.provider}
                    </div>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <Badge variant="outline" className={
                    model.status === 'active' ? "border-green-500/20 text-green-400 bg-green-500/10" : 
                    model.status === 'degraded' ? "border-yellow-500/20 text-yellow-400 bg-yellow-500/10" : 
                    "border-red-500/20 text-red-400 bg-red-500/10"
                  }>
                    {model.status}
                  </Badge>
                  {model.latencyMs && (
                    <span className="text-xs font-mono text-muted-foreground">{model.latencyMs}ms p95</span>
                  )}
                </div>
              </motion.div>
            ))}
          </CardContent>
        </Card>

        <Card className="glass shadow-none bg-black/20 h-fit">
          <CardHeader>
            <CardTitle>Routing Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-muted-foreground">Cache Hit Rate</span>
                  <span className="font-mono">{((status.cacheHitRate || 0) * 100).toFixed(1)}%</span>
                </div>
                <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-primary" style={{ width: `${(status.cacheHitRate || 0) * 100}%` }} />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5">
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Active Models</div>
                  <div className="text-2xl font-mono text-green-400">{status.modelsActive}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Offline Models</div>
                  <div className="text-2xl font-mono text-destructive">{status.modelsDown}</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatusCard({ title, value, icon: Icon, status }: { title: string, value: string, icon: any, status: "ok" | "warn" | "error" | "neutral" }) {
  const colorClass = 
    status === "ok" ? "text-green-500" : 
    status === "warn" ? "text-yellow-500" : 
    status === "error" ? "text-red-500" : "text-primary";

  return (
    <Card className="glass shadow-none bg-black/20">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className={`h-4 w-4 ${colorClass}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold font-mono tracking-tight">{value}</div>
      </CardContent>
    </Card>
  );
}
