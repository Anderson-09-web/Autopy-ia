import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Copy, Check, ChevronRight, Download, Bot } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

// ─── Types ────────────────────────────────────────────────────────────────────

type Method = "GET" | "POST" | "PATCH" | "DELETE" | "PUT";

// ─── Copy helper (iframe-safe) ────────────────────────────────────────────────

async function safeCopy(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    try {
      const el = document.createElement("textarea");
      el.value = text;
      el.style.cssText = "position:fixed;opacity:0";
      document.body.appendChild(el);
      el.focus();
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
      return true;
    } catch { return false; }
  }
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function MethodBadge({ method }: { method: Method }) {
  const colors: Record<Method, string> = {
    GET:    "bg-blue-500/10 text-blue-400 border-blue-500/20",
    POST:   "bg-green-500/10 text-green-400 border-green-500/20",
    PATCH:  "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    DELETE: "bg-red-500/10 text-red-400 border-red-500/20",
    PUT:    "bg-purple-500/10 text-purple-400 border-purple-500/20",
  };
  return (
    <span className={`px-2 py-0.5 rounded border text-xs font-mono font-bold shrink-0 ${colors[method]}`}>
      {method}
    </span>
  );
}

function CodeBlock({ code, language = "bash" }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await safeCopy(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-lg overflow-hidden my-4 border border-white/10 bg-[#0a0a0a]">
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/10 bg-black/40">
        <span className="text-xs text-muted-foreground font-mono">{language}</span>
        <button onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-white transition-colors">
          {copied ? <Check className="h-3 w-3 text-green-400" /> : <Copy className="h-3 w-3" />}
          {copied ? "Copiado" : "Copiar"}
        </button>
      </div>
      <pre className="p-4 overflow-x-auto text-sm font-mono text-gray-300 leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function EndpointHeader({ method, path, description }: { method: Method; path: string; description: string }) {
  return (
    <div className="mt-10 mb-4 p-4 rounded-xl bg-white/[0.02] border border-white/5">
      <div className="flex items-center gap-3 mb-2">
        <MethodBadge method={method} />
        <code className="text-sm font-mono text-white">{path}</code>
      </div>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}

function ParamTable({ params }: {
  params: { name: string; type: string; required?: boolean; description: string }[]
}) {
  return (
    <div className="rounded-lg border border-white/5 overflow-hidden my-4 text-sm">
      <div className="grid grid-cols-[140px_80px_60px_1fr] bg-black/40 px-4 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
        <span>Parámetro</span><span>Tipo</span><span>Req.</span><span>Descripción</span>
      </div>
      {params.map((p) => (
        <div key={p.name} className="grid grid-cols-[140px_80px_60px_1fr] px-4 py-3 border-t border-white/5 hover:bg-white/[0.02] transition-colors">
          <code className="text-primary font-mono">{p.name}</code>
          <span className="text-muted-foreground font-mono text-xs self-center">{p.type}</span>
          <span className="self-center">{p.required ? <span className="text-green-400 text-xs">sí</span> : <span className="text-muted-foreground text-xs">no</span>}</span>
          <span className="text-muted-foreground text-xs self-center">{p.description}</span>
        </div>
      ))}
    </div>
  );
}

function SectionDivider() {
  return <hr className="border-white/5 my-12" />;
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────

const NAV = [
  { label: "Primeros pasos", items: [
    { href: "#intro",   label: "Introducción" },
    { href: "#auth",    label: "Autenticación" },
    { href: "#errors",  label: "Errores" },
    { href: "#limits",  label: "Rate limits" },
  ]},
  { label: "Endpoints de usuario", items: [
    { href: "#chat",    label: "Chat Completions" },
    { href: "#oai",     label: "OpenAI-Compatible" },
    { href: "#images",  label: "Generación de imágenes" },
    { href: "#models",  label: "Listar modelos" },
    { href: "#status",  label: "Estado del sistema" },
    { href: "#me",      label: "Mi cuenta" },
    { href: "#usage",   label: "Uso y estadísticas" },
    { href: "#discord", label: "Discord Bot" },
  ]},
  { label: "Admin (X-Admin-Key)", items: [
    { href: "#admin-keys",      label: "Gestión de keys" },
    { href: "#admin-logs",      label: "Registros" },
    { href: "#admin-models",    label: "Modelos" },
    { href: "#admin-stats",     label: "Stats en tiempo real" },
  ]},
  { label: "Integraciones", items: [
    { href: "#sdk-python",  label: "Python" },
    { href: "#sdk-node",    label: "Node.js / TypeScript" },
    { href: "#sdk-discord", label: "Discord Bot" },
    { href: "#cog-python",  label: "📦 Cog Python (descarga)" },
  ]},
];

function Sidebar({ active }: { active: string }) {
  return (
    <div className="w-60 border-r border-white/5 p-5 hidden lg:block shrink-0 sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto">
      {NAV.map((group) => (
        <div key={group.label} className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-2 px-1">{group.label}</p>
          {group.items.map((item) => (
            <a key={item.href} href={item.href}
              className={`flex items-center gap-1.5 px-2 py-1.5 rounded text-sm transition-colors ${
                active === item.href
                  ? "text-white bg-primary/15 font-medium"
                  : "text-muted-foreground hover:text-white hover:bg-white/5"
              }`}>
              {active === item.href && <ChevronRight className="h-3 w-3 text-primary shrink-0" />}
              {item.label}
            </a>
          ))}
        </div>
      ))}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

const BASE = "https://autopy-ia-6a0f.onrender.com";

export default function Docs() {
  const { toast } = useToast();

  const copy = async (text: string) => {
    const ok = await safeCopy(text);
    toast({ title: ok ? "Copiado" : "No se pudo copiar — selecciónalo manualmente" });
  };

  return (
    <div className="flex-1 flex max-w-[1400px] mx-auto w-full">
      <Sidebar active="#intro" />

      <div className="flex-1 min-w-0 p-6 md:p-10 pb-40 overflow-y-auto">
        <div className="max-w-3xl mx-auto">

          {/* ── Intro ── */}
          <h1 id="intro" className="text-4xl font-bold tracking-tight mb-3 scroll-mt-20">Autopy AI — Documentación</h1>
          <p className="text-lg text-muted-foreground mb-2">
            Gateway unificado para múltiples LLMs con failover automático, caché inteligente, moderación y analíticas.
          </p>
          <p className="text-sm text-muted-foreground mb-8">
            Compatible con el formato OpenAI — puedes usar cualquier SDK de OpenAI apuntando la <code className="text-primary">base_url</code> a tu dominio de Autopy.
          </p>

          <div className="grid sm:grid-cols-3 gap-4 mb-10">
            {[
              { title: "Failover automático", desc: "Si OpenAI falla, Groq responde sin que el cliente note nada." },
              { title: "Caché inteligente", desc: "Respuestas idénticas se sirven desde caché con latencia < 5 ms." },
              { title: "Rate limiting", desc: "Cada API key tiene su propio límite de RPM configurable." },
            ].map((f) => (
              <div key={f.title} className="p-4 rounded-xl border border-white/5 bg-white/[0.02]">
                <p className="font-semibold text-sm mb-1">{f.title}</p>
                <p className="text-xs text-muted-foreground">{f.desc}</p>
              </div>
            ))}
          </div>

          <SectionDivider />

          {/* ── Auth ── */}
          <h2 id="auth" className="text-2xl font-bold mb-3 scroll-mt-20">Autenticación</h2>
          <p className="text-muted-foreground mb-4 text-sm">
            Los endpoints de usuario requieren una <strong>API key</strong> con prefijo <code className="text-primary">apt_</code>.<br />
            Los endpoints de admin requieren la cabecera <code className="text-primary">X-Admin-Key</code>.
          </p>
          <CodeBlock language="bash" code={`# Endpoints de usuario
Authorization: Bearer apt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Endpoints de administración
X-Admin-Key: tu-admin-key-secreta`} />

          <SectionDivider />

          {/* ── Errors ── */}
          <h2 id="errors" className="text-2xl font-bold mb-3 scroll-mt-20">Formato de errores</h2>
          <p className="text-muted-foreground mb-4 text-sm">
            Todos los errores devuelven JSON con el mismo formato, independientemente del código HTTP.
          </p>
          <CodeBlock language="json" code={`{
  "success": false,
  "error": "Descripción legible del error",
  "status_code": 404
}`} />
          <div className="rounded-lg border border-white/5 overflow-hidden my-4 text-sm">
            {[
              ["400", "Petición inválida — revisa los parámetros"],
              ["401", "API key ausente o inválida"],
              ["403", "Contenido bloqueado por moderación"],
              ["404", "Ruta no encontrada"],
              ["429", "Rate limit superado — espera e inténtalo de nuevo"],
              ["500", "Error interno — todos los proveedores fallaron"],
            ].map(([code, desc]) => (
              <div key={code} className="flex items-start gap-4 px-4 py-2.5 border-t border-white/5 first:border-t-0 hover:bg-white/[0.02]">
                <code className={`text-xs font-bold shrink-0 ${
                  code.startsWith("4") ? "text-yellow-400" : code.startsWith("5") ? "text-red-400" : "text-green-400"
                }`}>{code}</code>
                <span className="text-muted-foreground text-xs">{desc}</span>
              </div>
            ))}
          </div>

          <SectionDivider />

          {/* ── Rate limits ── */}
          <h2 id="limits" className="text-2xl font-bold mb-3 scroll-mt-20">Rate limits</h2>
          <p className="text-muted-foreground text-sm mb-4">
            Cada API key tiene un límite en RPM (requests por minuto) configurable desde el dashboard de admin.
            El valor por defecto es <strong>100 RPM</strong>. Al superar el límite recibirás un <code>429</code>.
          </p>

          <SectionDivider />

          {/* ══════════════════════════════════════════════════════
              ENDPOINTS DE USUARIO
          ══════════════════════════════════════════════════════ */}

          <h2 className="text-2xl font-bold mb-1 scroll-mt-20">Endpoints de usuario</h2>
          <p className="text-muted-foreground text-sm mb-8">Requieren <code className="text-primary">Authorization: Bearer apt_…</code></p>

          {/* Chat */}
          <h3 id="chat" className="text-xl font-semibold scroll-mt-20">Chat Completions</h3>
          <EndpointHeader method="POST" path="/api/v1/chat"
            description="Genera una respuesta de chat con failover automático entre proveedores. Incluye caché y moderación." />
          <ParamTable params={[
            { name: "messages", type: "array",  required: true,  description: "Array de mensajes con role (system|user|assistant) y content." },
            { name: "model",    type: "string",  required: false, description: "ID del modelo. Omitir o 'auto' para selección automática." },
            { name: "max_tokens", type: "int",  required: false, description: "Máximo de tokens a generar. Default: 1024." },
            { name: "temperature", type: "float", required: false, description: "Creatividad (0.0–2.0). Default: 0.7." },
          ]} />
          <CodeBlock language="bash" code={`curl -X POST ${BASE}/api/v1/chat \\
  -H "Authorization: Bearer apt_..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "messages": [
      { "role": "system", "content": "Eres un asistente útil." },
      { "role": "user",   "content": "¿Qué es la inteligencia artificial?" }
    ],
    "model": "llama-3.3-70b-versatile"
  }'`} />
          <CodeBlock language="json" code={`{
  "success": true,
  "text": "La inteligencia artificial es...",
  "model": "llama-3.3-70b-versatile",
  "provider": "groq",
  "tokensUsed": 148,
  "latencyMs": 820,
  "cached": false,
  "failoverCount": 0
}`} />

          {/* OpenAI-compat */}
          <h3 id="oai" className="text-xl font-semibold mt-10 scroll-mt-20">Chat — Formato OpenAI Compatible</h3>
          <p className="text-sm text-muted-foreground mb-2">
            Devuelve exactamente el mismo JSON que la API de OpenAI. Úsalo como drop-in para cualquier SDK o bot.
          </p>
          <EndpointHeader method="POST" path="/api/openai/v1/chat/completions"
            description="Endpoint compatible con OpenAI. Acepta el mismo body que openai.chat.completions.create()." />
          <CodeBlock language="python" code={`import openai

client = openai.OpenAI(
    api_key="apt_...",
    base_url="${BASE}/api/openai/v1",
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hola!"}],
)
print(response.choices[0].message.content)`} />
          <CodeBlock language="json" code={`{
  "id": "chatcmpl-a3f9e2b1c4d5",
  "object": "chat.completion",
  "created": 1721347200,
  "model": "llama-3.3-70b-versatile",
  "choices": [{
    "index": 0,
    "message": { "role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte?" },
    "finish_reason": "stop"
  }],
  "usage": { "total_tokens": 42 },
  "x_autopy": { "provider": "groq", "latency_ms": 620, "failover_count": 0 }
}`} />

          {/* Images */}
          <h3 id="images" className="text-xl font-semibold mt-10 scroll-mt-20">Generación de imágenes</h3>
          <EndpointHeader method="POST" path="/api/v1/images"
            description="Genera una imagen a partir de un prompt de texto usando gpt-image-1 con failover." />
          <ParamTable params={[
            { name: "prompt",  type: "string", required: true,  description: "Descripción en lenguaje natural de la imagen a generar." },
            { name: "size",    type: "string", required: false, description: "Resolución: 1024x1024 | 1536x1024 | 1024x1536. Default: 1024x1024." },
            { name: "format",  type: "string", required: false, description: "Formato de respuesta: url | base64. Default: url." },
          ]} />
          <CodeBlock language="bash" code={`curl -X POST ${BASE}/api/v1/images \\
  -H "Authorization: Bearer apt_..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "A futuristic city skyline at sunset, cinematic lighting",
    "size": "1024x1024",
    "format": "url"
  }'`} />
          <CodeBlock language="json" code={`{
  "success": true,
  "url": "https://...",
  "base64": null,
  "model": "gpt-image-1",
  "provider": "openai",
  "latencyMs": 8420
}`} />

          {/* Models */}
          <h3 id="models" className="text-xl font-semibold mt-10 scroll-mt-20">Listar modelos</h3>
          <EndpointHeader method="GET" path="/api/v1/models"
            description="Devuelve todos los modelos disponibles con su estado actual y capacidades." />
          <CodeBlock language="bash" code={`curl ${BASE}/api/v1/models \\
  -H "Authorization: Bearer apt_..."`} />
          <CodeBlock language="json" code={`{
  "success": true,
  "models": [
    {
      "id": "llama-3.3-70b-versatile",
      "name": "Llama 3.3 70B",
      "provider": "groq",
      "speed": "fast",
      "status": "active",
      "priority": 4,
      "maxTokens": 8192,
      "supportsImages": false,
      "latencyMs": 400
    }
  ]
}`} />

          {/* Status */}
          <h3 id="status" className="text-xl font-semibold mt-10 scroll-mt-20">Estado del sistema</h3>
          <p className="text-sm text-muted-foreground mb-2">Este endpoint es <strong>público</strong> — no requiere API key.</p>
          <EndpointHeader method="GET" path="/api/v1/status"
            description="Devuelve el estado en tiempo real de todos los modelos, latencia, CPU/RAM y métricas de caché." />
          <CodeBlock language="bash" code={`curl ${BASE}/api/v1/status`} />
          <CodeBlock language="json" code={`{
  "success": true,
  "modelsActive": 7,
  "modelsDown": 0,
  "totalRequests": 1842,
  "requestsToday": 94,
  "avgLatencyMs": 680.5,
  "uptime": 86400,
  "ramUsageMb": 312.4,
  "cpuPercent": 12.1,
  "cacheHitRate": 0.23,
  "models": [...]
}`} />

          {/* Me */}
          <h3 id="me" className="text-xl font-semibold mt-10 scroll-mt-20">Mi cuenta</h3>
          <EndpointHeader method="GET" path="/api/v1/me"
            description="Devuelve la información y estadísticas de uso de la API key autenticada." />
          <CodeBlock language="bash" code={`curl ${BASE}/api/v1/me \\
  -H "Authorization: Bearer apt_..."`} />
          <CodeBlock language="json" code={`{
  "success": true,
  "key": {
    "id": "abc123",
    "name": "Mi Bot de Discord",
    "status": "active",
    "rateLimit": 100,
    "createdAt": "2026-07-18T17:19:55Z",
    "expiresAt": null,
    "lastUsedAt": "2026-07-19T00:10:00Z"
  },
  "usage": {
    "totalRequests": 1842,
    "tokensUsed": 94500,
    "requestsToday": 94,
    "errorsTotal": 3
  }
}`} />

          {/* Usage */}
          <h3 id="usage" className="text-xl font-semibold mt-10 scroll-mt-20">Uso y estadísticas</h3>
          <EndpointHeader method="GET" path="/api/v1/usage"
            description="Desglose diario de requests, tokens y errores para los últimos N días." />
          <ParamTable params={[
            { name: "days", type: "int", required: false, description: "Número de días a consultar (1–90). Default: 30." },
          ]} />
          <CodeBlock language="bash" code={`curl "${BASE}/api/v1/usage?days=7" \\
  -H "Authorization: Bearer apt_..."`} />
          <CodeBlock language="json" code={`{
  "success": true,
  "days": 7,
  "data": [
    { "date": "2026-07-13", "requests": 0,  "tokens": 0,    "errors": 0 },
    { "date": "2026-07-14", "requests": 12, "tokens": 3400, "errors": 0 },
    { "date": "2026-07-19", "requests": 94, "tokens": 28000,"errors": 3 }
  ]
}`} />

          {/* Discord */}
          <h3 id="discord" className="text-xl font-semibold mt-10 scroll-mt-20">Discord Bot — Respuesta formateada</h3>
          <EndpointHeader method="POST" path="/api/v1/discord/chat"
            description="Igual que /v1/chat pero devuelve el formato de embeds de Discord listos para enviar con discord.py o discord.js." />
          <CodeBlock language="bash" code={`curl -X POST ${BASE}/api/v1/discord/chat \\
  -H "Authorization: Bearer apt_..." \\
  -H "Content-Type: application/json" \\
  -d '{"messages": [{"role": "user", "content": "Hola!"}]}'`} />
          <CodeBlock language="json" code={`{
  "embeds": [{
    "title": "Autopy AI",
    "description": "¡Hola! Estoy aquí para ayudarte.",
    "color": 5814783,
    "fields": [
      { "name": "Model",    "value": "llama-3.3-70b-versatile", "inline": true },
      { "name": "Provider", "value": "GROQ",                    "inline": true },
      { "name": "Tokens",   "value": "42",                      "inline": true }
    ],
    "footer": { "text": "Autopy AI • Powered by Multiple AI Models" },
    "timestamp": "2026-07-19T00:10:00Z"
  }]
}`} />

          <SectionDivider />

          {/* ══════════════════════════════════════════════════════
              ADMIN
          ══════════════════════════════════════════════════════ */}

          <h2 className="text-2xl font-bold mb-1 scroll-mt-20">Endpoints de administración</h2>
          <p className="text-muted-foreground text-sm mb-8">Requieren la cabecera <code className="text-primary">X-Admin-Key: &lt;tu-admin-key&gt;</code></p>

          {/* Admin keys */}
          <h3 id="admin-keys" className="text-xl font-semibold scroll-mt-20">Gestión de API Keys</h3>

          <EndpointHeader method="GET" path="/api/admin/keys"
            description="Lista todas las API keys del sistema con sus estadísticas de uso." />
          <CodeBlock language="bash" code={`curl ${BASE}/api/admin/keys \\
  -H "X-Admin-Key: tu-admin-key"`} />

          <EndpointHeader method="POST" path="/api/admin/keys"
            description="Crea una nueva API key." />
          <ParamTable params={[
            { name: "name",       type: "string", required: true,  description: "Nombre descriptivo de la key." },
            { name: "rate_limit", type: "int",    required: false, description: "Límite en RPM. 0 = ilimitado. Default: 100." },
            { name: "expires_at", type: "string", required: false, description: "Fecha de expiración ISO 8601. Null = nunca." },
          ]} />
          <CodeBlock language="bash" code={`curl -X POST ${BASE}/api/admin/keys \\
  -H "X-Admin-Key: tu-admin-key" \\
  -H "Content-Type: application/json" \\
  -d '{ "name": "Bot de producción", "rate_limit": 500 }'`} />

          <EndpointHeader method="PATCH" path="/api/admin/keys/{keyId}"
            description="Actualiza el nombre, estado o rate limit de una key existente." />
          <ParamTable params={[
            { name: "name",       type: "string", required: false, description: "Nuevo nombre." },
            { name: "status",     type: "string", required: false, description: "active | inactive | revoked" },
            { name: "rate_limit", type: "int",    required: false, description: "Nuevo límite RPM." },
          ]} />

          <EndpointHeader method="DELETE" path="/api/admin/keys/{keyId}"
            description="Elimina permanentemente una API key. Las peticiones que la usen fallarán de inmediato." />

          <EndpointHeader method="POST" path="/api/admin/keys/{keyId}/reset-usage"
            description="Resetea los contadores total_requests y tokens_used de una key a 0." />
          <CodeBlock language="bash" code={`curl -X POST ${BASE}/api/admin/keys/abc123/reset-usage \\
  -H "X-Admin-Key: tu-admin-key"`} />
          <CodeBlock language="json" code={`{
  "success": true,
  "message": "Usage counters reset for key 'Bot de producción'",
  "key": { "id": "abc123", "totalRequests": 0, "tokensUsed": 0, ... }
}`} />

          {/* Admin logs */}
          <h3 id="admin-logs" className="text-xl font-semibold mt-10 scroll-mt-20">Registros de solicitudes</h3>

          <EndpointHeader method="GET" path="/api/admin/logs"
            description="Lista los registros de solicitudes más recientes." />
          <ParamTable params={[
            { name: "limit",  type: "int",    required: false, description: "Número de registros a devolver (máx 200). Default: 50." },
            { name: "status", type: "string", required: false, description: "Filtrar por estado: success | error | blocked." },
          ]} />

          <EndpointHeader method="GET" path="/api/admin/logs/export"
            description="Exporta hasta 10 000 registros como JSON. Admite los mismos filtros que /logs." />
          <ParamTable params={[
            { name: "limit",    type: "int",    required: false, description: "Máx 10 000. Default: 1000." },
            { name: "status",   type: "string", required: false, description: "Filtrar por estado." },
            { name: "provider", type: "string", required: false, description: "Filtrar por proveedor (openai | groq)." },
          ]} />
          <CodeBlock language="bash" code={`curl "${BASE}/api/admin/logs/export?limit=500&status=error" \\
  -H "X-Admin-Key: tu-admin-key" > errores.json`} />

          <EndpointHeader method="DELETE" path="/api/admin/logs"
            description="Elimina registros en masa. Sin parámetros elimina TODOS." />
          <ParamTable params={[
            { name: "older_than_days", type: "int",    required: false, description: "Solo borrar registros más antiguos que N días. 0 = todos." },
            { name: "status",          type: "string", required: false, description: "Solo borrar registros con este estado." },
          ]} />
          <CodeBlock language="bash" code={`# Borrar todos los registros de error de hace más de 30 días
curl -X DELETE "${BASE}/api/admin/logs?older_than_days=30&status=error" \\
  -H "X-Admin-Key: tu-admin-key"`} />

          {/* Admin models */}
          <h3 id="admin-models" className="text-xl font-semibold mt-10 scroll-mt-20">Modelos</h3>

          <EndpointHeader method="GET" path="/api/admin/models"
            description="Lista todos los modelos con su estado actual y prioridad de enrutamiento." />

          <EndpointHeader method="PUT" path="/api/admin/models"
            description="Cambia el estado de un modelo para controlarlo manualmente." />
          <ParamTable params={[
            { name: "id",       type: "string", required: true,  description: "ID del modelo (ej. llama-3.3-70b-versatile)." },
            { name: "status",   type: "string", required: true,  description: "active | degraded | down" },
            { name: "priority", type: "int",    required: false, description: "Prioridad de enrutamiento (menor = primero)." },
          ]} />

          {/* Admin realtime */}
          <h3 id="admin-stats" className="text-xl font-semibold mt-10 scroll-mt-20">Stats en tiempo real</h3>

          <EndpointHeader method="GET" path="/api/admin/stats/realtime"
            description="Snapshot de los últimos 60 segundos: requests, errores, latencia media y distribución por proveedor." />
          <CodeBlock language="bash" code={`curl ${BASE}/api/admin/stats/realtime \\
  -H "X-Admin-Key: tu-admin-key"`} />
          <CodeBlock language="json" code={`{
  "success": true,
  "windowSeconds": 60,
  "asOf": "2026-07-19T12:00:00Z",
  "requests": 28,
  "errors": 1,
  "avgLatencyMs": 512,
  "byProvider": { "groq": 22, "openai": 6 },
  "recent": [...]
}`} />

          {/* Admin dashboard */}
          <EndpointHeader method="GET" path="/api/admin/dashboard"
            description="Métricas agregadas: requests totales, tokens, tasa de error, top modelos y tráfico de los últimos 7 días." />

          <SectionDivider />

          {/* ══════════════════════════════════════════════════════
              SDKs / Integraciones
          ══════════════════════════════════════════════════════ */}

          <h2 className="text-2xl font-bold mb-6 scroll-mt-20">Integraciones</h2>

          <h3 id="sdk-python" className="text-xl font-semibold scroll-mt-20">Python</h3>
          <p className="text-sm text-muted-foreground mb-3">
            Usa el SDK oficial de OpenAI apuntando la <code className="text-primary">base_url</code> a Autopy.
          </p>
          <CodeBlock language="bash" code={`pip install openai`} />
          <CodeBlock language="python" code={`import openai

client = openai.OpenAI(
    api_key="apt_...",                     # tu Autopy API key
    base_url="${BASE}/api/openai/v1",
)

# Chat
chat = client.chat.completions.create(
    model="llama-3.3-70b-versatile",      # o "auto" para failover
    messages=[
        {"role": "system", "content": "Eres un asistente de soporte."},
        {"role": "user",   "content": "¿Cómo cancelo mi suscripción?"},
    ],
)
print(chat.choices[0].message.content)`} />

          <h3 id="sdk-node" className="text-xl font-semibold mt-10 scroll-mt-20">Node.js / TypeScript</h3>
          <CodeBlock language="bash" code={`npm install openai`} />
          <CodeBlock language="typescript" code={`import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "apt_...",
  baseURL: "${BASE}/api/openai/v1",
});

const response = await client.chat.completions.create({
  model: "llama-3.3-70b-versatile",
  messages: [{ role: "user", content: "Hola desde TypeScript!" }],
});

console.log(response.choices[0].message.content);`} />

          <h3 id="sdk-discord" className="text-xl font-semibold mt-10 scroll-mt-20">Discord Bot (Python)</h3>
          <p className="text-sm text-muted-foreground mb-3">
            Dos formas de integrar Autopy en un bot de Discord:
          </p>
          <CodeBlock language="bash" code={`pip install discord.py openai`} />
          <CodeBlock language="python" code={`import discord
import openai

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

ai = openai.AsyncOpenAI(
    api_key="apt_...",
    base_url="${BASE}/api/openai/v1",
)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not bot.user.mentioned_in(message):
        return

    async with message.channel.typing():
        response = await ai.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system",  "content": "Eres el asistente del servidor."},
                {"role": "user",    "content": message.clean_content},
            ],
        )
        await message.reply(response.choices[0].message.content)

bot.run("TU_DISCORD_TOKEN")`} />

          <div className="mt-6 p-4 rounded-xl border border-primary/20 bg-primary/5">
            <p className="text-sm font-medium mb-1">💡 Endpoint de embeds de Discord</p>
            <p className="text-xs text-muted-foreground">
              También puedes usar <code className="text-primary">POST /api/v1/discord/chat</code> que devuelve el JSON de embeds
              listo para pasar directamente a <code className="text-primary">channel.send(embeds=data["embeds"])</code>.
            </p>
          </div>

          <SectionDivider />

          {/* ── Cog Python descargable ── */}
          <h3 id="cog-python" className="text-xl font-semibold scroll-mt-20 flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary" /> Cog Python — Archivo listo para usar
          </h3>
          <p className="text-sm text-muted-foreground mt-1 mb-5">
            Descarga el cog oficial de Autopy AI para <strong>discord.py</strong>. Solo necesitas editar tu API key
            y cargarlo en tu bot — nada más.
          </p>

          {/* Download card */}
          <div className="rounded-xl border border-primary/30 bg-gradient-to-br from-primary/10 to-primary/5 p-6 mb-6">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center shrink-0">
                  <Bot className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="font-semibold text-sm">autopy_discord_cog.py</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Cog completo con comandos <code className="text-primary">/setia</code>,{" "}
                    <code className="text-primary">/ia</code> y{" "}
                    <code className="text-primary">/iamodelo</code> · Historial por canal ·
                    Webhooks · Failover automático
                  </p>
                </div>
              </div>
              <a
                href="/autopy_discord_cog.py"
                download="autopy_discord_cog.py"
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors shrink-0"
              >
                <Download className="h-4 w-4" /> Descargar
              </a>
            </div>

            <div className="mt-5 grid sm:grid-cols-3 gap-3">
              {[
                { icon: "🔗", title: "/setia", desc: "Panel de control con botones para configurar canal, webhook e identidad de la IA." },
                { icon: "💬", title: "/ia pregunta", desc: "Consulta directa a la IA en cualquier canal. Responde con proveedor y latencia." },
                { icon: "🎛️", title: "/iamodelo nombre", desc: "Cambia el modelo de IA del canal (auto, llama-3.3-70b, gemini-2.0-flash…)." },
              ].map((f) => (
                <div key={f.title} className="p-3 rounded-lg bg-black/20 border border-white/5">
                  <p className="text-sm font-mono font-semibold mb-1">{f.icon} {f.title}</p>
                  <p className="text-xs text-muted-foreground">{f.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Quick start */}
          <p className="text-sm font-medium mb-2">Inicio rápido</p>
          <CodeBlock language="bash" code={`pip install discord.py aiohttp`} />
          <CodeBlock language="python" code={`# En tu archivo principal del bot:
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def main():
    await bot.load_extension("autopy_discord_cog")  # carga el cog
    await bot.start("TU_DISCORD_TOKEN")

import asyncio
asyncio.run(main())`} />

          <CodeBlock language="python" code={`# Dentro del cog, edita estas dos líneas:
AUTOPY_API_KEY  = "apt_..."                                      # Tu API key
AUTOPY_BASE_URL = "${BASE}/api/v1"  # URL ya correcta`} />

          <div className="mt-4 p-4 rounded-xl border border-blue-500/20 bg-blue-500/5">
            <p className="text-sm font-medium mb-1 text-blue-400">ℹ️ Cómo obtener una API key</p>
            <p className="text-xs text-muted-foreground">
              Ve al <a href="/dashboard" className="text-primary underline hover:text-white transition-colors">Dashboard</a>,
              inicia sesión con tu cuenta admin y crea una nueva API key. Copia el valor <code className="text-primary">apt_…</code> y
              pégalo en la variable <code className="text-primary">AUTOPY_API_KEY</code> del cog.
            </p>
          </div>

        </div>
      </div>
    </div>
  );
}
