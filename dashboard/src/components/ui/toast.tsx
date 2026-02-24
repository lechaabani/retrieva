"use client";

import React, { createContext, useContext, useState, useCallback, useRef } from "react";
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from "lucide-react";

type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
  duration?: number;
}

interface ToastContextType {
  toast: (opts: { type?: ToastType; title: string; description?: string; duration?: number }) => void;
  success: (title: string, description?: string) => void;
  error: (title: string, description?: string) => void;
  warning: (title: string, description?: string) => void;
  info: (title: string, description?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

const ICONS: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle2 size={18} className="text-green-500" />,
  error: <XCircle size={18} className="text-red-500" />,
  warning: <AlertTriangle size={18} className="text-amber-500" />,
  info: <Info size={18} className="text-blue-500" />,
};

const COLORS: Record<ToastType, string> = {
  success: "border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950",
  error: "border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950",
  warning: "border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950",
  info: "border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950",
};

function ToastItem({ toast: t, onDismiss }: { toast: Toast; onDismiss: () => void }) {
  const [exiting, setExiting] = React.useState(false);

  const handleDismiss = useCallback(() => {
    setExiting(true);
    setTimeout(onDismiss, 200);
  }, [onDismiss]);

  React.useEffect(() => {
    const dur = t.duration ?? 4000;
    if (dur > 0) {
      const timer = setTimeout(handleDismiss, dur);
      return () => clearTimeout(timer);
    }
  }, [t.duration, handleDismiss]);

  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 rounded-xl border shadow-lg backdrop-blur-sm max-w-sm w-full transition-all duration-200 ${
        exiting ? "opacity-0 translate-x-4" : "opacity-100 translate-x-0"
      } ${COLORS[t.type]}`}
      style={{ animation: exiting ? undefined : "toastSlideIn 0.3s ease-out" }}
    >
      <span className="shrink-0 mt-0.5">{ICONS[t.type]}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-text-primary">{t.title}</p>
        {t.description && (
          <p className="text-xs text-text-secondary mt-0.5">{t.description}</p>
        )}
      </div>
      <button
        onClick={handleDismiss}
        className="shrink-0 p-0.5 rounded-lg text-text-muted hover:text-text-primary transition-colors"
      >
        <X size={14} />
      </button>
    </div>
  );
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const counterRef = useRef(0);

  const addToast = useCallback((opts: { type?: ToastType; title: string; description?: string; duration?: number }) => {
    const id = String(++counterRef.current);
    setToasts(prev => [...prev, { id, type: opts.type || "info", title: opts.title, description: opts.description, duration: opts.duration }]);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const ctx: ToastContextType = {
    toast: addToast,
    success: (title, description) => addToast({ type: "success", title, description }),
    error: (title, description) => addToast({ type: "error", title, description }),
    warning: (title, description) => addToast({ type: "warning", title, description }),
    info: (title, description) => addToast({ type: "info", title, description }),
  };

  return (
    <ToastContext.Provider value={ctx}>
      {children}
      {/* Toast container */}
      <div className="fixed bottom-4 right-4 z-[200] flex flex-col gap-2 items-end">
        {toasts.map(t => (
          <ToastItem key={t.id} toast={t} onDismiss={() => removeToast(t.id)} />
        ))}
      </div>
      <style jsx global>{`
        @keyframes toastSlideIn {
          from { opacity: 0; transform: translateX(100%); }
          to { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
