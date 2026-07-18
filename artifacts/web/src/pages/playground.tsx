import { useState, useRef, useEffect } from "react";
import { useAuth, getCustomFetchOptions } from "@/lib/auth";
import { useCreateChatCompletion, useGenerateImage, useListModels } from "@workspace/api-client-react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Play, Send, Settings, Sparkles, Image as ImageIcon, MessageSquare, Clock, Cpu, Terminal } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ChatMessage, ChatMessageRole } from "@workspace/api-client-react";

export default function Playground() {
  const { apiKey, setApiKey } = useAuth();
  
  if (!apiKey) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center max-w-md mx-auto">
        <div className="w-16 h-16 bg-primary/20 rounded-2xl flex items-center justify-center mb-6">
          <Settings className="w-8 h-8 text-primary" />
        </div>
        <h2 className="text-2xl font-bold mb-2">API Key Required</h2>
        <p className="text-muted-foreground mb-8">
          Enter an API key to test models in the playground. If you are running locally, you can create one in the dashboard using your admin key.
        </p>
        <Card className="w-full glass">
          <CardContent className="pt-6">
            <div className="flex flex-col gap-4">
              <Input 
                type="password"
                placeholder="apt_..."
                onChange={(e) => {
                  if (e.target.value.trim()) {
                    setApiKey(e.target.value.trim());
                  }
                }}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col p-6 gap-6 max-w-7xl mx-auto w-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Playground</h1>
          <p className="text-muted-foreground text-sm">Test models and prompts interactively.</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => setApiKey("")}>
          Clear API Key
        </Button>
      </div>

      <Tabs defaultValue="chat" className="flex-1 flex flex-col">
        <TabsList className="grid w-full grid-cols-2 md:w-96 glass bg-black/40">
          <TabsTrigger value="chat" className="data-[state=active]:bg-primary/20"><MessageSquare className="w-4 h-4 mr-2"/> Chat</TabsTrigger>
          <TabsTrigger value="image" className="data-[state=active]:bg-primary/20"><ImageIcon className="w-4 h-4 mr-2"/> Images</TabsTrigger>
        </TabsList>
        
        <div className="flex-1 mt-6 border border-white/5 rounded-xl bg-card/40 backdrop-blur flex overflow-hidden">
          <TabsContent value="chat" className="m-0 flex-1 flex flex-col h-full border-none shadow-none outline-none">
            <ChatInterface apiKey={apiKey} />
          </TabsContent>
          <TabsContent value="image" className="m-0 flex-1 flex flex-col h-full border-none shadow-none outline-none">
            <ImageInterface apiKey={apiKey} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}

