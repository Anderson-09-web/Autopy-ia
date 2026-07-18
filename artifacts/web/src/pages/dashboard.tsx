import { useState, startTransition } from "react";
import { useAuth, getCustomFetchOptions } from "@/lib/auth";
import {
  useGetDashboardStats,
  useListApiKeys,
  useCreateApiKey,
  useDeleteApiKey,
  useGetRequestLogs,
  useAdminListModels,
  useUpdateModelStatus,
} from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from "recharts";
import { format } from "date-fns";
import { Copy, Plus, Trash2, ArrowRightLeft, AlertTriangle, CheckCircle2, ShieldCheck, LogOut, Eye, EyeOff } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog";
import autopyLogo from "@/assets/autopy-logo.png";

// ─── Admin Login ─────────────────────────────────────────────────────────────

function AdminLogin({ onLogin }: { onLogin: (key: string) => void }) {
  const [key, setKey] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
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
        toast({ title: "Acceso concedido", description: "Bienvenido al panel de administración." });
      } else {
        setError("Clave incorrecta. Verifica tu ADMIN_KEY en los secrets del proyecto.");
      }
    } catch {
      setError("No se pudo conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
      <div className="w-full max-w-sm space-y-8">
        {/* Logo + heading */}
        <div className="flex flex-col items-center gap-4 text-center">
          <img src={autopyLogo} alt="Autopy AI" className="h-14 w-14 object-contain drop-shadow-[0_0_16px_rgba(124,58,237,0.5)]" />
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Panel de administración</h1>
            <p className="text-muted-foreground text-sm mt-1">Solo para administradores de Autopy AI</p>
          </div>
        </div>

        {/* Login card */}
        <Card className="glass border-white/10">
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Admin Key</label>
                <div className="relative">
                  <Input
                    type={show ? "text" : "password"}
                    placeholder="Ingresa tu ADMIN_KEY…"
                    value={key}
                    onChange={(e) => { setKey(e.target.value); setError(""); }}
                    className="bg-black/40 border-white/10 pr-10"
                    autoFocus
                  />
                  <button
                    type="button"
                    onClick={() => setShow(!show)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white transition-colors"
                  >
                    {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {error && (
                  <p className="text-xs text-destructive flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" /> {error}
                  </p>
                )}
              </div>
              <Button type="submit" disabled={!key.trim() || loading} className="w-full">
                {loading ? "Verificando…" : "Entrar al Dashboard"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground">
          La ADMIN_KEY está configurada en los Secrets del proyecto.
        </p>
      </div>
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────

export default function Dashboard() {
  const { adminKey, setAdminKey } = useAuth();

  if (!adminKey) {
    return <AdminLogin onLogin={setAdminKey} />;
  }

  return (
    <div className="flex-1 flex flex-col p-6 gap-8 max-w-7xl mx-auto w-full">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ShieldCheck className="h-5 w-5 text-primary" />
            <h1 className="text-2xl font-bold tracking-tight">Platform Dashboard</h1>
          </div>
          <p className="text-muted-foreground text-sm">Gestiona claves, supervisa el uso y configura el enrutamiento.</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="gap-2 border-white/10 hover:border-destructive/50 hover:text-destructive"
          onClick={() => startTransition(() => setAdminKey(""))}
        >
          <LogOut className="h-4 w-4" />
          Cerrar sesión
        </Button>
      </div>

      <StatsOverview adminKey={adminKey} />

      <Tabs defaultValue="keys" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-3 glass bg-black/40">
          <TabsTrigger value="keys" className="data-[state=active]:bg-primary/20">API Keys</TabsTrigger>
          <TabsTrigger value="logs" className="data-[state=active]:bg-primary/20">Registros</TabsTrigger>
          <TabsTrigger value="models" className="data-[state=active]:bg-primary/20">Modelos</TabsTrigger>
        </TabsList>
        <div className="mt-6">
          <TabsContent value="keys" className="m-0 border-none p-0 outline-none">
            <ApiKeysPanel adminKey={adminKey} />
          </TabsContent>
          <TabsContent value="logs" className="m-0 border-none p-0 outline-none">
            <LogsPanel adminKey={adminKey} />
          </TabsContent>
          <TabsContent value="models" className="m-0 border-none p-0 outline-none">
            <ModelsPanel adminKey={adminKey} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}

// ─── Stats ────────────────────────────────────────────────────────────────────

function StatsOverview({ adminKey }: { adminKey: string }) {
  const { data: stats, isLoading } = useGetDashboardStats({ request: getCustomFetchOptions({ adminKey }) });

  if (isLoading || !stats) {
    return <div className="h-32 rounded-xl bg-card animate-pulse border border-white/5" />;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card className="glass shadow-none bg-black/20">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Total Requests</CardTitle>
          <ArrowRightLeft className="h-4 w-4 text-primary" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalRequests?.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground mt-1">+{stats.requestsToday?.toLocaleString()} today</p>
        </CardContent>
      </Card>
      <Card className="glass shadow-none bg-black/20">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Tokens Used</CardTitle>
          <span className="font-mono font-bold text-accent text-sm">TOK</span>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{(stats.totalTokens || 0).toLocaleString()}</div>
          <p className="text-xs text-muted-foreground mt-1">+{(stats.tokensToday || 0).toLocaleString()} today</p>
        </CardContent>
      </Card>
      <Card className="glass shadow-none bg-black/20">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Cache Hit Rate</CardTitle>
          <CheckCircle2 className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{((stats.cacheHitRate || 0) * 100).toFixed(1)}%</div>
          <p className="text-xs text-muted-foreground mt-1">Avg {Math.round(stats.avgLatencyMs || 0)}ms latency</p>
        </CardContent>
      </Card>
      <Card className="glass shadow-none bg-black/20">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Error Rate</CardTitle>
          <AlertTriangle className="h-4 w-4 text-destructive" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{((stats.errorRate || 0) * 100).toFixed(2)}%</div>
          <p className="text-xs text-muted-foreground mt-1">{stats.activeApiKeys} active API keys</p>
        </CardContent>
      </Card>

      {stats.requestsOverTime && stats.requestsOverTime.length > 0 && (
        <Card className="col-span-full glass shadow-none bg-black/20">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Tráfico (últimos 7 días)</CardTitle>
          </CardHeader>
          <CardContent className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stats.requestsOverTime}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="date" stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false}
                  tickFormatter={(v) => format(new Date(v), "MMM d")} />
                <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} />
                <RechartsTooltip
                  contentStyle={{ backgroundColor: "hsl(var(--card))", borderColor: "rgba(255,255,255,0.1)", borderRadius: "8px" }}
                  itemStyle={{ color: "hsl(var(--foreground))" }}
                />
                <Line type="monotone" dataKey="requests" stroke="hsl(var(--primary))" strokeWidth={2} dot={false}
                  activeDot={{ r: 6, fill: "hsl(var(--primary))" }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ─── API Keys ─────────────────────────────────────────────────────────────────

function ApiKeysPanel({ adminKey }: { adminKey: string }) {
  const opts = { request: getCustomFetchOptions({ adminKey }) };
  const { data, refetch } = useListApiKeys({}, opts);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const createKey = useCreateApiKey(opts);
  const deleteKey = useDeleteApiKey(opts);
  const { toast } = useToast();

  const handleCreate = () => {
    if (!newKeyName.trim()) return;
    createKey.mutate(
      { data: { name: newKeyName } },
      {
        onSuccess: () => {
          toast({ title: "API Key creada", description: "Cópiala ahora, no se mostrará de nuevo." });
          refetch();
          setIsCreateOpen(false);
          setNewKeyName("");
        },
        onError: () => toast({ title: "Error al crear key", variant: "destructive" }),
      }
    );
  };

  const copyKey = (key: string) => {
    navigator.clipboard.writeText(key);
    toast({ title: "Copiada al portapapeles" });
  };

  return (
    <Card className="glass shadow-none bg-black/20">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>API Keys</CardTitle>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button size="sm" className="gap-2"><Plus className="w-4 h-4" /> Crear Key</Button>
          </DialogTrigger>
          <DialogContent className="glass">
            <DialogHeader><DialogTitle>Nueva API Key</DialogTitle></DialogHeader>
            <div className="py-4">
              <Input
                placeholder="Nombre (ej. Producción, App móvil…)"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                className="bg-black/40"
                autoFocus
              />
            </div>
            <DialogFooter>
              <DialogClose asChild><Button variant="outline">Cancelar</Button></DialogClose>
              <Button onClick={handleCreate} disabled={!newKeyName.trim() || createKey.isPending}>
                {createKey.isPending ? "Creando…" : "Crear Key"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-white/5 hover:bg-transparent">
              <TableHead>Nombre</TableHead>
              <TableHead>Key</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="text-right">Requests</TableHead>
              <TableHead className="text-right">Creada</TableHead>
              <TableHead className="w-[50px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.keys?.map((key) => (
              <TableRow key={key.id} className="border-white/5 border-b hover:bg-white/[0.02]">
                <TableCell className="font-medium">{key.name}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2 font-mono text-sm">
                    {key.key.substring(0, 8)}…{key.key.substring(key.key.length - 4)}
                    <Button variant="ghost" size="icon" className="h-6 w-6 rounded hover:bg-white/10" onClick={() => copyKey(key.key)}>
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={key.status === "active"
                    ? "text-green-400 border-green-500/20 bg-green-500/10"
                    : "text-muted-foreground"}>
                    {key.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-right font-mono text-sm text-muted-foreground">
                  {key.totalRequests?.toLocaleString()}
                </TableCell>
                <TableCell className="text-right text-muted-foreground">
                  {format(new Date(key.createdAt), "dd MMM yyyy")}
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost" size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                    onClick={() => { if (confirm("¿Revocar y eliminar esta key?")) deleteKey.mutate({ keyId: key.id }, { onSuccess: () => refetch() }); }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {!data?.keys?.length && (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                  No hay API keys. Crea una con el botón de arriba.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

// ─── Logs ─────────────────────────────────────────────────────────────────────

function LogsPanel({ adminKey }: { adminKey: string }) {
  const [status, setStatus] = useState<string>("all");
  const { data } = useGetRequestLogs(
    { limit: 50, status: status === "all" ? undefined : (status as any) },
    { request: getCustomFetchOptions({ adminKey }) }
  );

  return (
    <Card className="glass shadow-none bg-black/20">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Registros de solicitudes</CardTitle>
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="w-[160px] h-8 bg-black/40 border-white/10">
            <SelectValue placeholder="Filtrar estado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="success">Exitosos</SelectItem>
            <SelectItem value="error">Errores</SelectItem>
            <SelectItem value="blocked">Bloqueados</SelectItem>
          </SelectContent>
        </Select>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-white/5 hover:bg-transparent">
              <TableHead>Timestamp</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Endpoint</TableHead>
              <TableHead>Proveedor / Modelo</TableHead>
              <TableHead className="text-right">Latencia</TableHead>
              <TableHead className="text-right">Tokens</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.logs?.map((log) => (
              <TableRow key={log.id} className="border-white/5 border-b hover:bg-white/[0.02]">
                <TableCell className="text-muted-foreground whitespace-nowrap">
                  {format(new Date(log.createdAt), "dd MMM HH:mm:ss")}
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={
                    log.status === "success" ? "text-green-400 border-green-500/20 bg-green-500/10" :
                    log.status === "error" ? "text-destructive border-destructive/20 bg-destructive/10" :
                    "text-yellow-400 border-yellow-500/20 bg-yellow-500/10"
                  }>{log.status}</Badge>
                </TableCell>
                <TableCell className="font-mono text-xs">{log.endpoint}</TableCell>
                <TableCell>
                  {log.provider
                    ? <div className="flex items-center gap-1.5 text-sm">
                        <span className="text-muted-foreground">{log.provider}</span>
                        <span className="text-white/20">/</span>
                        <span className="font-mono">{log.model}</span>
                      </div>
                    : <span className="text-muted-foreground">—</span>}
                </TableCell>
                <TableCell className="text-right font-mono text-sm text-muted-foreground">
                  {log.latencyMs ? `${log.latencyMs}ms` : "—"}
                </TableCell>
                <TableCell className="text-right font-mono text-sm text-muted-foreground">
                  {log.tokensUsed || "—"}
                </TableCell>
              </TableRow>
            ))}
            {!data?.logs?.length && (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                  No hay registros todavía.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

// ─── Models ───────────────────────────────────────────────────────────────────

function ModelsPanel({ adminKey }: { adminKey: string }) {
  const opts = { request: getCustomFetchOptions({ adminKey }) };
  const { data, refetch } = useAdminListModels(opts);
  const updateModel = useUpdateModelStatus(opts);
  const { toast } = useToast();

  const handleStatusChange = (id: string, status: any) => {
    updateModel.mutate({ data: { id, status } }, {
      onSuccess: () => { toast({ title: "Modelo actualizado" }); refetch(); },
    });
  };

  return (
    <Card className="glass shadow-none bg-black/20">
      <CardHeader>
        <CardTitle>Enrutamiento de modelos</CardTitle>
        <p className="text-sm text-muted-foreground">Activa, degrada o fuerza la caída de cada modelo.</p>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-white/5 hover:bg-transparent">
              <TableHead>Proveedor</TableHead>
              <TableHead>Model ID</TableHead>
              <TableHead>Capacidades</TableHead>
              <TableHead>Estado</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.models?.map((m) => (
              <TableRow key={m.id} className="border-white/5 border-b hover:bg-white/[0.02]">
                <TableCell className="font-medium capitalize">{m.provider}</TableCell>
                <TableCell className="font-mono text-sm">{m.id}</TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Badge variant="outline" className="bg-white/5 border-white/10">Texto</Badge>
                    {m.supportsImages && <Badge variant="outline" className="bg-white/5 border-white/10">Imagen</Badge>}
                  </div>
                </TableCell>
                <TableCell>
                  <Select value={m.status} onValueChange={(val) => handleStatusChange(m.id, val)}>
                    <SelectTrigger className="w-[140px] h-8 bg-black/40 border-white/10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Activo</SelectItem>
                      <SelectItem value="degraded">Degradado</SelectItem>
                      <SelectItem value="down">Forzar caída</SelectItem>
                    </SelectContent>
                  </Select>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
