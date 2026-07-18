import { useState, useRef, useEffect } from "react";
import { useAuth, getCustomFetchOptions } from "@/lib/auth";
import { useCreateChatCompletion, useGenerateImage, useListModels } from "@workspace/api-client-react";
import type { ChatMessage } from "@workspace/api-client-react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Send, Settings, Sparkles, Image as ImageIcon, MessageSquare,
  Clock, Cpu, Terminal, Eye, EyeOff, AlertCircle,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import autopyLogo from "@/assets/autopy-logo.png";

// ─── API Key gate ─────────────────────────────────────────────────────────────

function ApiKeyGate({ onSave }: { onSave: (key: string) => void }) {
  const [value, setValue] = useState("");
  const [show, setShow] = useState(false);

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
      <div className="w-full max-w-sm space-y-8 text-center">
        <div className="flex flex-col items-center gap-4">
          <img src={autopyLogo} alt="Autopy AI" className="h-14 w-14 object-contain drop-shadow-[0_0_16px_rgba(124,58,237,0.5)]" />
          <div>
            <h2 className="text-2xl font-bold">Playground</h2>
            <p className="text-muted-foreground text-sm mt-1">
              Ingresa una API key <span className="font-mono text-primary">apt_…</span> para empezar.
              Créala en el <a href="/dashboard" className="underline hover:text-white transition-colors">Dashboard</a>.
            </p>
          </div>
        </div>
        <Card className="glass border-white/10 text-left">
          <CardContent className="pt-5 space-y-3">
            <label className="text-sm font-medium text-muted-foreground">API Key</label>
            <div className="relative">
              <Input
                type={show ? "text" : "password"}
                placeholder="apt_..."
                value={value}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && value.trim() && onSave(value.trim())}
                className="bg-black/40 border-white/10 pr-10 font-mono"
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
            <Button
              className="w-full"
              disabled={!value.trim()}
              onClick={() => onSave(value.trim())}
            >
              Acceder al Playground
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ─── Playground shell ─────────────────────────────────────────────────────────
// We use plain state for the active tab to avoid Radix UI Tabs
// mounting both panels simultaneously — that causes Select portals to go
// orphan and triggers the "removeChild" React reconciliation crash.

type Tab = "chat" | "image";

export default function Playground() {
  const { apiKey, setApiKey } = useAuth();
  const [tab, setTab] = useState<Tab>("chat");

  if (!apiKey) return <ApiKeyGate onSave={setApiKey} />;

  return (
    <div className="flex-1 flex flex-col p-6 gap-6 max-w-7xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Playground</h1>
          <p className="text-muted-foreground text-sm">Prueba modelos y prompts de forma interactiva.</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => setApiKey("")} className="border-white/10">
          <Settings className="h-4 w-4 mr-2" /> Cambiar key
        </Button>
      </div>

      {/* Manual tab bar — avoids Radix Tabs portal issues */}
      <div className="flex gap-1 p-1 rounded-lg bg-black/40 border border-white/5 w-fit">
        <button
          onClick={() => setTab("chat")}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            tab === "chat" ? "bg-primary/20 text-white" : "text-muted-foreground hover:text-white hover:bg-white/5"
          }`}
        >
          <MessageSquare className="h-4 w-4" /> Chat
        </button>
        <button
          onClick={() => setTab("image")}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            tab === "image" ? "bg-primary/20 text-white" : "text-muted-foreground hover:text-white hover:bg-white/5"
          }`}
        >
          <ImageIcon className="h-4 w-4" /> Imágenes
        </button>
      </div>

      {/* Panel — only ONE child rendered at a time → no orphan portals */}
      <div className="flex-1 border border-white/5 rounded-xl bg-card/40 backdrop-blur flex overflow-hidden min-h-[500px]">
        {tab === "chat" ? (
          <ChatInterface apiKey={apiKey} />
        ) : (
          <ImageInterface apiKey={apiKey} />
        )}
      </div>
    </div>
  );
}

// ─── Chat ─────────────────────────────────────────────────────────────────────