function ChatInterface({ apiKey }: { apiKey: string }) {
  const { data: modelsData } = useListModels({ request: getCustomFetchOptions({ apiKey }) });
  const chatModels = modelsData?.models?.filter(m => !m.supportsImages) || [];
  
  const [model, setModel] = useState("auto");
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: ChatMessageRole.system, content: "You are a helpful AI assistant." }
  ]);
  const [input, setInput] = useState("");
  
  const createChat = useCreateChatCompletion({ request: getCustomFetchOptions({ apiKey }) });
  
  const [lastResponseInfo, setLastResponseInfo] = useState<{
    latencyMs?: number;
    tokensUsed?: number;
    provider?: string;
    model?: string;
    cached?: boolean;
    failoverCount?: number;
  } | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, createChat.isPending]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || createChat.isPending) return;

    const userMsg: ChatMessage = { role: ChatMessageRole.user, content: input.trim() };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");

    createChat.mutate({
      data: {
        messages: newMessages,
        model: model !== "auto" ? model : undefined
      }
    }, {
      onSuccess: (data) => {
        setMessages([...newMessages, { role: ChatMessageRole.assistant, content: data.text }]);
        setLastResponseInfo({
          latencyMs: data.latencyMs,
          tokensUsed: data.tokensUsed,
          provider: data.provider,
          model: data.model,
          cached: data.cached,
          failoverCount: data.failoverCount
        });
      },
      onError: (err: any) => {
        setMessages([...newMessages, { role: ChatMessageRole.assistant, content: `Error: ${err.message || "Failed to generate response"}` }]);
      }
    });
  };

  return (
    <div className="flex flex-col h-full min-h-[600px]">
      <div className="flex items-center gap-4 p-4 border-b border-white/5 bg-black/20">
        <Select value={model} onValueChange={setModel}>
          <SelectTrigger className="w-[200px] h-8 bg-black/40 border-white/10">
            <SelectValue placeholder="Select model" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="auto">Auto (Best Available)</SelectItem>
            {chatModels.map(m => (
              <SelectItem key={m.id} value={m.id}>{m.name} ({m.provider})</SelectItem>
            ))}
          </SelectContent>
        </Select>
        
        {lastResponseInfo && (
          <div className="ml-auto flex items-center gap-3 text-xs font-mono text-muted-foreground">
            {lastResponseInfo.cached && <Badge variant="secondary" className="bg-primary/20 text-primary hover:bg-primary/30">CACHED</Badge>}
            {lastResponseInfo.failoverCount ? <Badge variant="destructive">Failovers: {lastResponseInfo.failoverCount}</Badge> : null}
            <span className="flex items-center gap-1"><Cpu className="w-3 h-3" /> {lastResponseInfo.provider} / {lastResponseInfo.model}</span>
            <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {lastResponseInfo.latencyMs}ms</span>
            <span className="flex items-center gap-1"><Terminal className="w-3 h-3" /> {lastResponseInfo.tokensUsed} tok</span>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-xl px-4 py-3 ${
              msg.role === 'user' 
                ? 'bg-primary text-primary-foreground' 
                : msg.role === 'system'
                  ? 'bg-white/5 text-muted-foreground border border-white/10 font-mono text-sm'
                  : 'bg-card border border-white/5 text-card-foreground'
            }`}>
              {msg.role === 'system' && <div className="text-[10px] uppercase tracking-wider mb-1 opacity-50">System Prompt</div>}
              <div className="whitespace-pre-wrap">{msg.content}</div>
            </div>
          </div>
        ))}
        {createChat.isPending && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-xl px-4 py-3 bg-card border border-white/5 text-card-foreground">
              <span className="flex gap-1 items-center h-5">
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "300ms" }} />
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-white/5 bg-black/20">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Textarea 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="Type a message..."
            className="min-h-[44px] h-[44px] max-h-[200px] resize-none py-3 bg-black/40 border-white/10 focus-visible:ring-primary"
          />
          <Button type="submit" size="icon" className="h-[44px] w-[44px] shrink-0 bg-primary hover:bg-primary/90" disabled={!input.trim() || createChat.isPending}>
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}

function ImageInterface({ apiKey }: { apiKey: string }) {
  const { data: modelsData } = useListModels({ request: getCustomFetchOptions({ apiKey }) });
  const imageModels = modelsData?.models?.filter(m => m.supportsImages) || [];
  
  const [model, setModel] = useState("auto");
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<{ url?: string | null, error?: string, latencyMs?: number, provider?: string, model?: string } | null>(null);
  
  const generate = useGenerateImage({ request: getCustomFetchOptions({ apiKey }) });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || generate.isPending) return;

    setResult(null);
    generate.mutate({
      data: {
        prompt: prompt.trim(),
        model: model !== "auto" ? model : undefined,
        size: "1024x1024",
        format: "url"
      }
    }, {
      onSuccess: (data) => {
        setResult({
          url: data.url,
          latencyMs: data.latencyMs,
          provider: data.provider,
          model: data.model
        });
      },
      onError: (err: any) => {
        setResult({ error: err.message || "Failed to generate image" });
      }
    });
  };

  return (
    <div className="flex flex-col h-full min-h-[600px] p-6 gap-6">
      <div className="flex items-center gap-4">
        <Select value={model} onValueChange={setModel}>
          <SelectTrigger className="w-[250px] bg-black/40 border-white/10">
            <SelectValue placeholder="Select image model" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="auto">Auto (Best Available)</SelectItem>
            {imageModels.map(m => (
              <SelectItem key={m.id} value={m.id}>{m.name} ({m.provider})</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input 
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe an image..."
          className="h-12 bg-black/40 border-white/10 text-base"
        />
        <Button type="submit" className="h-12 px-8 bg-primary hover:bg-primary/90 gap-2" disabled={!prompt.trim() || generate.isPending}>
          <Sparkles className="w-4 h-4" /> Generate
        </Button>
      </form>

      <div className="flex-1 border border-white/5 bg-black/20 rounded-xl overflow-hidden flex flex-col items-center justify-center p-8 relative">
        {generate.isPending ? (
          <div className="flex flex-col items-center gap-4 text-muted-foreground">
            <div className="w-12 h-12 rounded-full border-2 border-primary border-t-transparent animate-spin" />
            <p className="font-mono text-sm">Generating image...</p>
          </div>
        ) : result?.error ? (
          <div className="text-destructive max-w-md text-center">
            <h3 className="font-bold mb-2">Generation Failed</h3>
            <p className="text-sm opacity-80">{result.error}</p>
          </div>
        ) : result?.url ? (
          <div className="w-full h-full flex flex-col items-center justify-center gap-4">
            <img src={result.url} alt={prompt} className="max-w-full max-h-[400px] object-contain rounded-lg shadow-2xl" />
            <div className="flex items-center gap-3 text-xs font-mono text-muted-foreground bg-black/40 px-3 py-1.5 rounded-full border border-white/10">
              <span className="flex items-center gap-1"><Cpu className="w-3 h-3" /> {result.provider} / {result.model}</span>
              <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {result.latencyMs}ms</span>
            </div>
          </div>
        ) : (
          <div className="text-center text-muted-foreground max-w-sm">
            <ImageIcon className="w-12 h-12 mx-auto mb-4 opacity-20" />
            <p>Enter a prompt above to generate an image.</p>
          </div>
        )}
      </div>
    </div>
  );
}
