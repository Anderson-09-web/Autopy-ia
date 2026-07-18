import { useGetSystemStatus } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, Cpu, Server, Clock, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { motion } from "framer-motion";

export default function Status() {
  const { data: status, isLoading } = useGetSystemStatus({ query: { refetchInterval: 10000 } });

  if (isLoading || !status) {
    return (
      <div className="flex-1 p-6 max-w-7xl mx-auto w-full">
        <div className="h-8 w-48 bg-card animate-pulse rounded mb-8" />
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          {[1,2,3,4].map(i => <div key={i} className="h-32 bg-card animate-pulse rounded-xl" />)}
        </div>
        <div className="h-[400px] bg-card animate-pulse rounded-xl" />
      </div>
    );
  }

  const isHealthy = status.modelsDown === 0 && status.uptime > 0.99;
  const isDegraded = status.modelsDown > 0 && status.modelsActive > 0;
  
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
          title="Global Uptime"
          value={`${(status.uptime * 100).toFixed(2)}%`}
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
