import { useState } from "react";
import { 
  useGetDashboardStats, 
  useListApiKeys, 
  useCreateApiKey, 
  useDeleteApiKey,
  useGetRequestLogs,
  useAdminListModels,
  useUpdateModelStatus
} from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar } from "recharts";
import { format } from "date-fns";
import { Copy, Plus, Trash2, ArrowRightLeft, AlertTriangle, CheckCircle2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog";

export default function Dashboard() {
  return (
    <div className="flex-1 flex flex-col p-6 gap-8 max-w-7xl mx-auto w-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Platform Dashboard</h1>
          <p className="text-muted-foreground text-sm">Manage keys, monitor usage, and configure routing.</p>
        </div>
      </div>

      <StatsOverview />
      
      <Tabs defaultValue="keys" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-3 glass bg-black/40">
          <TabsTrigger value="keys" className="data-[state=active]:bg-primary/20">API Keys</TabsTrigger>
          <TabsTrigger value="logs" className="data-[state=active]:bg-primary/20">Request Logs</TabsTrigger>
          <TabsTrigger value="models" className="data-[state=active]:bg-primary/20">Model Routing</TabsTrigger>
        </TabsList>
        <div className="mt-6">
          <TabsContent value="keys" className="m-0 border-none p-0 outline-none">
            <ApiKeysPanel />
          </TabsContent>
          <TabsContent value="logs" className="m-0 border-none p-0 outline-none">
            <LogsPanel />
          </TabsContent>
          <TabsContent value="models" className="m-0 border-none p-0 outline-none">
            <ModelsPanel />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}

function StatsOverview() {
  const { data: stats, isLoading } = useGetDashboardStats({});

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
          <p className="text-xs text-muted-foreground mt-1">
            +{stats.requestsToday?.toLocaleString()} today
          </p>
        </CardContent>
      </Card>
      <Card className="glass shadow-none bg-black/20">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Tokens Used</CardTitle>
          <span className="font-mono font-bold text-accent text-sm">TOK</span>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{(stats.totalTokens || 0).toLocaleString()}</div>
          <p className="text-xs text-muted-foreground mt-1">
            +{(stats.tokensToday || 0).toLocaleString()} today
          </p>
        </CardContent>
      </Card>
      <Card className="glass shadow-none bg-black/20">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Cache Hit Rate</CardTitle>
          <CheckCircle2 className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{((stats.cacheHitRate || 0) * 100).toFixed(1)}%</div>
          <p className="text-xs text-muted-foreground mt-1">
            Avg {Math.round(stats.avgLatencyMs || 0)}ms latency
          </p>
        </CardContent>
      </Card>
      <Card className="glass shadow-none bg-black/20">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Error Rate</CardTitle>
          <AlertTriangle className="h-4 w-4 text-destructive" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{((stats.errorRate || 0) * 100).toFixed(2)}%</div>
          <p className="text-xs text-muted-foreground mt-1">
            {stats.activeApiKeys} active API keys
          </p>
        </CardContent>
      </Card>

      {/* Chart */}
      {stats.requestsOverTime && stats.requestsOverTime.length > 0 && (
        <Card className="col-span-full glass shadow-none bg-black/20">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Traffic Volume</CardTitle>
          </CardHeader>
          <CardContent className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stats.requestsOverTime}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="date" stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v) => format(new Date(v), "MMM d")} />
                <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ color: 'hsl(var(--foreground))' }}
                />
                <Line type="monotone" dataKey="requests" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} activeDot={{ r: 6, fill: "hsl(var(--primary))" }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function ApiKeysPanel() {
  const { data, refetch } = useListApiKeys({});
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const createKey = useCreateApiKey({});
  const deleteKey = useDeleteApiKey({});
  const { toast } = useToast();

  const handleCreate = () => {
    if (!newKeyName.trim()) return;
    createKey.mutate({ data: { name: newKeyName } }, {
      onSuccess: (key) => {
        toast({ title: "API Key Created", description: "Make sure to copy the key now, it won't be shown again." });
        refetch();
        setIsCreateOpen(false);
        setNewKeyName("");
      }
    });
  };

  const copyKey = (key: string) => {
    navigator.clipboard.writeText(key);
    toast({ title: "Copied to clipboard" });
  };

  return (
    <Card className="glass shadow-none bg-black/20">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>API Keys</CardTitle>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button size="sm" className="gap-2"><Plus className="w-4 h-4" /> Create Key</Button>
          </DialogTrigger>
          <DialogContent className="glass">
            <DialogHeader>
              <DialogTitle>Create New API Key</DialogTitle>
            </DialogHeader>
            <div className="py-4">
              <Input 
                placeholder="Key Name (e.g. Production App)" 
                value={newKeyName} 
                onChange={(e) => setNewKeyName(e.target.value)} 
                className="bg-black/40"
              />
            </div>
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline">Cancel</Button>
              </DialogClose>
              <Button onClick={handleCreate} disabled={!newKeyName.trim() || createKey.isPending}>
                Create Key
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-white/5 hover:bg-transparent">
              <TableHead>Name</TableHead>
              <TableHead>Key</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Requests</TableHead>
              <TableHead className="text-right">Created</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.keys?.map((key) => (
              <TableRow key={key.id} className="border-white/5 border-b hover:bg-white/[0.02]">
                <TableCell className="font-medium">{key.name}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2 font-mono text-sm">
                    {key.key.substring(0, 8)}...{key.key.substring(key.key.length - 4)}
                    <Button variant="ghost" size="icon" className="h-6 w-6 rounded hover:bg-white/10" onClick={() => copyKey(key.key)}>
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={key.status === "active" ? "text-green-400 border-green-500/20 bg-green-500/10" : "text-muted-foreground"}>
                    {key.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-right font-mono text-sm text-muted-foreground">
                  {key.totalRequests?.toLocaleString()}
                </TableCell>
                <TableCell className="text-right text-muted-foreground">
                  {format(new Date(key.createdAt), "MMM d, yyyy")}
                </TableCell>
                <TableCell>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-8 w-8 text-destructive hover:bg-destructive/10 hover:text-destructive"
                    onClick={() => {
                      if (confirm("Revoke and delete this key?")) {
                        deleteKey.mutate({ keyId: key.id }, { onSuccess: () => refetch() });
                      }
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {!data?.keys?.length && (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                  No API keys found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function LogsPanel() {
  const [status, setStatus] = useState<string>("all");
  const { data } = useGetRequestLogs({ limit: 50, status: status === "all" ? undefined : status as any });

  return (
    <Card className="glass shadow-none bg-black/20">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Requests</CardTitle>
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="w-[150px] h-8 bg-black/40 border-white/10">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Requests</SelectItem>
            <SelectItem value="success">Success</SelectItem>
            <SelectItem value="error">Errors</SelectItem>
            <SelectItem value="blocked">Blocked / Rate Limited</SelectItem>
          </SelectContent>
        </Select>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-white/5 hover:bg-transparent">
              <TableHead>Timestamp</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Endpoint</TableHead>
              <TableHead>Provider/Model</TableHead>
              <TableHead className="text-right">Latency</TableHead>
              <TableHead className="text-right">Tokens</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.logs?.map((log) => (
              <TableRow key={log.id} className="border-white/5 border-b hover:bg-white/[0.02]">
                <TableCell className="text-muted-foreground whitespace-nowrap">
                  {format(new Date(log.createdAt), "MMM d HH:mm:ss")}
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={
                    log.status === "success" ? "text-green-400 border-green-500/20 bg-green-500/10" : 
                    log.status === "error" ? "text-destructive border-destructive/20 bg-destructive/10" : 
                    "text-yellow-400 border-yellow-500/20 bg-yellow-500/10"
                  }>
                    {log.status}
                  </Badge>
                </TableCell>
                <TableCell className="font-mono text-xs">{log.endpoint}</TableCell>
                <TableCell>
                  {log.provider ? (
                    <div className="flex items-center gap-1.5 text-sm">
                      <span className="text-muted-foreground">{log.provider}</span>
                      <span className="text-white/20">/</span>
                      <span className="font-mono">{log.model}</span>
                    </div>
                  ) : <span className="text-muted-foreground">-</span>}
                </TableCell>
                <TableCell className="text-right font-mono text-sm text-muted-foreground">
                  {log.latencyMs ? `${log.latencyMs}ms` : '-'}
                </TableCell>
                <TableCell className="text-right font-mono text-sm text-muted-foreground">
                  {log.tokensUsed || '-'}
                </TableCell>
              </TableRow>
            ))}
            {!data?.logs?.length && (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                  No request logs found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function ModelsPanel() {
  const { data, refetch } = useAdminListModels({});
  const updateModel = useUpdateModelStatus({});
  const { toast } = useToast();

  const handleStatusChange = (id: string, status: any) => {
    updateModel.mutate({ data: { id, status } }, {
      onSuccess: () => {
        toast({ title: "Model updated" });
        refetch();
      }
    });
  };

  return (
    <Card className="glass shadow-none bg-black/20">
      <CardHeader>
        <CardTitle>Model Routing & Status</CardTitle>
        <p className="text-sm text-muted-foreground">Configure which models are available and their failover priority.</p>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-white/5 hover:bg-transparent">
              <TableHead>Provider</TableHead>
              <TableHead>Model ID</TableHead>
              <TableHead>Capabilities</TableHead>
              <TableHead>Admin Override Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.models?.map((m) => (
              <TableRow key={m.id} className="border-white/5 border-b hover:bg-white/[0.02]">
                <TableCell className="font-medium capitalize">{m.provider}</TableCell>
                <TableCell className="font-mono text-sm">{m.id}</TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Badge variant="outline" className="bg-white/5 border-white/10">Text</Badge>
                    {m.supportsImages && <Badge variant="outline" className="bg-white/5 border-white/10">Image</Badge>}
                  </div>
                </TableCell>
                <TableCell>
                  <Select value={m.status} onValueChange={(val) => handleStatusChange(m.id, val)}>
                    <SelectTrigger className="w-[130px] h-8 bg-black/40 border-white/10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="degraded">Degraded</SelectItem>
                      <SelectItem value="down">Forced Down</SelectItem>
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
