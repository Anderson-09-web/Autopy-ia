import { Component, type ReactNode, type ErrorInfo } from "react";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Log to console in dev only — never surfaces credentials
    if (import.meta.env.DEV) {
      console.error("[ErrorBoundary]", error, info.componentStack);
    }
  }

  reset = () => {
    this.setState({ error: null });
    this.props.onReset?.();
  };

  render() {
    if (this.state.error) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center gap-4">
          <AlertTriangle className="h-10 w-10 text-destructive opacity-80" />
          <div>
            <p className="font-semibold text-lg">Algo salió mal</p>
            <p className="text-sm text-muted-foreground mt-1 font-mono max-w-sm break-all">
              {this.state.error.message}
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={this.reset} className="gap-2">
            <RefreshCw className="h-4 w-4" /> Reintentar
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}
