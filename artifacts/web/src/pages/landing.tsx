import { motion } from "framer-motion";
import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import { Terminal, Zap, Shield, GitMerge } from "lucide-react";
import autopyLogo from "@/assets/autopy-logo.jpeg";

export default function Landing() {
  return (
    <div className="relative overflow-hidden w-full flex-1">
      {/* Background patterns */}
      <div className="absolute inset-0 bg-grid opacity-[0.03] z-0 pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-b from-background via-background to-black z-0 pointer-events-none" />
      
      {/* Glows */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-primary/20 blur-[120px] rounded-full pointer-events-none" />
      
      <div className="container relative z-10 mx-auto px-4 md:px-8 pt-32 pb-24">
        <div className="flex flex-col items-center text-center space-y-8 max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
          >
            <img src={autopyLogo} alt="Autopy AI" className="h-20 w-20 object-contain drop-shadow-[0_0_24px_rgba(124,58,237,0.6)]" />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-white/5 text-sm font-medium"
          >
            <span className="flex h-2 w-2 rounded-full bg-primary animate-pulse" />
            Autopy AI is now in public beta
          </motion.div>
          
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-5xl md:text-7xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-br from-white to-white/50"
          >
            One API. Every Model.
            <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">
              Zero Configuration.
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-xl text-muted-foreground max-w-2xl"
          >
            Stop rewriting your AI integrations. Autopy AI unifies OpenAI, Anthropic, and Groq behind a single, reliable API with automatic failover, caching, and analytics.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center gap-4 pt-4"
          >
            <Link href="/playground">
              <Button size="lg" className="h-12 px-8 text-base bg-primary hover:bg-primary/90">
                Try the Playground
              </Button>
            </Link>
            <Link href="/docs">
              <Button size="lg" variant="outline" className="h-12 px-8 text-base border-white/10 bg-white/5 hover:bg-white/10 text-white">
                Read the Docs
              </Button>
            </Link>
          </motion.div>
        </div>

        <motion.div 
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.4 }}
          className="mt-24 p-1 rounded-xl bg-gradient-to-b from-white/10 to-transparent max-w-4xl mx-auto"
        >
          <div className="rounded-lg bg-card/80 backdrop-blur-sm border border-white/5 overflow-hidden">
            <div className="flex items-center px-4 py-3 border-b border-white/5 bg-black/40">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500/80" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                <div className="w-3 h-3 rounded-full bg-green-500/80" />
              </div>
              <div className="ml-4 text-xs font-mono text-muted-foreground flex gap-4">
                <span className="text-primary">index.js</span>
              </div>
            </div>
            <div className="p-6 font-mono text-sm leading-relaxed text-gray-300 bg-black/40 overflow-x-auto">
              <pre>
                <code>
<span className="text-purple-400">import</span> {"{ AutopyClient }"} <span className="text-purple-400">from</span> <span className="text-green-400">'autopy-ai'</span>;{"\n\n"}
<span className="text-purple-400">const</span> ai = <span className="text-purple-400">new</span> AutopyClient({"{\n"}
{"  "}apiKey: <span className="text-green-400">'apt_...'</span>,{"\n"}
{"}"});{"\n\n"}
<span className="text-gray-500">// Requests automatically load-balance and failover</span>{"\n"}
<span className="text-purple-400">const</span> response = <span className="text-purple-400">await</span> ai.chat.completions.create({"{\n"}
{"  "}model: <span className="text-green-400">'auto'</span>, <span className="text-gray-500">// Or specify 'gpt-4o', 'claude-3.5-sonnet', 'llama3'</span>{"\n"}
{"  "}messages: [{"{ "}role: <span className="text-green-400">'user'</span>, content: <span className="text-green-400">'Explain quantum computing'</span>{" }"}],{"\n"}
{"}"});{"\n\n"}
<span className="text-blue-400">console</span>.log(response.text);
                </code>
              </pre>
            </div>
          </div>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8 mt-32 max-w-5xl mx-auto">
          <FeatureCard 
            icon={GitMerge} 
            title="Smart Failover" 
            desc="If a provider goes down, we automatically route your request to the next best model. Zero downtime for your users."
          />
          <FeatureCard 
            icon={Zap} 
            title="Global Edge Caching" 
            desc="Identical prompts are cached at the edge, returning responses in < 50ms and costing you exactly $0."
          />
          <FeatureCard 
            icon={Shield} 
            title="Enterprise Security" 
            desc="SOC2 compliant, zero-retention policies. We don't train on your data, and we ensure providers don't either."
          />
        </div>
      </div>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, desc }: { icon: any, title: string, desc: string }) {
  return (
    <div className="flex flex-col gap-4 p-6 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.04] transition-colors">
      <div className="w-12 h-12 rounded-lg bg-primary/20 flex items-center justify-center text-primary">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="text-muted-foreground leading-relaxed">{desc}</p>
    </div>
  );
}