function ChatInterface({ apiKey }: { apiKey: string }) {
  const fetchOpts = getCustomFetchOptions({ apiKey });
  const { data: modelsData } = useListModels({ request: fetchOpts });
  const chatModels = modelsData?.models?.filter((m) => !m.supportsImages) ?? [];

  const [model, setModel] = useState("auto");
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "system", content: "You are a helpful AI assistant." },
  ]);
  const [input, setInput] = useState("");
  const [meta, setMeta] = useState<{
    latencyMs?: number; tokensUsed?: number; provider?: string;
    model?: string; cached?: boolean; failoverCount?: number;
  } | null>(null);

  const { toast } = useToast();
  const createChat = useCreateChatCompletion({ request: fetchOpts });
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, createChat.isPending]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    const text = input.trim();
    if (!text || createChat.isPending) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    const updated = [...messages, userMsg];
    setMessages(updated);
    setInput("");

    createChat.mutate(
      { data: { messages: updated, model: model !== "auto" ? model : undefined } },
      {
        onSuccess: (res) => {
          setMessages([...updated, { role: "assistant", content: res.text ?? "" }]);
          setMeta({
            latencyMs: res.latencyMs,
            tokensUsed: res.tokensUsed,
            provider: res.provider,
            model: res.model,
            cached: res.cached,
            failoverCount: res.failoverCount,
          });
        },
        onError: (err: any) => {
          const msg =
            err?.response?.detail?.error ??
            err?.message ??
            "No se pudo obtener respuesta del servidor.";
          setMessages([...updated, { role: "assistant", content: `⚠️ Error: ${msg}` }]);
          toast({ title: "Error en la petición", description: msg, variant: "destructive" });
        },
      }
    );
  };

  const visibleMessages = messages.filter((m) => m.role !== "system");
  const systemPrompt = messages.find((m) => m.role === "system")?.content ?? "";

  return (
    <div className="flex flex-col w-full">
      {/* Toolbar */}
      <div className="flex items-center gap-3 flex-wrap p-4 border-b border-white/5 bg-black/20">
        <Select value={model} onValueChange={setModel}>
          <SelectTrigger className="w-52 h-8 bg-black/40 border-white/10 text-sm">
            <SelectValue placeholder="Modelo" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="auto">Auto (mejor disponible)</SelectItem>
            {chatModels.map((m) => (
              <SelectItem key={m.id} value={m.id}>
                {m.name} · {m.provider}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {meta && (
          <div className="ml-auto flex items-center gap-3 text-xs font-mono text-muted-foreground flex-wrap">
            {meta.cached && (
              <Badge variant="secondary" className="bg-primary/20 text-primary">CACHED</Badge>
            )}
            {!!meta.failoverCount && (
              <Badge variant="destructive">Failovers: {meta.failoverCount}</Badge>
            )}
            <span className="flex items-center gap-1">
              <Cpu className="w-3 h-3" /> {meta.provider} / {meta.model}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" /> {meta.latencyMs}ms
            </span>
            <span className="flex items-center gap-1">
              <Terminal className="w-3 h-3" /> {meta.tokensUsed ?? "—"} tok
            </span>
          </div>
        )}
      </div>

      {/* System prompt strip */}
      {systemPrompt && (
        <div className="px-4 py-2 border-b border-white/5 bg-white/[0.02] flex items-center gap-2">
          <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-mono">System</span>
          <span className="text-xs text-muted-foreground truncate">{systemPrompt}</span>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
        {visibleMessages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground gap-2 py-16">
            <MessageSquare className="h-10 w-10 opacity-20" />
            <p className="text-sm">Escribe un mensaje para empezar.</p>
          </div>
        )}
        {visibleMessages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-card border border-white/5 text-card-foreground"
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>
            </div>
          </div>
        ))}

        {createChat.isPending && (
          <div className="flex justify-start">
            <div className="rounded-xl px-4 py-3 bg-card border border-white/5">
              <span className="flex gap-1 items-center h-5">
                {[0, 150, 300].map((d) => (
                  <span
                    key={d}
                    className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce"
                    style={{ animationDelay: `${d}ms` }}
                  />
                ))}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-white/5 bg-black/20">
        <form onSubmit={handleSubmit} className="flex gap-2 items-end">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            placeholder="Escribe un mensaje… (Enter para enviar, Shift+Enter para nueva línea)"
            className="min-h-[44px] max-h-[180px] resize-none py-3 bg-black/40 border-white/10 focus-visible:ring-primary text-sm"
            rows={1}
          />
          <Button
            type="submit"
            size="icon"
            className="h-[44px] w-[44px] shrink-0 bg-primary hover:bg-primary/90"
            disabled={!input.trim() || createChat.isPending}
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}

// ─── Image generation ─────────────────────────────────────────────────────────

function ImageInterface({ apiKey }: { apiKey: string }) {
  const fetchOpts = getCustomFetchOptions({ apiKey });
  const { data: modelsData } = useListModels({ request: fetchOpts });
  const imageModels = modelsData?.models?.filter((m) => m.supportsImages) ?? [];

  const [model, setModel] = useState("auto");
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<{
    url?: string | null; error?: string; latencyMs?: number; provider?: string; model?: string;
  } | null>(null);

  const { toast } = useToast();
  const generate = useGenerateImage({ request: fetchOpts });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || generate.isPending) return;
    setResult(null);
    generate.mutate(
      { data: { prompt: prompt.trim(), model: model !== "auto" ? model : undefined, size: "1024x1024", format: "url" } },
      {
        onSuccess: (res) => {
          setResult({ url: res.url, latencyMs: res.latencyMs, provider: res.provider, model: res.model });
        },
        onError: (err: any) => {
          const msg = err?.response?.detail?.error ?? err?.message ?? "No se pudo generar la imagen.";
          setResult({ error: msg });
          toast({ title: "Error al generar imagen", description: msg, variant: "destructive" });
        },
      }
    );
  };

  return (
    <div className="flex flex-col w-full p-6 gap-5">
      {/* Controls */}
      <div className="flex gap-3 items-center flex-wrap">
        <Select value={model} onValueChange={setModel}>
          <SelectTrigger className="w-60 bg-black/40 border-white/10">
            <SelectValue placeholder="Modelo de imagen" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="auto">Auto (mejor disponible)</SelectItem>
            {imageModels.map((m) => (
              <SelectItem key={m.id} value={m.id}>{m.name} · {m.provider}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Prompt */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe la imagen que quieres generar…"
          className="h-12 bg-black/40 border-white/10 text-sm"
        />
        <Button
          type="submit"
          className="h-12 px-6 bg-primary hover:bg-primary/90 gap-2 shrink-0"
          disabled={!prompt.trim() || generate.isPending}
        >
          <Sparkles className="w-4 h-4" />
          Generar
        </Button>
      </form>

      {/* Result area */}
      <div className="flex-1 border border-white/5 bg-black/20 rounded-xl overflow-hidden flex flex-col items-center justify-center p-8 min-h-[300px]">
        {generate.isPending ? (
          <div className="flex flex-col items-center gap-4 text-muted-foreground">
            <div className="w-12 h-12 rounded-full border-2 border-primary border-t-transparent animate-spin" />
            <p className="font-mono text-sm">Generando imagen…</p>
          </div>
        ) : result?.error ? (
          <div className="flex flex-col items-center gap-3 text-center max-w-md">
            <AlertCircle className="h-10 w-10 text-destructive opacity-80" />
            <p className="font-semibold text-destructive">Error al generar</p>
            <p className="text-sm text-muted-foreground">{result.error}</p>
          </div>
        ) : result?.url ? (
          <div className="w-full h-full flex flex-col items-center justify-center gap-4">
            <img
              src={result.url}
              alt={prompt}
              className="max-w-full max-h-[420px] object-contain rounded-lg shadow-2xl"
            />
            <div className="flex items-center gap-3 text-xs font-mono text-muted-foreground bg-black/40 px-3 py-1.5 rounded-full border border-white/10">
              <span className="flex items-center gap-1"><Cpu className="w-3 h-3" /> {result.provider} / {result.model}</span>
              <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {result.latencyMs}ms</span>
            </div>
          </div>
        ) : (
          <div className="text-center text-muted-foreground max-w-sm">
            <ImageIcon className="w-12 h-12 mx-auto mb-4 opacity-20" />
            <p className="text-sm">Escribe un prompt arriba para generar una imagen.</p>
          </div>
        )}
      </div>
    </div>
  );
}
