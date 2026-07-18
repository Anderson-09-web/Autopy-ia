import { Card } from "@/components/ui/card";
import { Terminal, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

export default function Docs() {
  const { toast } = useToast();

  const copy = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({ title: "Copied to clipboard" });
  };

  return (
    <div className="flex-1 flex max-w-7xl mx-auto w-full">
      {/* Sidebar Navigation */}
      <div className="w-64 border-r border-white/5 p-6 hidden md:block shrink-0 sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto">
        <div className="space-y-6">
          <div>
            <h4 className="font-semibold mb-3 text-sm text-white">Getting Started</h4>
            <div className="space-y-2 text-sm">
              <a href="#intro" className="block text-primary">Introduction</a>
              <a href="#auth" className="block text-muted-foreground hover:text-white transition-colors">Authentication</a>
              <a href="#errors" className="block text-muted-foreground hover:text-white transition-colors">Errors</a>
            </div>
          </div>
          <div>
            <h4 className="font-semibold mb-3 text-sm text-white">API Reference</h4>
            <div className="space-y-2 text-sm">
              <a href="#chat" className="block text-muted-foreground hover:text-white transition-colors">Chat Completions</a>
              <a href="#images" className="block text-muted-foreground hover:text-white transition-colors">Image Generation</a>
              <a href="#models" className="block text-muted-foreground hover:text-white transition-colors">List Models</a>
            </div>
          </div>
          <div>
            <h4 className="font-semibold mb-3 text-sm text-white">SDKs</h4>
            <div className="space-y-2 text-sm">
              <a href="#sdk-node" className="block text-muted-foreground hover:text-white transition-colors">Node.js / TypeScript</a>
              <a href="#sdk-python" className="block text-muted-foreground hover:text-white transition-colors">Python</a>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-6 md:p-12 max-w-4xl pb-32 overflow-y-auto scroll-smooth">
        <div className="prose prose-invert prose-pre:bg-black/40 prose-pre:border prose-pre:border-white/10 max-w-none">
          <h1 id="intro" className="text-4xl font-bold tracking-tight mb-4">Autopy AI Documentation</h1>
          <p className="text-xl text-muted-foreground mb-8">
            The unified API for accessing all major LLMs with built-in failover, caching, and analytics.
          </p>

          <hr className="border-white/5 my-10" />

          <h2 id="auth">Authentication</h2>
          <p>
            Authenticate your requests by including your API key in the <code>Authorization</code> HTTP header.
          </p>
          <CodeBlock 
            language="bash"
            code={`curl https://api.autopy.ai/v1/models \\
  -H "Authorization: Bearer apt_1234567890abcdef"`} 
            onCopy={() => copy(`curl https://api.autopy.ai/v1/models -H "Authorization: Bearer apt_1234567890abcdef"`)}
          />

          <hr className="border-white/5 my-10" />

          <h2 id="chat">Chat Completions</h2>
          <p>
            Create a chat completion. The API conforms to the standard OpenAI format, meaning you can drop Autopy AI directly into existing apps by simply changing the base URL.
          </p>

          <div className="flex flex-col gap-2 mb-4 mt-6">
            <div className="flex items-center gap-3">
              <span className="px-2 py-1 rounded bg-green-500/10 text-green-400 border border-green-500/20 text-xs font-mono font-bold">POST</span>
              <code className="text-sm">/v1/chat</code>
            </div>
          </div>

          <CodeBlock 
            language="javascript"
            code={`const response = await fetch('https://api.autopy.ai/v1/chat', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer apt_...',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'auto', // Or 'gpt-4o', 'claude-3.5-sonnet', etc
    messages: [
      { role: 'system', content: 'You are a helpful assistant.' },
      { role: 'user', content: 'Hello!' }
    ]
  })
});

const data = await response.json();
console.log(data.text);`}
            onCopy={() => copy("...")} // omitted full copy string for brevity
          />

          <hr className="border-white/5 my-10" />

          <h2 id="images">Image Generation</h2>
          <p>Generate images from text prompts using DALL-E, Midjourney, or Stable Diffusion under the hood.</p>

          <div className="flex flex-col gap-2 mb-4 mt-6">
            <div className="flex items-center gap-3">
              <span className="px-2 py-1 rounded bg-green-500/10 text-green-400 border border-green-500/20 text-xs font-mono font-bold">POST</span>
              <code className="text-sm">/v1/images</code>
            </div>
          </div>

          <CodeBlock 
            language="python"
            code={`import requests

response = requests.post(
    'https://api.autopy.ai/v1/images',
    headers={'Authorization': 'Bearer apt_...'},
    json={
        'prompt': 'A cyberpunk cityscape at night',
        'size': '1024x1024',
        'format': 'url'
    }
)
print(response.json()['url'])`}
            onCopy={() => copy("...")}
          />
        </div>
      </div>
    </div>
  );
}

function CodeBlock({ code, language, onCopy }: { code: string, language: string, onCopy: () => void }) {
  return (
    <div className="relative group rounded-lg overflow-hidden my-6 border border-white/10 bg-[#0d0d0d]">
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/10 bg-black/40">
        <span className="text-xs text-muted-foreground font-mono">{language}</span>
        <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-white" onClick={onCopy}>
          <Copy className="h-3 w-3" />
        </Button>
      </div>
      <pre className="p-4 overflow-x-auto text-sm font-mono text-gray-300 !m-0 !bg-transparent !border-none">
        <code>{code}</code>
      </pre>
    </div>
  );
}
